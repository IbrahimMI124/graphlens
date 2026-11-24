"""Only tiny harmless children; never models, Java or research inference."""
from pathlib import Path
import json
import os
import signal
import sys
import tempfile
import unittest

from kgc.research.inference_limiter import Limits,_supervise,worker_command


@unittest.skipUnless(sys.platform.startswith("linux"),"Linux process groups/prctl required")
class InferenceLimiterTests(unittest.TestCase):
    def test_fixed_worker_command_cannot_select_training_or_executable(self):
        command=worker_command("a path/root","fresh",["original"],["general"],4)
        self.assertEqual(command[:3],[sys.executable,"-m","kgc.research.structure_inference"])
        self.assertEqual(command[-2:],["--limit-facts","4"])
        self.assertNotIn("kgc.research.structure",command)
        with self.assertRaises(ValueError):worker_command("x","run",["original"],["all"])
        with self.assertRaises(ValueError):worker_command("x","fresh",["not-a-condition"],["all"])
        with self.assertRaises(ValueError):worker_command("x","fresh",["original"],["not-a-family"])
        with self.assertRaises(ValueError):worker_command("x","fresh",["original"],["all"],0)
        with self.assertRaises(ValueError):Limits(active_ms=500).validate()
        with self.assertRaises(ValueError):Limits(active_ms=50,pause_ms=0).validate()

    def test_real_stop_continue_completion_and_atomic_metadata(self):
        # About15ms of CPU plus interpreter startup, bounded to one core.
        command=[sys.executable,"-c","import time; end=time.process_time()+.015\nwhile time.process_time()<end: pass"]
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/"state.json"
            result=_supervise(command,state,Limits(active_ms=5,pause_ms=20,max_wall_seconds=3),temperature_reader=lambda:[])
            self.assertEqual(result["status"],"complete")
            self.assertEqual(result["returncode"],0)
            self.assertTrue(result["cleanup_complete"])
            self.assertGreater(result["observed_stop_count"],0)
            self.assertGreater(result["observed_stopped_wall_seconds"],0)
            self.assertGreater(result["child_cpu_seconds"],0)
            self.assertLess(result["child_cpu_seconds"],.25)
            self.assertIn(result["selected_cpu"],os.sched_getaffinity(0))
            self.assertFalse(result["thermal_sensor_available"])
            self.assertFalse(Path(f"/proc/{result['child_pid']}").exists())
            self.assertEqual(json.loads(state.read_text())["status"],"complete")
            self.assertFalse(list(Path(tmp).glob("*.tmp-*")))

    def test_frozen_case_scope_has_fixed_worker_and_no_prefix_or_all_family(self):
        command=worker_command("a root","frozen-cases",["targeted_local"],["general","constants"],report_output="a report")
        self.assertEqual(command[:3],[sys.executable,"-m","kgc.research.structure_inference"])
        self.assertEqual(command[-2:],["--report-output","a report"])
        self.assertNotIn("--limit-facts",command)
        with self.assertRaisesRegex(ValueError,"fact limit"):
            worker_command("x","frozen-cases",["original"],["general"],1)
        with self.assertRaisesRegex(ValueError,"general/constant"):
            worker_command("x","frozen-cases",["original"],["all"])
        for kind in ("fresh","frozen"):
            with self.assertRaisesRegex(ValueError,"only for frozen-cases"):
                worker_command("x",kind,["original"],["general"],report_output="x")

    def test_wall_timeout_resumes_and_reaps_stopped_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=_supervise([sys.executable,"-c","import time; time.sleep(10)"],Path(tmp)/"state.json",
                Limits(active_ms=5,pause_ms=20,max_wall_seconds=.15,cleanup_seconds=.2),temperature_reader=lambda:[])
            self.assertEqual(result["status"],"failed")
            self.assertEqual(result["reason"],"wall_limit")
            self.assertTrue(result["cleanup_complete"])
            self.assertIsNotNone(result["returncode"])
            self.assertFalse(Path(f"/proc/{result['child_pid']}").exists())
            self.assertLess(result["wall_seconds"],1.5)

    def test_sigterm_cleanup_and_handler_restoration(self):
        reads=0
        def temperatures():
            nonlocal reads
            reads+=1
            if reads==3:os.kill(os.getpid(),signal.SIGTERM)
            return []
        old=signal.getsignal(signal.SIGTERM)
        with tempfile.TemporaryDirectory() as tmp:
            result=_supervise([sys.executable,"-c","import time; time.sleep(10)"],Path(tmp)/"state.json",
                Limits(active_ms=5,pause_ms=20,max_wall_seconds=2,cleanup_seconds=.2),temperature_reader=temperatures)
            self.assertEqual(result["status"],"interrupted")
            self.assertEqual(result["interrupt_signal"],signal.SIGTERM)
            self.assertTrue(result["cleanup_complete"])
            self.assertFalse(Path(f"/proc/{result['child_pid']}").exists())
        self.assertEqual(signal.getsignal(signal.SIGTERM),old)

    def test_thermal_timeout_starts_no_worker_and_preserves_prior_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/"state.json";state.write_text('{"status":"old-attempt"}')
            result=_supervise([sys.executable,"-c","raise RuntimeError('must not start')"],state,
                Limits(active_ms=5,pause_ms=20,max_wall_seconds=1,max_thermal_wait=.04),temperature_reader=lambda:[80.])
            self.assertEqual(result["status"],"failed")
            self.assertEqual(result["reason"],"thermal_wait_limit")
            self.assertNotIn("child_pid",result)
            self.assertTrue(result["cleanup_complete"])
            self.assertGreater(result["thermal_wait_seconds"],0)
            self.assertEqual(result["max_observed_cpu_c"],80.)
            archives=list(Path(tmp).glob("state.attempt-*.json"))
            self.assertEqual(len(archives),1)
            self.assertEqual(json.loads(archives[0].read_text())["status"],"old-attempt")

    def test_nonzero_worker_exit_is_never_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=_supervise([sys.executable,"-c","raise SystemExit(7)"],Path(tmp)/"state.json",
                Limits(active_ms=5,pause_ms=20,max_wall_seconds=2),temperature_reader=lambda:[])
            self.assertEqual(result["status"],"failed")
            self.assertEqual(result["returncode"],7)
            self.assertTrue(result["cleanup_complete"])
