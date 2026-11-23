#! /usr/bin/env python3
"""Monty Hall simulation, generalized to n doors and m reveals.

Model:
  - The contestant picks one of n doors uniformly at random.
  - The host knows the car and opens exactly m goat doors, chosen
    uniformly among doors that are neither the pick nor the car
    (1 <= m <= n-2, so at least one other closed door remains).
  - If switching, the contestant re-picks uniformly among the n-1-m
    doors that are neither the original pick nor revealed.

Under this model the exact win probabilities are
    stay:   1/n
    switch: (n-1) / (n * (n-m-1))
For m=1, n=3 this is the classic result (1/3 vs 2/3); m=n-2 gives
switch = (n-1)/n. See `enumerate` for an exhaustive exact check.
"""

import argparse
import itertools
import math
import random
import sys
from fractions import Fraction

NUM_DOORS = 3
SEED = 42

MIN_DOORS = 3
MAX_DOORS = 5
NUM_ROUNDS = 1_000_000


def validate(n, rounds=1, reveals=1):
    if n < 3:
        raise ValueError("need at least 3 doors")
    if rounds < 1:
        raise ValueError("rounds must be >= 1")
    if not 1 <= reveals <= n - 2:
        raise ValueError(f"reveals must be 1..{n - 2} for {n} doors")


# Single round; door values are 0-indexed internally, printed +1.
def play_round(n, change, rng, log=False, reveals=1):
    validate(n, reveals=reveals)
    doors = range(n)
    win = rng.choice(doors)
    pick = rng.choice(doors)
    revealed = rng.sample([d for d in doors if d not in (pick, win)], reveals)
    if log:
        print(f"Contestant selected door {pick + 1}")
        shown = ", ".join(str(d + 1) for d in revealed)
        print(f"Host revealed {shown} ({reveals} door{'s' if reveals > 1 else ''})")
    if change:
        pick = rng.choice([d for d in doors if d != pick and d not in revealed])
        if log:
            print(f"Contestant changed their selection to door {pick + 1}")
    if log:
        print(f"Winning door was {win + 1}: Contestant {'wins!' if pick == win else 'loses...'}")
    return {"win": pick == win, "selected_door": pick,
            "revealed_doors": revealed, "win_door": win}


def simulate(n, change, rounds, rng, reveals=1):
    validate(n, rounds, reveals)
    return sum(play_round(n, change, rng, reveals=reveals)["win"] for _ in range(rounds))


# Exact win probability under the modeled host behavior.
def theory(n, change, reveals=1):
    validate(n, reveals=reveals)
    return Fraction(n - 1, n * (n - reveals - 1)) if change else Fraction(1, n)


# Normal-approx 95% CI half-width, expressed as a probability.
def ci95(wins, rounds):
    p = wins / rounds
    return 1.96 * math.sqrt(p * (1 - p) / rounds)


# Exhaustive enumeration over all (car, pick, reveal-set) outcomes.
# Exact for this host model; only practical for small n.
def enumerate_exact(n, reveals=1):
    validate(n, reveals=reveals)
    stay = switch = Fraction(0)
    for car in range(n):
        for pick in range(n):
            goats = [d for d in range(n) if d not in (pick, car)]
            subsets = list(itertools.combinations(goats, reveals))
            w = Fraction(1, n * n * len(subsets))  # weight per reveal-set
            for _ in subsets:
                if pick == car:
                    stay += w
                else:
                    # switch re-picks uniformly among n-1-reveals doors;
                    # the car is one of them
                    switch += w / (n - 1 - reveals)
    return stay, switch


def _cell(n, change, reveals, rounds, rng, out):
    w = simulate(n, change, rounds, rng, reveals)
    sim = 100 * w / rounds
    th = 100 * float(theory(n, change, reveals))
    hw = 100 * ci95(w, rounds)
    out(f" {n:<7} | {reveals:>8} | {change!s:>7} | {w:>6} | {sim:6.2f} | {th:8.2f} | {hw:9.2f} | {abs(sim - th) <= hw}")


# Classic sweep: n doors, single reveal (m=1).
def sweep(lo, hi, rounds, rng, reveals=1, out=print):
    out(f"=== Monty Hall sweep: doors {lo}-{hi}, {reveals} reveal(s), {rounds} rounds/cell ===")
    out(" # Doors | Reveals | Change? |   Wins | Sim %  | Theory % | 95% CI ±% | In CI")
    for n in range(lo, hi + 1):
        for change in (True, False):
            _cell(n, change, reveals, rounds, rng, out)
    out("")
    out("Derived from theory, not simulation: the chosen door keeps probability 1/n;")
    out("the remaining (n-1)/n is shared equally by the unchosen, unrevealed doors.")


# Advanced sweep: n doors x m reveals (m = 1..n-2) x strategies.
def adv_sweep(lo, hi, rounds, rng, out=print):
    out(f"=== Monty Hall advanced sweep: doors {lo}-{hi}, 1..n-2 reveals, {rounds} rounds/cell ===")
    out(" # Doors | Reveals | Change? |   Wins | Sim %  | Theory % | 95% CI ±% | In CI")
    for n in range(lo, hi + 1):
        for m in range(1, n - 1):
            for change in (True, False):
                _cell(n, change, m, rounds, rng, out)
    out("")
    out("Derived from theory, not simulation: the chosen door keeps probability 1/n;")
    out("the revealed doors' m/n is shared equally by the n-1-m open, unchosen doors.")
    for n in range(lo, hi + 1):
        for m in range(1, n - 1):
            stay = 100 * float(theory(n, False, m))
            per_open = 100 * float(Fraction(n - 1, n) / (n - 1 - m))
            out(f" n={n}, m={m}: chosen door {stay:.2f}% / each open unchosen door {per_open:.2f}%")


def build_parser():
    p = argparse.ArgumentParser(
        prog="src/montyhall.py",
        description="Monty Hall simulation: stay vs switch, n doors, m reveals.")
    sub = p.add_subparsers(dest="cmd", required=True)

    seed = argparse.ArgumentParser(add_help=False)
    seed.add_argument("--seed", type=int, default=SEED,
                      help=f"RNG seed (default {SEED})")

    r = sub.add_parser("round", parents=[seed], help="play one traced round")
    r.add_argument("--doors", type=int, default=NUM_DOORS)
    r.add_argument("--change", action="store_true", help="switch after the reveal")
    r.add_argument("--reveals", type=int, default=1)

    u = sub.add_parser("run", parents=[seed], help="simulate many rounds")
    u.add_argument("--doors", type=int, default=NUM_DOORS)
    u.add_argument("--change", action="store_true")
    u.add_argument("--reveals", type=int, default=1)
    u.add_argument("--rounds", type=int, default=NUM_ROUNDS)

    s = sub.add_parser("sweep", parents=[seed], help="sweep door counts x strategies (1 reveal)")
    s.add_argument("--min-doors", type=int, default=MIN_DOORS)
    s.add_argument("--max-doors", type=int, default=MAX_DOORS)
    s.add_argument("--rounds", type=int, default=NUM_ROUNDS)

    a = sub.add_parser("adv", parents=[seed], help="sweep doors x reveals x strategies")
    a.add_argument("--min-doors", type=int, default=MIN_DOORS)
    a.add_argument("--max-doors", type=int, default=6)
    a.add_argument("--rounds", type=int, default=NUM_ROUNDS)

    e = sub.add_parser("enumerate", help="exact enumeration vs theory (all m)")
    e.add_argument("--min-doors", type=int, default=MIN_DOORS)
    e.add_argument("--max-doors", type=int, default=8)

    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    rng = random.Random(getattr(a, "seed", SEED))
    try:
        if a.cmd == "round":
            play_round(a.doors, a.change, rng, log=True, reveals=a.reveals)
        elif a.cmd == "run":
            w = simulate(a.doors, a.change, a.rounds, rng, a.reveals)
            sim = 100 * w / a.rounds
            th = 100 * float(theory(a.doors, a.change, a.reveals))
            hw = 100 * ci95(w, a.rounds)
            print(f"{a.rounds} rounds, {a.doors} doors, {a.reveals} reveals, "
                  f"change={a.change}: {w} wins = {sim:.2f}% "
                  f"(theory {th:.2f}%, 95% CI ±{hw:.2f}%)")
        elif a.cmd == "sweep":
            sweep(a.min_doors, a.max_doors, a.rounds, rng)
        elif a.cmd == "adv":
            adv_sweep(a.min_doors, a.max_doors, a.rounds, rng)
        else:  # enumerate
            print(" # Doors | Reveals | Stay (exact) | Switch (exact) | Matches theory")
            for n in range(a.min_doors, a.max_doors + 1):
                for m in range(1, n - 1):
                    s, w = enumerate_exact(n, m)
                    match = (s, w) == (theory(n, False, m), theory(n, True, m))
                    if not match:
                        raise RuntimeError(f"enumeration != theory for n={n}, m={m}: {(s, w)}")
                    print(f" {n:<7} | {m:>7} | {str(s):>12} | {str(w):>14} | {match}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
