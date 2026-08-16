#!/usr/bin/env python3
"""No number in the README without a runnable path behind it.

Every number quoted below is recomputed here from the CSVs bundled in
data/ or from the notebook sources themselves, and then asserted to be
present in README.md as a literal substring. Nothing is hardcoded on
both sides, so the README and its artifacts cannot drift apart quietly.

Four groups:
1. Structure. Each notebook in notebooks/ carries strictly sequential
   execution counts starting at 1 and zero error outputs, the CSVs the
   notebooks read are committed and non-empty, and the traffic file is
   the strict hourly grid data/build_dataset.py promises.
2. Notebook 01. The aliasing demo and the hand-made probe, rerun.
3. Notebook 02. The Keeling curve: trend = 12-month centred rolling
   mean, anom = co2 - trend, climatology = anom by calendar month.
   The notebook hardcodes the month NAMES while computing the values,
   so the recomputed peak and trough months are checked against those
   names too.
4. Notebook 03. Hour-of-week climatology against harmonic regression on
   held-out 2018, the per-slot z-score alarm, and the April weekend.

README comparisons run against a whitespace-flattened copy, because the
README is hard-wrapped and most claims straddle a line break.

Offline and stdlib + numpy/pandas only: no notebook is re-executed, no
model is refit beyond two least-squares solves, no URL is touched.
"""

import ast
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.fft import rfft, rfftfreq

# Some BLAS builds raise spurious matmul warnings inside lstsq, exactly as
# notebook 03 notes when it silences them.
warnings.filterwarnings("ignore", message=".*encountered in matmul.*")

REPO = Path(__file__).resolve().parent.parent

MONTHS = [None, "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
         "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = [None, None, "twenty", "thirty", "forty", "fifty", "sixty",
        "seventy", "eighty", "ninety"]

problems = []


def check(name, condition, detail=""):
    print(f"  {'ok ' if condition else 'FAIL'} {name}" +
          (f" ({detail})" if detail and not condition else ""))
    if not condition:
        problems.append(name)


def spelled(n: int) -> str:
    """English for 0-99, so 'sixty-eight years' is derived, not assumed."""
    if n < 20:
        return UNITS[n]
    tens, units = divmod(n, 10)
    return TENS[tens] + (f"-{UNITS[units]}" if units else "")


def flatten(text: str) -> str:
    return " ".join(text.split())


def notebooks():
    return sorted((REPO / "notebooks").glob("*.ipynb"))


def source_of(path: Path) -> list:
    nb = json.loads(path.read_text(encoding="utf-8"))
    return [(c, "".join(c["source"])) for c in nb["cells"]
            if c["cell_type"] == "code"]


def probe_line_count(cell_sources: list) -> int:
    """Lines of the hand-made probe(), docstring and blanks excluded."""
    src = next((s for s in cell_sources if "def probe(" in s), "")
    # Comment out IPython magics so ast can parse the cell verbatim; the
    # substitution is the same width, so line numbers stay honest.
    src = re.sub(r"^([%!])", r"#\1", src, flags=re.M)
    lines = src.splitlines()
    for node in ast.walk(ast.parse(src or "pass")):
        if isinstance(node, ast.FunctionDef) and node.name == "probe":
            body = lines[node.lineno - 1:node.end_lineno]
            doc = node.body[0]
            skip = set()
            if isinstance(doc, ast.Expr) and isinstance(doc.value, ast.Constant) \
                    and isinstance(doc.value.value, str):
                skip = set(range(doc.lineno, doc.end_lineno + 1))
            return sum(1 for i, ln in enumerate(body, start=node.lineno)
                       if ln.strip() and i not in skip)
    return 0


def hour_of_week(index):
    return index.dayofweek * 24 + index.hour


def main() -> int:
    readme_raw = (REPO / "README.md").read_text(encoding="utf-8")
    readme = flatten(readme_raw)

    print("notebooks are executed clean:")
    nbs = notebooks()
    check("notebooks/ holds at least one notebook", bool(nbs))
    for path in nbs:
        cells = source_of(path)
        counts = [c.get("execution_count") for c, _ in cells]
        check(f"{path.name}: execution counts are 1..{len(counts)} in order",
              counts == list(range(1, len(counts) + 1)), str(counts))
        errors = sum(1 for c, _ in cells for o in c.get("outputs", [])
                     if o.get("output_type") == "error")
        check(f"{path.name}: no cell output is an error", errors == 0,
              f"{errors} error output(s)")
    check(f"README badge says notebooks-{len(nbs)}%20executed",
          f"notebooks-{len(nbs)}%20executed" in readme)

    print("bundled data the notebooks read:")
    wanted = sorted({m for _, src in
                     [c for p in nbs for c in source_of(p)]
                     for m in re.findall(r"\.\./data/([\w.\-]+)", src)})
    check("notebooks name at least one bundled CSV", bool(wanted))
    for name in wanted:
        f = REPO / "data" / name
        check(f"data/{name} is committed and non-empty",
              f.exists() and f.stat().st_size > 0)
    py_req = re.search(r"Python\s*>=\s*([\d.]+)",
                       (REPO / "requirements.txt").read_text(encoding="utf-8"))
    check("requirements.txt states a Python floor", py_req is not None)
    if py_req:
        check(f"README badge matches that floor (python-{py_req.group(1)}%2B)",
              f"python-{py_req.group(1)}%2B" in readme)

    co2 = (pd.read_csv(REPO / "data" / "co2_mm_mlo.csv", parse_dates=["date"])
           .set_index("date")["co2"])
    traf = (pd.read_csv(REPO / "data" / "metro_traffic.csv",
                        parse_dates=["date_time"]).set_index("date_time"))
    v = traf["traffic_volume"]
    grid = pd.date_range(v.index.min(), v.index.max(), freq="h")
    check("metro_traffic.csv is the strict hourly grid, no gaps or dupes",
          v.index.equals(grid),
          f"{len(v)} rows against a {len(grid)}-hour grid")
    check("README calls it a strict hourly grid",
          "strict hourly grid" in readme)

    print("notebook 01, the transform by hand:")
    cells_by_nb = {p.name: [s for _, s in source_of(p)] for p in nbs}
    src01 = "\n".join(cells_by_nb.get("01_fourier_from_scratch.ipynb", []))
    n_lines = probe_line_count(cells_by_nb.get(
        "01_fourier_from_scratch.ipynb", []))
    check(f"probe() is {spelled(n_lines)} lines of numpy", n_lines > 0,
          "probe() not found")
    check(f"README says 'in {spelled(n_lines)} lines of numpy'",
          f"in {spelled(n_lines)} lines of numpy" in readme)

    fs_m = re.search(r"fs_slow\s*=\s*(\d+)", src01)
    f0_m = re.search(r"samples\s*=\s*np\.cos\(2 \* np\.pi \* (\d+) \* t_slow\)",
                     src01)
    check("the aliasing cell states its true frequency and sample rate",
          fs_m is not None and f0_m is not None)
    if fs_m and f0_m:
        fs_slow, f0 = int(fs_m.group(1)), int(f0_m.group(1))
        t_slow = np.arange(0, 1, 1 / fs_slow)
        spec = np.abs(rfft(np.cos(2 * np.pi * f0 * t_slow))) * 2 / len(t_slow)
        alias = rfftfreq(len(t_slow), d=1 / fs_slow)[np.argmax(spec)]
        sentence = (f"a {f0} Hz wave sampled at {fs_slow} per second "
                    f"swears it is {alias:.0f} Hz")
        check(f"README quotes the alias ({sentence})", sentence in readme)

    print("notebook 02, the Keeling curve:")
    src02 = "\n".join(
        cells_by_nb.get("02_seasonality_in_the_keeling_curve.ipynb", []))
    lo, hi = co2.index.min(), co2.index.max()
    check(f"README dates the CO2 record ({lo.year} to {hi.year})",
          f"Mauna Loa, {lo.year} to {hi.year}" in readme)
    years = hi.year - lo.year
    check(f"README says {spelled(years)} years of atmospheric CO2",
          f"{spelled(years)} years of atmospheric CO2" in readme)

    anom = (co2 - co2.rolling(12, center=True).mean()).dropna()
    clim = anom.groupby(anom.index.month).mean()
    peak_m, trough_m = int(clim.idxmax()), int(clim.idxmin())
    # The notebook hardcodes these month NAMES in its print string while
    # computing the values from the data, so a data refresh could move the
    # month and leave the name behind. These two checks are that tripwire.
    check(f"notebook 02's hardcoded peak month is still the computed one "
          f"({MONTHS[peak_m]}, month {peak_m})",
          f"peak month: {MONTHS[peak_m]}" in src02
          and f"clim[{peak_m}]" in src02)
    check(f"notebook 02's hardcoded trough month is still the computed one "
          f"({MONTHS[trough_m]}, month {trough_m})",
          f"trough: {MONTHS[trough_m]}" in src02
          and f"clim[{trough_m}]" in src02)
    runner_up = clim.drop(index=trough_m).min() - clim.min()
    print(f"       note: the trough leads its runner-up by only "
          f"{runner_up:.3f} ppm, so those names are one refresh from stale")

    nd = len(anom)
    amp = np.abs(rfft(anom.values)) * 2 / nd
    nearest_bin = amp[np.argmax(amp[1:]) + 1]
    t_yr = np.arange(nd) / 12
    cols = []
    for harmonic in (1, 2, 3):
        cols += [np.sin(2 * np.pi * harmonic * t_yr),
                 np.cos(2 * np.pi * harmonic * t_yr)]
    beta, *_ = np.linalg.lstsq(np.column_stack(cols), anom.values, rcond=None)
    fundamental = float(np.hypot(beta[0], beta[1]))
    swing = clim.max() - clim.min()
    trio = (f"the nearest-bin FFT readout ({nearest_bin:.0f} ppm), "
            f"the true fundamental ({fundamental:.1f} ppm), and "
            f"the calendar swing ({swing:.1f} ppm)")
    check(f"README reconciles the three amplitudes ({trio})", trio in readme)

    print("notebook 03, demand rhythms and staffing:")
    t_lo, t_hi = v.index.min(), v.index.max()
    check(f"README dates the traffic record "
          f"({t_lo:%B %Y} to {t_hi:%B %Y})",
          f"{t_lo:%B %Y} to {t_hi:%B %Y}" in readme)
    months = (t_hi.year - t_lo.year) * 12 + t_hi.month - t_lo.month + 1
    check(f"README says {spelled(months)} months of real hourly traffic",
          f"{spelled(months)} months of real hourly traffic" in readme)

    train, test = v.loc[:"2017-12-31"], v.loc["2018-01-01":]
    how_tr, how_te = hour_of_week(train.index), hour_of_week(test.index)
    prof = train.groupby(how_tr).mean()
    check(f"README calls the lookup table {len(prof)}-slot",
          f"{len(prof)}-slot hour-of-week lookup table" in readme)

    pred = pd.Series(how_te.map(prof), index=test.index)
    mae_clim = (test - pred).abs().mean()
    t0 = v.index[0]

    def design(index, K):
        t = (index - t0).total_seconds().values / 3600.0
        cols = [np.ones(len(t))]
        for period in (24.0, 168.0):
            for k in range(1, K + 1):
                cols.append(np.sin(2 * np.pi * k * t / period))
                cols.append(np.cos(2 * np.pi * k * t / period))
        return np.column_stack(cols)

    mae_harm = []
    for K in (3, 6, 10):
        b, *_ = np.linalg.lstsq(design(train.index, K), train.values,
                                rcond=None)
        mae_harm.append(np.abs(test.values - design(test.index, K) @ b).mean())
    best_harm = min(mae_harm)
    check("climatology beats every harmonic regression on held-out 2018",
          mae_clim < best_harm,
          f"{mae_clim:.0f} against a best harmonic of {best_harm:.0f}")
    verdict = (f"{mae_clim:.0f} versus roughly {round(best_harm / 100) * 100:.0f} "
               f"vehicles per hour of error")
    check(f"README quotes the backtest ({verdict})", verdict in readme)

    sigma = (train - pd.Series(how_tr.map(prof),
                               index=train.index)).groupby(how_tr).std()
    z = (test - pred) / pd.Series(how_te.map(sigma), index=test.index)
    flags = z[z.abs() > 3]
    rate = len(flags) / len(test)
    check(f"README quotes the flag rate ({rate:.1%} of hours flagged)",
          f"{rate:.1%} of hours flagged" in readme)
    check(f"README repeats it in the real-world section (a {rate:.1%} "
          f"flag rate)", f"a {rate:.1%} flag rate" in readme)

    by_day = pd.Series(flags.index.date).value_counts()
    weekend = [d for d in by_day.index if pd.Timestamp(d).dayofweek >= 5]
    check("a weekend day is among the flagged days", bool(weekend))
    if weekend:
        worst = pd.Timestamp(weekend[0])
        saturday = worst - pd.Timedelta(days=worst.dayofweek - 5)
        pair = [saturday, saturday + pd.Timedelta(days=1)]
        temps = traf.loc[f"{pair[0]:%Y-%m-%d}":f"{pair[1]:%Y-%m-%d}", "temp_c"]
        check(f"that weekend is sub-freezing ({temps.mean():.1f} C mean)",
              temps.mean() < 0, f"{temps.mean():.1f} C")
        # The README's figure is the deeper of the weekend's two days, which
        # is the number notebook 03 prints for that Saturday.
        deepest = max(1 - test.loc[f"{d:%Y-%m-%d}"].sum()
                      / pred.loc[f"{d:%Y-%m-%d}"].sum() for d in pair)
        phrase = (f"a sub-freezing {MONTHS[saturday.month]} weekend "
                  f"that cut demand by {deepest:.0%}")
        check(f"README quotes that weekend ({phrase})", phrase in readme)

    print("README's local links resolve:")
    targets = set(re.findall(r'(?:src|srcset|href)="([^"]+)"', readme_raw))
    targets |= set(re.findall(r"\]\(([^)]+)\)", readme_raw))
    local = sorted(t for t in targets
                   if not t.startswith(("http", "#", "mailto:")))
    check("README links to local files at all", bool(local))
    for target in local:
        check(f"{target} exists", (REPO / target.split("#")[0]).exists())

    if problems:
        print(f"\n{len(problems)} README claim(s) drifted: {problems}")
        return 1
    print("\nevery quoted README number matches its artifact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
