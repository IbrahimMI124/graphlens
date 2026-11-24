"""Server handoff guards and mocked argv; no backends, tests or training launched."""
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import io
import fcntl
import json
import platform
import signal
import sys
import tempfile
import unittest

from scripts import run_phase5_work as handoff


class WorkHandoffTests(unittest.TestCase):
    def fixture(self,root):
        project=Path(root);run=project/handoff.RUN_ROOT;run.mkdir(parents=True)
        protocol={"conditions":list(handoff.CONDITIONS),"neural_seeds":[0,1,2],"mining_realizations":[0,1],"query_limit_facts":None}
        (run/"protocol.json").write_text(json.dumps(protocol));(project/"bundle.txt").write_text("synthetic integrity fixture\n")
        manifest={"laptop_hostname":"laptop","run_root":handoff.RUN_ROOT,"report_output":handoff.REPORT_OUTPUT,
            "lockedversions":{"unit-test-distribution":"1.0"},"python_version":".".join(platform.python_version().split(".")[:2]),
            "files":{p:handoff.digest(project/p) for p in ("bundle.txt",handoff.RUN_ROOT+"/protocol.json")}}
        path=project/"handoff.json";path.write_text(json.dumps(manifest))
        return project,path,manifest

    def main(self,project,path,*args):
        output=io.StringIO()
        with redirect_stdout(output):code=handoff.main(["--project",str(project),"--manifest",str(path),*args])
        return code,json.loads(output.getvalue())

    def final_report(self,project,complete=True):
        cells=[{"condition":c,"component":f"neural-{s}","status":"complete"} for c in handoff.CONDITIONS for s in (0,1,2)]
        cells += [{"condition":c,"component":f"rules-{r}","status":"complete"} for c in handoff.CONDITIONS for r in (0,1)]
        frozen=[{"condition":c,"family":f,"status":"complete"} for c in handoff.CONDITIONS for f in ("general","constants")]
        result={"smoke":False,"all_primary_cells_complete":True,"all_declared_frozen_cells_complete":complete,
            "cells":cells,"frozen_family_cells":frozen,"neural_seeds":[0,1,2],"independent_miners_per_graph":2,"root":handoff.RUN_ROOT}
        path=project/handoff.REPORT_OUTPUT/"report-status.json";path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result))

    def test_verify_only_prints_plan_without_any_subprocess_or_execution_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp)
            with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="laptop"),patch.object(handoff.subprocess,"Popen") as child:
                code,result=self.main(project,path)
            self.assertEqual(code,0);self.assertEqual(result["mode"],"verify-only")
            self.assertFalse(result["execution_started"]);self.assertFalse(result["models_imported"])
            self.assertEqual(len(result["planned_commands"]),10);child.assert_not_called()
            self.assertFalse((project/handoff.RUN_ROOT/"work-execution.json").exists())

    def test_execute_refuses_laptop_and_explicit_host_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp)
            for actual,requested,expected in (("laptop","laptop","forbidden"),("work-server","different","explicitly match")):
                with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value=actual),patch.object(handoff.subprocess,"Popen") as child:
                    code,result=self.main(project,path,"--execute","--compute-host",requested)
                self.assertEqual(code,2);self.assertIn(expected,result["error"]);child.assert_not_called()

    def test_checksum_and_distribution_mismatch_block_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp);(project/"bundle.txt").write_text("tampered")
            with patch.object(handoff.metadata,"version",return_value="wrong"),patch.object(handoff.socket,"gethostname",return_value="work-server"),patch.object(handoff.subprocess,"Popen") as child:
                _,verification=handoff.verify_bundle(project,path)
                code,result=self.main(project,path,"--execute","--compute-host","work-server")
            self.assertEqual(code,2);self.assertIn("verification failed",result["error"])
            self.assertTrue(any("SHA256 mismatch" in x for x in verification["errors"]))
            self.assertTrue(any("version mismatch" in x for x in verification["errors"]));child.assert_not_called()

    def test_exact_serial_plan_keeps_training_and_reports_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,manifest=self.fixture(tmp);plan=handoff.planned_commands(manifest)
            self.assertEqual([p["name"] for p in plan],["backend-preflight","full-tests","separate-smoke","replicated-primary","frozen-constants","initial-report","fresh-cases","frozen-general-cases","frozen-constant-cases","report-refresh"])
            self.assertTrue(all(p["argv"][0]==sys.executable for p in plan))
            self.assertIn(handoff.RUN_ROOT+"/smoke",plan[2]["argv"])
            self.assertEqual(plan[3]["argv"][-6:],["--seeds","0","1","2","--rule-repetitions","2"])
            self.assertEqual(plan[5]["argv"],plan[-1]["argv"])
            self.assertIn(handoff.REPORT_OUTPUT,plan[6]["argv"])
            self.assertTrue(all("inference_limiter" not in " ".join(p["argv"]) for p in plan))
            self.assertTrue(all("ssh" not in p["argv"] and "pip" not in p["argv"] for p in plan))
            with self.assertRaisesRegex(ValueError,"isolated"):
                handoff.planned_commands({**manifest,"run_root":"runs/phase5-90"})

    def test_pyclause_commit_checked_using_distribution_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,manifest=self.fixture(tmp);manifest["pyclause_commit"]="a"*40;path.write_text(json.dumps(manifest))
            installed=SimpleNamespace(read_text=lambda name:json.dumps({"vcs_info":{"commit_id":"b"*40}}))
            with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.metadata,"distribution",return_value=installed):
                _,result=handoff.verify_bundle(project,path)
            self.assertEqual(result["status"],"blocked")
            self.assertTrue(any("pinned VCS commit" in e for e in result["errors"]))

    def test_unowned_old_control_checkpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp);old=project/handoff.RUN_ROOT/"original/neural-0/embedding/best.pt"
            old.parent.mkdir(parents=True);old.write_bytes(b"synthetic old control")
            with patch.object(handoff.metadata,"version",return_value="1.0"):
                _,result=handoff.verify_bundle(project,path)
            self.assertTrue(any("no old-control reuse" in e for e in result["errors"]))

    def test_mocked_execution_requires_complete_final_primary_and_frozen_report(self):
        class Done:
            pid=999999999;returncode=0
            def poll(self):return 0
            def wait(self,timeout=None):return 0
        for complete in (True,False):
            with self.subTest(complete=complete),tempfile.TemporaryDirectory() as tmp:
                project,path,_=self.fixture(tmp);self.final_report(project,complete)
                calls=[]
                def child(argv,**kwargs):
                    calls.append((argv,kwargs))
                    with (project/handoff.RUN_ROOT/"work-execution.lock").open("a+") as second:
                        with self.assertRaises(BlockingIOError):
                            fcntl.flock(second.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                    return Done()
                with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="work-server"),patch.object(handoff.subprocess,"Popen",side_effect=child):
                    code,_=self.main(project,path,"--execute","--compute-host","work-server")
                record=json.loads((project/handoff.RUN_ROOT/"work-execution.json").read_text())
                self.assertEqual(len(calls),10)
                self.assertTrue(all(row[1]["start_new_session"] for row in calls))
                self.assertTrue(all(row[1]["env"]["JAVA_TOOL_OPTIONS"]=="-XX:ActiveProcessorCount=1" for row in calls))
                self.assertTrue(all(row[1]["env"]["OMP_NUM_THREADS"]=="1" for row in calls))
                self.assertEqual(record["status"],"complete" if complete else "failed")
                self.assertEqual(code,0 if complete else 1)
                self.assertFalse(record["old_controls_reused"])
                if complete:self.assertEqual(record["final_report_check"]["primary_cells"],25)
                else:self.assertIn("incomplete",record["error"])

    def test_stage_failure_or_interrupt_stops_following_commands(self):
        class Failed:
            pid=999999999;returncode=9
            def poll(self):return 9
            def wait(self,timeout=None):return 9
        for interrupted in (False,True):
            with self.subTest(interrupted=interrupted),tempfile.TemporaryDirectory() as tmp:
                project,path,_=self.fixture(tmp)
                effect=handoff.Interrupted(15) if interrupted else None
                with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="work-server"),patch.object(handoff.subprocess,"Popen",side_effect=effect,return_value=Failed()) as child:
                    code,_=self.main(project,path,"--execute","--compute-host","work-server")
                record=json.loads((project/handoff.RUN_ROOT/"work-execution.json").read_text())
                self.assertEqual(child.call_count,1)
                self.assertEqual(len(record["stages"]),1)
                self.assertEqual(record["status"],"interrupted" if interrupted else "failed")
                self.assertEqual(code,143 if interrupted else 1)

    def test_nonblocking_lock_refuses_concurrent_launcher_without_writing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp);root=project/handoff.RUN_ROOT
            with (root/"work-execution.lock").open("a+") as existing:
                fcntl.flock(existing.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="work-server"),patch.object(handoff.subprocess,"Popen") as child:
                    code,result=self.main(project,path,"--execute","--compute-host","work-server")
                self.assertEqual(code,2);self.assertIn("execution lock",result["error"])
                child.assert_not_called();self.assertFalse((root/"work-execution.json").exists())

    def test_running_state_refused_even_without_checkpoints_and_checked_again_under_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,manifest=self.fixture(tmp);root=project/handoff.RUN_ROOT
            with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="work-server"):
                _,verified=handoff.verify_bundle(project,path)
                owner={"status":"running","manifest_sha256":verified["manifest_sha256"],"hostname":"work-server"}
                (root/"work-execution.json").write_text(json.dumps(owner))
                _,blocked=handoff.verify_bundle(project,path)
                self.assertIn(handoff.RUNNING_STATE_MESSAGE,blocked["errors"])
                with patch.object(handoff.subprocess,"Popen") as child:
                    code,result=self.main(project,path,"--execute","--compute-host","work-server")
                    self.assertEqual(code,2);self.assertIn("manually",result["error"]);child.assert_not_called()
                with patch.object(handoff,"execute_locked") as execute:
                    with self.assertRaisesRegex(ValueError,"marked running"):
                        handoff.execute_plan(project,manifest,verified,"work-server")
                    execute.assert_not_called()
            self.assertEqual(json.loads((root/"work-execution.json").read_text()),owner)

    def test_sighup_records_interruption_restores_handler_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            project,path,_=self.fixture(tmp);old=signal.getsignal(signal.SIGHUP)
            def hangup(*args,**kwargs):signal.raise_signal(signal.SIGHUP)
            with patch.object(handoff.metadata,"version",return_value="1.0"),patch.object(handoff.socket,"gethostname",return_value="work-server"),patch.object(handoff.subprocess,"Popen",side_effect=hangup) as child:
                code,_=self.main(project,path,"--execute","--compute-host","work-server")
            record=json.loads((project/handoff.RUN_ROOT/"work-execution.json").read_text())
            self.assertEqual(code,129);self.assertEqual(record["status"],"interrupted")
            self.assertEqual(record["interrupt_signal"],signal.SIGHUP);self.assertEqual(child.call_count,1)
            self.assertEqual(signal.getsignal(signal.SIGHUP),old)
            self.assertIn("SIGKILL/power loss",record["hard_kill_policy"])
            with (project/handoff.RUN_ROOT/"work-execution.lock").open("a+") as unlocked:
                fcntl.flock(unlocked.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)

    def test_cleanup_kills_residual_group_after_direct_child_exits(self):
        child=SimpleNamespace(pid=999999999,poll=lambda:0)
        # The already-exited direct child must not hide a lingering Java member.
        with patch.object(handoff,"group_exists",side_effect=[True,True,False]),patch.object(handoff.os,"killpg") as send,patch.object(handoff.time,"monotonic",side_effect=[0.,4.,8.]):
            self.assertTrue(handoff.cleanup(child))
        self.assertEqual([call.args for call in send.call_args_list],[(child.pid,signal.SIGTERM),(child.pid,signal.SIGKILL)])
