"""Tests for src/montyhall.py. Fast, seeded, deterministic.

main.py is the user's exploratory script (unseeded, evolving): it gets
smoke-level coverage only. archive/main_original.py is v0, guarded by a
pinned sha256.
"""

import hashlib
import io
import random
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from math import sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import montyhall as mh  # noqa: E402

ORIGINAL_SHA256 = "0747b70efb8f3c7689d482e52d2aab3dcb03c66861f723423ce2e6464198ae80" # sha256sum of archive/main.py

class Rules(unittest.TestCase):
    def test_reveal_valid(self):
        for n in range(3, 7):
            for m in range(1, n - 1):
                rng = random.Random(1)
                for _ in range(2000):
                    res = mh.play_round(n, False, rng, reveals=m)
                    rev = res["revealed_doors"]
                    self.assertEqual(len(rev), m)
                    self.assertEqual(len(set(rev)), m)
                    self.assertNotIn(res["win_door"], rev)
                    self.assertNotIn(res["selected_door"], rev)

    def test_switch_excludes_revealed(self):
        for n, m in ((3, 1), (4, 1), (5, 3), (6, 2)):
            rng = random.Random(2)
            for _ in range(2000):
                res = mh.play_round(n, True, rng, reveals=m)
                self.assertNotIn(res["selected_door"], res["revealed_doors"])

    def test_single_open_door_forced(self):
        # n=5, m=3 leaves exactly one unchosen open door; switch must land
        # there. Scripted RNG: car=0, pick=1, reveals={2,3,4} -> only door 0
        # remains -> switch must win.
        class FakeRng:
            def __init__(self):
                self._choices = iter([0, 1, 0])
            def choice(self, seq):
                return next(self._choices)
            def sample(self, seq, k):
                return list(seq)[:k]
        res = mh.play_round(5, True, FakeRng(), reveals=3)
        self.assertEqual(res["revealed_doors"], [2, 3, 4])
        self.assertEqual(res["selected_door"], 0)
        self.assertTrue(res["win"])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            mh.play_round(2, False, random.Random(0))
        with self.assertRaises(ValueError):
            mh.simulate(3, False, 0, random.Random(0))
        with self.assertRaises(ValueError):
            mh.play_round(3, False, random.Random(0), reveals=0)
        with self.assertRaises(ValueError):
            mh.play_round(5, False, random.Random(0), reveals=4)  # m must be <= n-2


class Repro(unittest.TestCase):
    def test_same_seed_same_result(self):
        a = mh.simulate(3, True, 2000, random.Random(1))
        b = mh.simulate(3, True, 2000, random.Random(1))
        self.assertEqual(a, b)

    def test_different_seed_differs(self):
        a = mh.simulate(3, True, 2000, random.Random(1))
        b = mh.simulate(3, True, 2000, random.Random(2))
        self.assertNotEqual(a, b)


class Exact(unittest.TestCase):
    def test_enumeration_matches_theory(self):
        for n in range(3, 9):
            for m in range(1, n - 1):
                stay, switch = mh.enumerate_exact(n, m)
                self.assertEqual(stay, mh.theory(n, False, m))
                self.assertEqual(switch, mh.theory(n, True, m))

    def test_classic_values(self):
        self.assertEqual(mh.enumerate_exact(3), (Fraction(1, 3), Fraction(2, 3)))

    def test_theory_formula(self):
        self.assertEqual(mh.theory(5, True, 3), Fraction(4, 5))   # 20/80
        self.assertEqual(mh.theory(4, True, 1), Fraction(3, 8))   # m=1 classic family
        self.assertEqual(mh.theory(6, True, 4), Fraction(5, 6))   # m=n-2 limit
        for n in range(3, 8):
            for m in range(1, n - 1):
                self.assertEqual(mh.theory(n, False, m), Fraction(1, n))

    def test_redistribution_identity(self):
        # After the reveal: chosen door keeps 1/n; each of the m revealed
        # doors drops 1/n -> 0 (mass m/n); each of the n-1-m open unchosen
        # doors goes from 1/n to (n-1)/n/(n-1-m). Mass must balance.
        for n in range(3, 9):
            for m in range(1, n - 1):
                chosen = Fraction(1, n)
                per_open = Fraction(n - 1, n * (n - 1 - m))
                self.assertEqual(chosen + (n - 1 - m) * per_open, 1)
                # mass gained by open doors == mass lost by revealed doors
                gained = (n - 1 - m) * (per_open - Fraction(1, n))
                self.assertEqual(gained, Fraction(m, n))


class Stats(unittest.TestCase):
    def test_sim_near_theory(self):
        # 4 standard-error tolerance; seeded so the result is deterministic.
        rounds = 30000
        for n, m in ((3, 1), (4, 1), (4, 2), (5, 3), (6, 2), (6, 4)):
            for change in (True, False):
                rng = random.Random(42)
                p = mh.simulate(n, change, rounds, rng, reveals=m) / rounds
                th = float(mh.theory(n, change, m))
                tol = 4 * sqrt(th * (1 - th) / rounds)
                self.assertAlmostEqual(p, th, delta=tol, msg=f"n={n} m={m} change={change}")


class CLI(unittest.TestCase):
    def test_no_args_exits_2(self):
        with self.assertRaises(SystemExit) as c, redirect_stdout(io.StringIO()):
            mh.main([])
        self.assertEqual(c.exception.code, 2)

    def test_sweep_smoke(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(mh.main(["sweep", "--rounds", "500"]), 0)

    def test_adv_smoke(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(mh.main(["adv", "--rounds", "300"]), 0)
        self.assertIn("Reveals", out.getvalue())
        self.assertIn("80.00", out.getvalue())  # n=5 m=3 open-door share

    def test_enumerate_smoke(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(mh.main(["enumerate"]), 0)
        self.assertIn("1/3", out.getvalue())
        self.assertIn("4/5", out.getvalue())  # n=5, m=3 switch

    def test_run_reveals(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(mh.main(["run", "--doors", "5", "--reveals", "3",
                                      "--change", "--rounds", "100"]), 0)

    def test_bad_reveals(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(mh.main(["run", "--doors", "5", "--reveals", "4",
                                      "--rounds", "10"]), 2)

    def test_bad_doors(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(mh.main(["run", "--doors", "2", "--rounds", "10"]), 2)


class MainPy(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run([sys.executable, "archive/main.py", *args], cwd=ROOT,
                              capture_output=True, text=True, timeout=120)

    def test_usage(self):
        r = self._run()
        self.assertEqual(r.returncode, 0)
        self.assertIn("Usage", r.stdout)

    def test_round_no_crash(self):
        # regression: used to hit NameError on `num_revealed`
        self.assertEqual(self._run("round").returncode, 0)


class Archive(unittest.TestCase):
    def test_original_v0_unchanged(self):
        digest = hashlib.sha256((ROOT / "archive" / "main.py").read_bytes()).hexdigest()
        self.assertEqual(digest, ORIGINAL_SHA256)


if __name__ == "__main__":
    unittest.main()
