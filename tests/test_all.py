"""Valid, invalid and boundary test cases for every module."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from osim import bashbridge, deadlock, disk, memory, scheduler, validation  # noqa: E402
from osim.scheduler import Process  # noqa: E402
from osim.validation import ValidationError  # noqa: E402

CLASSIC = [Process("P1", 0, 5), Process("P2", 1, 3), Process("P3", 2, 8), Process("P4", 3, 6)]
BANKER = dict(available=[3, 3, 2],
              allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
              maximum=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]])
REFS = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]


class TestScheduler(unittest.TestCase):
    def test_fcfs_known_values(self):
        r = scheduler.fcfs(CLASSIC)
        self.assertEqual([x["completion"] for x in r["rows"]], [5, 8, 16, 22])
        self.assertAlmostEqual(r["avg_waiting"], 5.75)

    def test_sjf_beats_fcfs_on_waiting(self):
        self.assertLessEqual(scheduler.sjf(CLASSIC)["avg_waiting"], scheduler.fcfs(CLASSIC)["avg_waiting"])

    def test_srtf_is_optimal_for_waiting(self):
        best = min(r["avg_waiting"] for r in scheduler.run_all(CLASSIC, 2))
        self.assertAlmostEqual(scheduler.srtf(CLASSIC)["avg_waiting"], best)

    def test_round_robin_conserves_burst_time(self):
        r = scheduler.round_robin(CLASSIC, 2)
        run = sum(e - s for pid, s, e in r["gantt"] if pid != "IDLE")
        self.assertEqual(run, sum(p.burst for p in CLASSIC))

    def test_idle_gap_when_cpu_waits(self):
        r = scheduler.fcfs([Process("A", 5, 2)])
        self.assertEqual(r["gantt"][0][0], "IDLE")
        self.assertEqual(r["rows"][0]["completion"], 7)

    def test_boundary_single_process_and_quantum_larger_than_burst(self):
        r = scheduler.round_robin([Process("A", 0, 1)], 100)
        self.assertEqual(r["avg_waiting"], 0)

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            scheduler.fcfs([])
        with self.assertRaises(ValidationError):
            scheduler.round_robin(CLASSIC, 0)
        with self.assertRaises(ValidationError):
            scheduler.fcfs([Process("A", 0, 1), Process("A", 1, 1)])


class TestMemory(unittest.TestCase):
    def test_classic_fault_counts(self):
        self.assertEqual(memory.fifo(REFS, 3)["faults"], 15)
        self.assertEqual(memory.lru(REFS, 3)["faults"], 12)
        self.assertEqual(memory.optimal(REFS, 3)["faults"], 9)

    def test_beladys_anomaly_reproduced(self):
        belady = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        self.assertEqual(memory.fifo(belady, 3)["faults"], 9)
        self.assertEqual(memory.fifo(belady, 4)["faults"], 10)

    def test_boundary_one_frame_every_distinct_ref_faults(self):
        self.assertEqual(memory.fifo([1, 2, 1, 2], 1)["faults"], 4)

    def test_enough_frames_only_compulsory_faults(self):
        self.assertEqual(memory.lru(REFS, 8)["faults"], len(set(REFS)))

    def test_allocation_strategies(self):
        best = memory.allocate([100, 500, 200, 300, 600], [212, 417, 112, 426], "best")
        self.assertEqual(best["unplaced"], [])
        first = memory.allocate([100, 500, 200, 300, 600], [212, 417, 112, 426], "first")
        self.assertEqual(first["unplaced"], [426])

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            memory.fifo([], 3)
        with self.assertRaises(ValidationError):
            memory.fifo(REFS, 0)
        with self.assertRaises(ValidationError):
            memory.allocate([10], [5], "random")
        with self.assertRaises(ValidationError):
            memory.allocate([10, -1], [5])


class TestDeadlock(unittest.TestCase):
    def test_safe_sequence(self):
        safe, seq, _ = deadlock.safety_check(**BANKER)
        self.assertTrue(safe)
        self.assertEqual(seq, ["P1", "P3", "P4", "P0", "P2"])

    def test_request_granted_and_denied(self):
        self.assertTrue(deadlock.request_resources(**BANKER, pid=1, request=[1, 0, 2])[0])
        self.assertFalse(deadlock.request_resources(**BANKER, pid=4, request=[3, 3, 0])[0])
        self.assertFalse(deadlock.request_resources(**BANKER, pid=1, request=[9, 9, 9])[0])

    def test_unsafe_state_detected(self):
        safe, seq, _ = deadlock.safety_check([0, 0], [[1, 0], [0, 1]], [[1, 1], [1, 1]])
        self.assertFalse(safe)

    def test_detection(self):
        dead = deadlock.detect_deadlock([0, 0], [[1, 0], [0, 1]], [[0, 1], [1, 0]])
        self.assertEqual(dead, ["P0", "P1"])
        self.assertEqual(deadlock.detect_deadlock([1, 1], [[1, 0], [0, 1]], [[0, 1], [1, 0]]), [])

    def test_invalid_matrices(self):
        with self.assertRaises(ValidationError):
            deadlock.safety_check([1], [[2]], [[1]])           # allocation > max
        with self.assertRaises(ValidationError):
            deadlock.safety_check([1, 1], [[1]], [[1]])        # width mismatch
        with self.assertRaises(ValidationError):
            deadlock.request_resources(**BANKER, pid=99, request=[0, 0, 0])


class TestDisk(unittest.TestCase):
    Q = [98, 183, 37, 122, 14, 124, 65, 67]

    def test_known_movement(self):
        self.assertEqual(disk.fcfs(53, 199, self.Q)["movement"], 640)
        self.assertEqual(disk.sstf(53, 199, self.Q)["movement"], 236)
        self.assertEqual(disk.scan(53, 199, self.Q)["movement"], 331)
        self.assertEqual(disk.look(53, 199, self.Q)["movement"], 299)

    def test_boundary_head_at_edge_and_single_request(self):
        self.assertEqual(disk.fcfs(0, 10, [0])["movement"], 0)
        self.assertEqual(disk.scan(10, 10, [5])["movement"], 5)

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            disk.fcfs(5, 10, [])
        with self.assertRaises(ValidationError):
            disk.sstf(5, 10, [11])
        with self.assertRaises(ValidationError):
            disk.look(50, 10, [1])


class TestValidationAndFiles(unittest.TestCase):
    def _tmp(self, text, suffix=".csv"):
        fh = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False)
        fh.write(text); fh.close()
        self.addCleanup(os.remove, fh.name)
        return fh.name

    def test_positive_int(self):
        self.assertEqual(validation.positive_int(" 7 "), 7)
        for bad in ("abc", "", "-3", "0", "1.5", None):
            with self.assertRaises(ValidationError):
                validation.positive_int(bad)

    def test_load_valid_csv(self):
        procs = validation.load_processes(self._tmp("pid,arrival,burst,priority\nA,0,3,1\nB,1,2,2\n"))
        self.assertEqual(len(procs), 2)

    def test_bad_csv_variants(self):
        for text in ("pid,arrival\nA,0\n", "pid,arrival,burst\nA,0,0\n", "pid,arrival,burst\nA,x,1\n",
                     "pid,arrival,burst\nA,0,1\nA,1,1\n", "pid,arrival,burst\n"):
            with self.assertRaises(ValidationError):
                validation.load_processes(self._tmp(text))

    def test_missing_file(self):
        with self.assertRaises(ValidationError):
            validation.load_processes("/no/such/file.csv")

    def test_bad_json(self):
        with self.assertRaises(ValidationError):
            validation.load_banker(self._tmp("{not json", ".json"))
        with self.assertRaises(ValidationError):
            validation.load_banker(self._tmp('{"available":[1]}', ".json"))

    def test_bundled_datasets_load(self):
        d = os.path.join(ROOT, "data")
        self.assertEqual(len(validation.load_processes(os.path.join(d, "processes_large.csv"))), 40)
        self.assertEqual(len(validation.load_page_refs(os.path.join(d, "page_refs_large.txt"))), 300)
        self.assertEqual(validation.load_disk_requests(os.path.join(d, "disk_requests.txt"))[0], 53)


class TestBashIntegration(unittest.TestCase):
    def test_sysinfo(self):
        ok, info = bashbridge.system_info()
        if ok:
            self.assertIn("MEM_TOTAL_MB", info)

    def test_missing_script_and_log(self):
        self.assertFalse(bashbridge.run_script("nope.sh")[0])
        self.assertFalse(bashbridge.log_summary("/no/such.log")[0])


class TestCLI(unittest.TestCase):
    def test_menu_survives_garbage_input(self):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "main.py")],
                              input="abc\n99\n\n0\n", capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Please choose a number", proc.stdout)

    def test_menu_rejects_bad_numbers_then_accepts(self):
        stdin = "1\nc\nzero\n-1\n1\n0\n3\n1\n2\n0\n\n0\n"   # 1 proc: arrival 0, burst 3, prio 1, quantum default
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "main.py")],
                              input=stdin, capture_output=True, text=True, timeout=30)
        self.assertIn("[!]", proc.stdout)
        self.assertIn("Algorithm comparison", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
