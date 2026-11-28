"""Verify a pinned Phase-5 WORK handoff; execute only on an explicitly named server.

Default operation performs stdlib-only integrity/provenance checks and prints the
planned argv. It imports no project, model, test or training modules. Installation,
downloads, SSH changes and paid compute are outside this entrypoint.

One nonblocking file lock covers the whole execution. A state left ``running``
after SIGKILL, power loss or another unhandled shutdown is never auto-resumed:
inspect the recorded process groups manually before resolving that state.
"""
from datetime import datetime,timezone
from importlib import metadata
from pathlib import Path,PurePosixPath
import argparse
import fcntl
import hashlib
import json
import os
import platform
import resource
import shutil
import signal
import socket
import subprocess
import sys
import time


RUN_ROOT="runs/phase5-replicated-prepared"
REPORT_OUTPUT="artifacts/phase5/replicated-report"
CONDITIONS=("original","random_global","random_relation_stratified","targeted_local","targeted_relation_matched_control")
CONTROL_SIGNALS=(signal.SIGINT,signal.SIGTERM,signal.SIGHUP)
RUNNING_STATE_MESSAGE="WORK execution is still marked running; inspect its recorded process groups manually and resolve the state before resuming. Automatic restart is forbidden."


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    os.replace(temporary,path)


def local_path(project,relative):
    if not isinstance(relative,str) or not relative or "\\" in relative:
        raise ValueError("Bundle paths must be nonempty relative POSIX paths")
    value=PurePosixPath(relative)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError(f"Bundle path leaves the project: {relative}")
    path=(project/relative).resolve()
    if not path.is_relative_to(project):raise ValueError(f"Bundle symlink leaves the project: {relative}")
    return path


def planned_commands(manifest,python=None):
    python=python or sys.executable
    if manifest.get("run_root")!=RUN_ROOT or manifest.get("report_output")!=REPORT_OUTPUT:
        raise ValueError("Handoff must use the isolated replicated run/report roots")
    base=[python,"-m","kgc.research.structure"]
    common=["--data","data/codex-s","--prepared","runs/next-phase-sparsity-prepared"]
    def structure(action,root=RUN_ROOT,extra=()):return base+[action]+common+["--output",root]+list(extra)
    report=structure("report",extra=("--report-output",REPORT_OUTPUT))
    return [
        {"name":"backend-preflight","argv":[python,"scripts/check_backend_environment.py","--data","data/codex-s","--jar","vendor/AnyBURL-23-1x.jar","--output",RUN_ROOT+"/backend-preflight.json"]},
        {"name":"full-tests","argv":[python,"-m","pytest","-q","-rs","--junitxml="+RUN_ROOT+"/full-tests.xml"]},
        {"name":"separate-smoke","argv":structure("smoke",RUN_ROOT+"/smoke",("--threads","1"))},
        {"name":"replicated-primary","argv":structure("run",extra=("--threads","1","--seeds","0","1","2","--rule-repetitions","2"))},
        {"name":"frozen-constants","argv":structure("frozen",extra=("--families","constants"))},
        {"name":"initial-report","argv":report},
        {"name":"fresh-cases","argv":structure("cases",extra=("--report-output",REPORT_OUTPUT))},
        {"name":"frozen-general-cases","argv":structure("frozen-cases",extra=("--family","general","--report-output",REPORT_OUTPUT))},
        {"name":"frozen-constant-cases","argv":structure("frozen-cases",extra=("--family","constants","--report-output",REPORT_OUTPUT))},
        {"name":"report-refresh","argv":list(report)}]


def verify_bundle(project,manifest_path):
    """Read files and installed distribution metadata; import no backend packages."""
    project=Path(project).resolve();manifest_path=Path(manifest_path)
    manifest=json.loads(manifest_path.read_text());errors=[]
    if not isinstance(manifest,dict):raise ValueError("Handoff manifest must be a JSON object")
    result={"manifest_sha256":digest(manifest_path),"verified_file_count":0,"version_checks":{},
        "actual_python_version":platform.python_version(),"models_imported":False,"execution_started":False}
    try:commands=planned_commands(manifest)
    except ValueError as error:commands=[];errors.append(str(error))
    if not isinstance(manifest.get("laptop_hostname"),str) or not manifest["laptop_hostname"].strip():
        errors.append("Manifest must identify the laptop hostname")
    files=manifest.get("files")
    if not isinstance(files,dict) or not files:errors.append("Manifest requires a nonempty files→SHA256 mapping")
    else:
        for relative,expected in files.items():
            try:
                path=local_path(project,relative)
                if not isinstance(expected,str) or len(expected)!=64 or any(x not in "0123456789abcdefABCDEF" for x in expected):
                    raise ValueError("Invalid SHA256")
                if digest(path)!=expected.lower():raise ValueError("SHA256 mismatch")
                result["verified_file_count"]+=1
            except (OSError,ValueError) as error:errors.append(f"{relative}: {error}")
    locked=manifest.get("lockedversions",manifest.get("locked_versions"))
    if "lockedversions" in manifest and "locked_versions" in manifest and manifest["lockedversions"]!=manifest["locked_versions"]:
        errors.append("Conflicting locked-version mappings")
    if not isinstance(locked,dict) or not locked:errors.append("Manifest requires locked distribution versions")
    else:
        for name,expected in locked.items():
            try:actual=metadata.version(name)
            except metadata.PackageNotFoundError:actual=None
            result["version_checks"][name]={"expected":expected,"actual":actual}
            if actual!=expected:errors.append(f"Distribution version mismatch: {name}, expected {expected}, found {actual}")
    expected_python=manifest.get("python_version")
    if expected_python:
        actual=platform.python_version();expected_parts=str(expected_python).split(".")
        if actual.split(".")[:len(expected_parts)]!=expected_parts:
            errors.append(f"Python version mismatch: expected {expected_python}, found {actual}")
    if manifest.get("pyclause_commit"):
        try:
            direct=json.loads(metadata.distribution("PyClause").read_text("direct_url.json") or "{}")
            commit=direct.get("vcs_info",{}).get("commit_id")
        except (metadata.PackageNotFoundError,ValueError,OSError):commit=None
        result["pyclause_commit"]={"expected":manifest["pyclause_commit"],"actual":commit}
        if commit!=manifest["pyclause_commit"]:errors.append("Installed PyClause direct_url.json does not certify the pinned VCS commit")
    try:
        run=local_path(project,manifest["run_root"])
        protocol=json.loads((run/"protocol.json").read_text())
        if protocol.get("neural_seeds")!=[0,1,2] or protocol.get("mining_realizations")!=[0,1] or protocol.get("query_limit_facts","missing") is not None or protocol.get("conditions")!=list(CONDITIONS):
            errors.append("Prepared protocol must declare all five graphs, three seeds, two miners and full queries")
        if (run/"resource-stop.json").exists():errors.append("Replicated root is resource-stopped; automatic restart forbidden")
        aliases=list(run.rglob("alias.json"))+list(run.rglob("checkpoint-reference.json"))
        if aliases:errors.append("Replicated root contains aliases or checkpoint references")
        owner_path=run/"work-execution.json"
        owner=json.loads(owner_path.read_text()) if owner_path.exists() else {}
        if owner.get("status")=="running":errors.append(RUNNING_STATE_MESSAGE)
        existing=list(run.glob("*/neural-*/embedding/*.pt"))+list(run.glob("*/rules-*/mining/training.json"))
        if existing:
            if owner.get("manifest_sha256")!=result["manifest_sha256"] or owner.get("hostname")!=socket.gethostname():
                errors.append("Existing trained artifacts lack matching server-handoff ownership; no old-control reuse allowed")
    except (KeyError,OSError,ValueError) as error:errors.append(f"Prepared cohort validation failed: {error}")
    result.update(status="verified" if not errors else "blocked",errors=errors,planned_commands=commands)
    return manifest,result


class Interrupted(KeyboardInterrupt):
    def __init__(self,signum):self.signum=signum;super().__init__(f"Handoff received signal {signum}")


def require_server(manifest,compute_host):
    actual=socket.gethostname()
    key=lambda value:value.strip().lower().split(".",1)[0]
    if key(actual)==key(manifest["laptop_hostname"]):raise ValueError("Research execution is forbidden on the recorded laptop")
    if not compute_host or compute_host!=actual:raise ValueError("--compute-host must explicitly match socket.gethostname()")
    return actual


def child_environment(project):
    env=dict(os.environ);root=project/RUN_ROOT
    env.update(OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",
        JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=1",CUDA_VISIBLE_DEVICES="",KGC_COOLING_SECONDS="0",KGC_MAX_CPU_C="0",
        KGC_DATA_S=str(project/"data/codex-s"),KGC_ANYBURL_JAR=str(project/"vendor/AnyBURL-23-1x.jar"),
        MPLCONFIGDIR=str(root/"cache/matplotlib"),PYSTOW_HOME=str(root/"cache/pystow"),PYKEEN_HOME=str(root/"cache/pykeen"))
    return env


def group_exists(pgid):
    try:os.killpg(pgid,0);return True
    except ProcessLookupError:return False
    except PermissionError:return True


def cleanup(child,first_signal=signal.SIGTERM):
    """Bounded process-group cleanup; never suspend a wall-clock miner."""
    if child is None:return True
    child.poll()  # Reap the direct child, but its descendants may still remain.
    if not group_exists(child.pid):return True
    sequence=[(first_signal,3.)]
    if first_signal!=signal.SIGTERM:sequence.append((signal.SIGTERM,3.))
    sequence.append((signal.SIGKILL,2.))
    for signum,seconds in sequence:
        try:os.killpg(child.pid,signum)
        except ProcessLookupError:pass
        except PermissionError:return False
        deadline=time.monotonic()+seconds
        while True:
            child.poll()
            if not group_exists(child.pid):return True
            if time.monotonic()>=deadline:break
            time.sleep(.05)
    return False


def run_stage(command,entry,project,env,log_path,save):
    child=None;start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    entry.update(status="running",log=str(log_path),started_utc=datetime.now(timezone.utc).isoformat());save()
    try:
        with log_path.open("w") as log:
            child=subprocess.Popen(command,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            entry.update(child_pid=child.pid,child_process_group=child.pid);save();last_save=start
            while child.poll() is None:
                try:child.wait(timeout=.25)
                except subprocess.TimeoutExpired:pass
                if time.monotonic()-last_save>=5.:
                    entry["wall_seconds"]=time.monotonic()-start;save();last_save=time.monotonic()
            entry["returncode"]=child.returncode
            if child.returncode!=0:raise RuntimeError(f"Stage {entry['name']} exited {child.returncode}; inspect {log_path}")
            entry["status"]="complete"
    except KeyboardInterrupt as error:
        entry.update(status="interrupted",error=str(error));raise
    except Exception as error:
        entry.update(status="failed",error=repr(error));raise
    finally:
        prior={s:signal.getsignal(s) for s in CONTROL_SIGNALS}
        for signum in prior:signal.signal(signum,signal.SIG_IGN)
        try:
            entry["cleanup_complete"]=cleanup(child,signal.SIGINT if entry.get("status")=="interrupted" else signal.SIGTERM)
            if not entry["cleanup_complete"]:entry.update(status="failed",error="Child cleanup incomplete; manual process inspection required")
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            entry.update(wall_seconds=time.monotonic()-start,finished_utc=datetime.now(timezone.utc).isoformat(),
                child_cpu_seconds=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime))
            if child is not None:entry["returncode"]=child.returncode
            save()
        finally:
            for signum,handler in prior.items():signal.signal(signum,handler)


def verify_final_report(project):
    path=project/REPORT_OUTPUT/"report-status.json"
    record=json.loads(path.read_text())
    primary={(c,f"neural-{s}") for c in CONDITIONS for s in (0,1,2)}|{(c,f"rules-{r}") for c in CONDITIONS for r in (0,1)}
    frozen={(c,f) for c in CONDITIONS for f in ("general","constants")}
    observed_primary={(r["condition"],r["component"]) for r in record.get("cells",[]) if r["status"]=="complete"}
    observed_frozen={(r["condition"],r["family"]) for r in record.get("frozen_family_cells",[]) if r["status"]=="complete"}
    if record.get("smoke") is not False or record.get("all_primary_cells_complete") is not True or record.get("all_declared_frozen_cells_complete") is not True:
        raise ValueError("Final report still marks primary or frozen cells incomplete")
    if observed_primary!=primary or observed_frozen!=frozen or len(record.get("cells",[]))!=25 or len(record.get("frozen_family_cells",[]))!=10:
        raise ValueError("Final report does not certify the expected 25 primary and 10 frozen cells")
    if record.get("neural_seeds")!=[0,1,2] or record.get("independent_miners_per_graph")!=2:
        raise ValueError("Final report replication differs from the handoff")
    if (project/record.get("root","")).resolve()!=(project/RUN_ROOT).resolve():raise ValueError("Final report belongs to another run root")
    return {"path":str(path),"sha256":digest(path),"primary_cells":25,"frozen_cells":10}


def execute_plan(project,manifest,verification,compute_host):
    hostname=require_server(manifest,compute_host)
    if verification["status"]!="verified":
        if RUNNING_STATE_MESSAGE in verification.get("errors",[]):raise ValueError(RUNNING_STATE_MESSAGE)
        raise ValueError("Bundle verification failed; execution refused")
    root=project/RUN_ROOT;root.mkdir(parents=True,exist_ok=True)
    # Keep this inode: unlinking a lock file can permit another launcher to lock
    # a different inode at the same path while the first process still runs.
    with (root/"work-execution.lock").open("a+") as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError("Another WORK launcher holds the execution lock; no concurrent launch permitted") from None
        try:
            path=root/"work-execution.json"
            if path.exists() and json.loads(path.read_text()).get("status")=="running":
                raise ValueError(RUNNING_STATE_MESSAGE)
            return execute_locked(project,manifest,verification,compute_host,hostname)
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


def execute_locked(project,manifest,verification,compute_host,hostname):
    root=project/RUN_ROOT;path=root/"work-execution.json";attempt=str(time.time_ns())
    if path.exists():shutil.copy2(path,root/f"work-execution.attempt-{attempt}.json")
    logs=root/"work-logs"/attempt;logs.mkdir(parents=True,exist_ok=True)
    env=child_environment(project)
    record={"status":"running","hostname":hostname,"compute_host":compute_host,"laptop_hostname":manifest["laptop_hostname"],
        "launcher_pid":os.getpid(),"launcher_process_group":os.getpgrp(),
        "hard_kill_policy":RUNNING_STATE_MESSAGE+" SIGKILL/power loss cannot guarantee cleanup or update execution metadata.",
        "manifest_sha256":verification["manifest_sha256"],"run_root":RUN_ROOT,"report_output":REPORT_OUTPUT,
        "actual_python_version":platform.python_version(),"python_executable":sys.executable,
        "started_utc":datetime.now(timezone.utc).isoformat(),"stages":[],"plan":verification["planned_commands"],
        "resource_policy":"Serial one-thread CPU work; Java ActiveProcessorCount=1; no duty-cycle, SIGSTOP or mining-budget suspension",
        "old_controls_reused":False,"compute_provider":"Hugging Face Jobs",
        "paid_compute":True,"paid_gpu_access":False,"installation_or_download_performed":False}
    save=lambda:atomic_json(path,record)
    previous={s:signal.getsignal(s) for s in CONTROL_SIGNALS}
    def interrupted(signum,frame):raise Interrupted(signum)
    for signum in previous:signal.signal(signum,interrupted)
    try:
        save()
        for i,item in enumerate(verification["planned_commands"]):
            entry={"name":item["name"],"argv":item["argv"]};record["stages"].append(entry)
            run_stage(item["argv"],entry,project,env,logs/f"{i:02d}-{item['name']}.log",save)
            if entry["status"]!="complete":raise RuntimeError(f"Stage {item['name']} is incomplete")
        record["final_report_check"]=verify_final_report(project)
        record["status"]="complete"
    except KeyboardInterrupt as error:
        record.update(status="interrupted",interrupt_signal=getattr(error,"signum",signal.SIGINT),error=str(error))
    except Exception as error:record.update(status="failed",error=repr(error))
    finally:
        record["finished_utc"]=datetime.now(timezone.utc).isoformat()
        try:save()
        finally:
            for signum,handler in previous.items():signal.signal(signum,handler)
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest",type=Path,default=Path("artifacts/phase5/work-handoff.json"))
    parser.add_argument("--execute",action="store_true");parser.add_argument("--compute-host")
    args=parser.parse_args(argv);project=args.project.resolve()
    manifest_path=args.manifest if args.manifest.is_absolute() else project/args.manifest
    try:
        manifest,verification=verify_bundle(project,manifest_path)
        if not args.execute:
            print(json.dumps({"mode":"verify-only","hostname":socket.gethostname(),**verification},indent=2))
            return 0 if verification["status"]=="verified" else 2
        record=execute_plan(project,manifest,verification,args.compute_host)
        print(json.dumps({"mode":"execute","status":record["status"],"state":str(project/RUN_ROOT/"work-execution.json"),"error":record.get("error")},indent=2))
        return 0 if record["status"]=="complete" else 128+record.get("interrupt_signal",2) if record["status"]=="interrupted" else 1
    except (OSError,ValueError,KeyError) as error:
        print(json.dumps({"status":"blocked","error":str(error),"execution_started":False},indent=2));return 2


if __name__=="__main__":raise SystemExit(main())
