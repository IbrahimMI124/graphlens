"""Duty-cycle ONLY the fixed inference worker; never training or Java mining.

Linux process-group stops cover native metadata loading as well as prediction.
This is a supervised run/pause schedule, not a kernel cgroup CPU quota. CPU
affinity limits the child to one allowed processor. Wall-window and child CPU
counters are reported separately. Inference equivalence must be checked against
unpaced outputs before using this resource policy for research results.
"""
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import subprocess
import sys
import time

from .resources import cpu_temperatures


CONDITIONS=("original","random_global","random_relation_stratified","targeted_local","targeted_relation_matched_control")
FAMILIES=("all","general","constants")


@dataclass(frozen=True)
class Limits:
    active_ms:float=50.
    pause_ms:float=450.
    max_wall_seconds:float=1800.
    max_cpu_c:float=70.
    resume_cpu_c:float=55.
    max_thermal_wait:float=180.
    cleanup_seconds:float=3.
    cpu:int|None=None

    def validate(self):
        values=(self.active_ms,self.pause_ms,self.max_wall_seconds,self.max_cpu_c,self.resume_cpu_c,self.max_thermal_wait,self.cleanup_seconds)
        if not all(math.isfinite(x) for x in values):raise ValueError("Resource limits must be finite")
        if not 0<self.active_ms<=250 or self.pause_ms<self.active_ms:
            raise ValueError("Active windows must be 0–250ms and pauses at least as long as active windows")
        if min(self.max_wall_seconds,self.max_thermal_wait,self.cleanup_seconds)<=0:
            raise ValueError("Wall, thermal-wait and cleanup limits must be positive")
        if not 0<self.resume_cpu_c<self.max_cpu_c<110:raise ValueError("Invalid thermal thresholds")
        allowed=os.sched_getaffinity(0)
        chosen=min(allowed) if self.cpu is None else self.cpu
        if chosen not in allowed:raise ValueError("Requested CPU is outside the allowed affinity")
        return chosen


class _Interrupted(KeyboardInterrupt):
    def __init__(self,signum):
        self.signum=signum
        super().__init__(f"Supervisor received signal {signum}")


class _ResourceStop(RuntimeError):
    def __init__(self,reason,message):
        self.reason=reason
        super().__init__(message)


def _atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    os.replace(temporary,path)


def _proc_state(pid):
    try:
        text=Path(f"/proc/{pid}/stat").read_text()
        return text[text.rfind(")")+2:].split()[0]
    except FileNotFoundError:return None


def _group_signal(child,signum):
    if child.poll() is not None:return False
    try:os.killpg(child.pid,signum)
    except ProcessLookupError:return False
    return True


def _stop(child):
    if not _group_signal(child,signal.SIGSTOP):return False
    deadline=time.monotonic()+.25
    while child.poll() is None:
        if _proc_state(child.pid) in ("T","t"):return True
        if time.monotonic()>=deadline:
            raise _ResourceStop("stop_not_observed","Child did not enter a stopped state within 250ms")
        time.sleep(.001)
    return False


def _cleanup(child,seconds):
    """Resume before termination so even a stopped child can handle SIGTERM."""
    if child is None:return True,None
    if child.poll() is not None:return True,None
    _group_signal(child,signal.SIGCONT)
    _group_signal(child,signal.SIGTERM)
    try:child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        _group_signal(child,signal.SIGKILL)
        try:child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:return False,"Child remains uninterruptible with SIGKILL pending"
    return True,None


def _supervise(command,state_path,limits=None,temperature_reader=cpu_temperatures,env=None):
    """Internal testable supervisor. The CLI exposes no arbitrary command path.

    Call from the main thread. The only production caller supplies the fixed
    structure_inference argv below. Tests may supply harmless bounded children.
    """
    limits=limits or Limits();cpu=limits.validate();state_path=Path(state_path)
    if state_path.exists():
        archive=state_path.with_name(state_path.stem+f".attempt-{time.time_ns()}"+state_path.suffix)
        shutil.copy2(state_path,archive)
    start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    child=None;phase="not_started";phase_start=start
    accounting={"permitted_active_wall_seconds":0.,"observed_stopped_wall_seconds":0.}
    record={"status":"running","started_utc":datetime.now(timezone.utc).isoformat(),
        "supervisor_version":1,"supervisor_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worker_thread_environment":{"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1"},
        "command":list(command),"selected_cpu":cpu,"configured_active_ms":limits.active_ms,
        "configured_pause_ms":limits.pause_ms,"configured_duty_fraction":limits.active_ms/(limits.active_ms+limits.pause_ms),
        "max_wall_seconds":limits.max_wall_seconds,"max_cpu_c":limits.max_cpu_c,"resume_cpu_c":limits.resume_cpu_c,
        "max_single_thermal_wait_seconds":limits.max_thermal_wait,"observed_stop_count":0,
        "thermal_wait_seconds":0.,"temperature_readings":0,"max_observed_cpu_c":None,
        "last_observed_cpu_c":None,"thermal_sensor_available":False,"cleanup_complete":None,
        "parent_death_signal":"SIGKILL (Linux PR_SET_PDEATHSIG)",
        "scope":"inference/loading only; no training, Java mining or arbitrary CLI command",
        "duty_accounting":"Observed stopped wall windows versus permitted active windows; active permission is not CPU usage. This is not a kernel CPU quota."}
    def transition(new_phase):
        nonlocal phase,phase_start
        now=time.monotonic()
        key={"active":"permitted_active_wall_seconds","stopped":"observed_stopped_wall_seconds"}.get(phase)
        if key:accounting[key]+=now-phase_start
        phase=new_phase;phase_start=now
    def wall_check():
        if time.monotonic()-start>=limits.max_wall_seconds:
            raise _ResourceStop("wall_limit","Inference supervisor reached its wall-time limit")
    def temperature():
        values=list(temperature_reader())
        valid=[float(x) for x in values if math.isfinite(float(x)) and 0<float(x)<120]
        if not valid:return None
        value=max(valid);record["thermal_sensor_available"]=True
        record["temperature_readings"]+=1;record["last_observed_cpu_c"]=value
        record["max_observed_cpu_c"]=max(value,record["max_observed_cpu_c"] or value)
        return value
    def thermal_gate():
        value=temperature()
        if value is None or value<limits.max_cpu_c:return
        began=time.monotonic()
        try:
            while value is not None and value>limits.resume_cpu_c:
                wall_check()
                if time.monotonic()-began>=limits.max_thermal_wait:
                    raise _ResourceStop("thermal_wait_limit","CPU did not cool within the configured thermal-wait limit")
                _atomic_json(state_path,{**record,**accounting,"phase":phase,"wall_seconds":time.monotonic()-start})
                time.sleep(min(.2,limits.max_thermal_wait/4,limits.max_wall_seconds/4))
                value=temperature()
        finally:record["thermal_wait_seconds"]+=time.monotonic()-began
    def wait_window(seconds):
        deadline=time.monotonic()+seconds
        while child.poll() is None and time.monotonic()<deadline:
            wall_check();time.sleep(min(.01,max(0.,deadline-time.monotonic())))
    def interrupted(signum,frame):raise _Interrupted(signum)
    previous={signum:signal.getsignal(signum) for signum in (signal.SIGINT,signal.SIGTERM)}
    for signum in previous:signal.signal(signum,interrupted)
    last_save=0.
    try:
        _atomic_json(state_path,record);thermal_gate();wall_check()
        # Pre-exec contains only affinity, prctl and a parent-death race check.
        # The production supervisor has no worker threads or backend imports.
        libc=ctypes.CDLL(None,use_errno=True);parent_pid=os.getpid()
        def child_setup():
            os.sched_setaffinity(0,{cpu})
            if libc.prctl(1,signal.SIGKILL,0,0,0)!=0:raise OSError(ctypes.get_errno(),"PR_SET_PDEATHSIG failed")
            if os.getppid()!=parent_pid:os.kill(os.getpid(),signal.SIGKILL)
        child_env=dict(os.environ if env is None else env)
        child_env.update(OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
        child=subprocess.Popen(list(command),start_new_session=True,preexec_fn=child_setup,env=child_env)
        record.update(child_pid=child.pid,child_process_group=child.pid)
        if _stop(child):
            transition("stopped");record["observed_stop_count"]+=1
        while child.poll() is None:
            wall_check();thermal_gate()
            if child.poll() is not None:break
            _group_signal(child,signal.SIGCONT);transition("active")
            wait_window(limits.active_ms/1000)
            if child.poll() is not None:break
            if _stop(child):
                transition("stopped");record["observed_stop_count"]+=1
            if child.poll() is not None:break
            wait_window(limits.pause_ms/1000)
            if time.monotonic()-last_save>=1.:
                _atomic_json(state_path,{**record,**accounting,"phase":phase,"wall_seconds":time.monotonic()-start})
                last_save=time.monotonic()
        transition("finished")
        record.update(status="complete" if child.returncode==0 else "failed",reason="worker_exit",returncode=child.returncode)
    except (KeyboardInterrupt,_Interrupted) as error:
        record.update(status="interrupted",reason="supervisor_signal",interrupt_signal=getattr(error,"signum",signal.SIGINT),error=str(error))
    except _ResourceStop as error:
        record.update(status="failed",reason=error.reason,error=str(error))
    except Exception as error:
        record.update(status="failed",reason="supervisor_error",error=repr(error))
    finally:
        # Ignore additional termination requests only during bounded cleanup.
        for signum in previous:signal.signal(signum,signal.SIG_IGN)
        try:
            cleanup_complete,cleanup_error=_cleanup(child,limits.cleanup_seconds)
            transition("finished")
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            record.update(accounting)
            record.update(wall_seconds=time.monotonic()-start,finished_utc=datetime.now(timezone.utc).isoformat(),
                cleanup_complete=cleanup_complete,cleanup_error=cleanup_error,
                returncode=child.returncode if child is not None else None,
                child_user_cpu_seconds=after.ru_utime-before.ru_utime,child_system_cpu_seconds=after.ru_stime-before.ru_stime)
            record["child_cpu_seconds"]=record["child_user_cpu_seconds"]+record["child_system_cpu_seconds"]
            record["cpu_fraction_of_one_core"]=record["child_cpu_seconds"]/record["wall_seconds"]
            windows=accounting["permitted_active_wall_seconds"]+accounting["observed_stopped_wall_seconds"]
            record["observed_permitted_active_fraction"]=accounting["permitted_active_wall_seconds"]/windows if windows else None
            if not cleanup_complete:record.update(status="failed",reason="cleanup_incomplete")
            _atomic_json(state_path,record)
        finally:
            for signum,handler in previous.items():signal.signal(signum,handler)
    return record


def worker_command(root,kind,conditions,families,limit_facts=None,report_output=None):
    """Production argv is fixed and contains no shell or user-selected executable."""
    if kind not in ("fresh","frozen","frozen-cases"):raise ValueError("Invalid inference kind")
    if not conditions or len(set(conditions))!=len(conditions) or not set(conditions)<=set(CONDITIONS):raise ValueError("Invalid graph conditions")
    if not families or len(set(families))!=len(families) or not set(families)<=set(FAMILIES):raise ValueError("Invalid rule families")
    if limit_facts is not None and limit_facts<1:raise ValueError("Positive fact limit required")
    if kind=="frozen-cases":
        if limit_facts is not None:raise ValueError("Frozen case collection cannot use a fact limit")
        if "all" in families:raise ValueError("Frozen case collection supports only general/constant families")
    elif report_output is not None:raise ValueError("Report output is supported only for frozen-cases")
    argv=[sys.executable,"-m","kgc.research.structure_inference","--root",str(root),"--kind",kind,
        "--conditions",*conditions,"--families",*families]
    if limit_facts is not None:argv += ["--limit-facts",str(limit_facts)]
    if report_output is not None:argv += ["--report-output",str(report_output)]
    return argv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True);parser.add_argument("--kind",required=True,choices=("fresh","frozen","frozen-cases"))
    parser.add_argument("--conditions",required=True,nargs="+",choices=CONDITIONS)
    parser.add_argument("--families",required=True,nargs="+",choices=FAMILIES)
    parser.add_argument("--state",required=True);parser.add_argument("--limit-facts",type=int);parser.add_argument("--report-output")
    parser.add_argument("--active-ms",type=float,default=50.);parser.add_argument("--pause-ms",type=float,default=450.)
    parser.add_argument("--max-wall-seconds",type=float,default=1800.)
    parser.add_argument("--max-cpu-c",type=float,default=70.);parser.add_argument("--resume-cpu-c",type=float,default=55.)
    parser.add_argument("--max-thermal-wait",type=float,default=180.);parser.add_argument("--cpu",type=int)
    args=parser.parse_args()
    try:
        command=worker_command(args.root,args.kind,args.conditions,args.families,args.limit_facts,args.report_output)
        limits=Limits(args.active_ms,args.pause_ms,args.max_wall_seconds,args.max_cpu_c,args.resume_cpu_c,args.max_thermal_wait,cpu=args.cpu)
        limits.validate()
    except ValueError as error:parser.error(str(error))
    result=_supervise(command,args.state,limits)
    print(json.dumps({k:result.get(k) for k in ("status","reason","returncode","child_cpu_seconds","wall_seconds","max_observed_cpu_c","cleanup_complete")}))
    return 0 if result["status"]=="complete" else 128+result.get("interrupt_signal",2) if result["status"]=="interrupted" else 1


if __name__=="__main__":
    raise SystemExit(main())
