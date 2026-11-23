# Monty Hall, generalized to n doors and m reveals

An exploratory simulation project: does switching doors beat staying
in the Monty Hall game — and how does the answer generalize to `n` doors
with `m` goat reveals?

## Question / hypothesis

The contestant picks one of `n` doors; the host reveals goats behind `m`
other doors; the contestant may switch. The rumor is that switching
always wins more often than staying, for every `n ≥ 3` and `1 ≤ m ≤ n-2`.

## Model and assumptions

- Contestant's first pick is uniform over `n` doors.
- The host knows the car and always opens **exactly `m`** goat doors,
  chosen uniformly among doors that are neither the pick nor the car
  (`m` ranges `1..n-2`, so at least one other closed door remains).
- If switching, the contestant re-picks uniformly among the `n-1-m`
  doors that are neither the original pick nor revealed.
- `n = 3, m = 1` is the classic puzzle. `m = n-2` is the n-door
  generalization.

**For future research:** Non-uniform selection for constant and host choices.

## Reproduce

Requires Python ≥ 3.8, but no dependencies. Run from the repo root:

```
python3 -m unittest discover -s tests -v          # tests (fast)
python3 src/montyhall.py round --seed 1 --change  # one traced round
python3 src/montyhall.py run --doors 5 --reveals 3 --change --rounds 100000
python3 src/montyhall.py sweep --rounds 100000    # quick 1-reveal sweep (~2 s)
python3 src/montyhall.py sweep                    # default 1M rounds/cell (~15 s)
python3 src/montyhall.py adv --rounds 100000      # doors x reveals x strategies
python3 src/montyhall.py enumerate --min-doors 3 --max-doors 8  # exact check
```

`python3 archive/main.py [round|run|sweep|adv]` is the original exploratory script.

## Results

`python3 src/montyhall.py adv --rounds 100000`, seed 42, Python 3.12.3,
2026-11-19 — deterministic for this environment. A cell's "In CI" column
says whether the simulated rate lies within its own 95% CI of theory.

| Doors | Reveals | Change? | Wins  | Sim %  | Theory % | 95% CI ±% |
|-------|---------|---------|-------|--------|----------|-----------|
|   3   |    1    |   True  | 66494 |  66.49 |    66.67 |    0.29   |
|   3   |    1    |  False  | 33459 |  33.46 |    33.33 |    0.29   |
|   4   |    1    |   True  | 37633 |  37.63 |    37.50 |    0.30   |
|   4   |    1    |  False  | 25044 |  25.04 |    25.00 |    0.27   |
|   4   |    2    |   True  | 75246 |  75.25 |    75.00 |    0.27   |
|   4   |    2    |  False  | 25060 |  25.06 |    25.00 |    0.27   |
|   5   |    1    |   True  | 26759 |  26.76 |    26.67 |    0.27   |
|   5   |    1    |  False  | 20094 |  20.09 |    20.00 |    0.25   |
|   5   |    2    |   True  | 39900 |  39.90 |    40.00 |    0.30   |
|   5   |    2    |  False  | 19906 |  19.91 |    20.00 |    0.25   |
|   5   |    3    |   True  | 79680 |  79.68 |    80.00 |    0.25   |
|   5   |    3    |  False  | 19874 |  19.87 |    20.00 |    0.25   |
|   6   |    4    |   True  | 83348 |  83.35 |    83.33 |    0.23   |
|   6   |    4    |  False  | 16476 |  16.48 |    16.67 |    0.23   |

(Subset of the full table for brevity — run `adv` for all cells.)

Exact enumeration over all `(car, pick, reveal-set)` outcomes
(`enumerate`, verified exactly for n = 3..8 and every legal m) gives:

    stay   = 1/n
    switch = (n-1) / (n · (n-m-1))

e.g. n=3,m=1: 1/3 vs 2/3 · n=5,m=3: 1/5 vs 4/5 · m=n-2: 1/n vs (n-1)/n.

## Interpretation

- The general claim: staying keeps `P(win) = 1/n`;
  switching wins iff the car was behind another door (`(n-1)/n`) and
  then picked among the `n-1-m` legal doors (`1/(n-1-m)`), so
  `P(switch) = (n-1)/(n(n-m-1))`. Ratio `(n-1)/(n-m-1) ≥ 1`, with
  equality only at m = 0 — every reveal favors switching.
- Redistribution: the reveal does **not** add probability to the chosen
  door (it stays `1/n`). Each revealed door loses its `1/n` share, so
  `m/n` total is redistributed equally over the `n-1-m` open unchosen
  doors, each ending at `(n-1)/n/(n-1-m)`. At n=5, m=3 that leaves
  exactly one alternative door at 80% vs the chosen door's 20% — the
  choice is emphatically not 50/50.

## Implementation notes

- The initial script used finit sampling to estimate the probabilities.
  That is kept in the final `montyhall.py` script, but exact enumeration
  is also available.
- Exact enumeration covers n = 3..8; simulation covered n = 3..6.
- One host model (informed, uniform, always offers a switch) and one
  switch rule (uniform among open doors). Biased hosts and
  restricted switch choices are open questions.

## File status

| File | Status |
|------|--------|
| `src/montyhall.py` | current, reproducible implementation + CLI (n doors, m reveals) |
| `tests/test_montyhall.py` | current; guards rules, seeding, exact values, redistribution identity, CLI |
| `archive/main.py` | original exploratory script, pinned in tests and smoke-tested |
