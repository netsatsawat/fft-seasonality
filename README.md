<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="pic/banner-dark.png">
    <img src="pic/banner-light.png" alt="FFT and the art of finding seasonality" width="100%">
  </picture>
</h1>

<p align="center">
  <a href="#-the-notebooks">Notebooks</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#-where-this-applies-in-the-real-world">Real-world uses</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#-running-it-yourself">Run it</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="https://satsawat.ai/#newsletter">Newsletter</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+"></a>
  <a href="notebooks/"><img src="https://img.shields.io/badge/notebooks-3%20executed-eb6834?style=for-the-badge&logo=jupyter&logoColor=white" alt="Notebooks: 3, executed"></a>
  <img src="https://img.shields.io/badge/data-NOAA%20%2B%20UCI%2C%20bundled-1baf7a?style=for-the-badge" alt="Real data, bundled">
  <img src="https://img.shields.io/badge/every%20number-verified%20twice-8a5cf6?style=for-the-badge" alt="Every number verified twice">
  <a href="https://satsawat.ai"><img src="https://img.shields.io/badge/author-satsawat.ai-e8a112?style=for-the-badge" alt="Author: satsawat.ai"></a>
</p>

A three-notebook tutorial on finding repeating patterns in time series
data, written for someone with basic Python and no signal processing
background. It starts by building the Fourier transform by hand in four
lines of numpy, proves the toolkit on sixty-eight years of atmospheric
CO2, and ends where an operations team would spend the results: a demand
baseline, an anomaly alarm, and a capacity table for thirty-three months
of real hourly traffic.

If "Fourier transform" means nothing to you yet, here is why you might
care. Every operational series has rhythms in it: sales swell before
payday, servers run hot every evening, call queues explode on Monday
mornings. Everyone in the meeting sort of knows these patterns; nobody
can say exactly how big they are, whether they are stable, or which
ones actually matter. The FFT is a sixty-year-old algorithm that
answers all three questions in milliseconds. Hand it your messy series
and it hands back the list of cycles hiding inside, each with a size
attached, in your own units. That turns "Mondays feel busy" into a
measured cycle you can staff against, alert on, or subtract away to
see what is really changing underneath, which is the difference
between a hunch and a plan.

![The spectrum of a working week](pic/traffic_spectrum.png)

## 🧭 Why this repository exists

The first version of this went up in 2020: one quick notebook I wrote
after using the FFT to settle a seasonality question, two synthetic
sine waves and a CO2 series with a decomposition cross-check. People
kept finding it through search for years, which was flattering right
up until I reopened it in 2026 and tried to run it. The data file had
never been in the repository, so the interesting half died at the
first cell. Two of the library calls no longer exist, and a third is
on its way out. Worse, rereading my own explanations, I kept catching
the spots where I wrote for someone who already understood, which is
the one reader a tutorial does not need.

So this is the rewrite, done the way I wish someone had taught me.
Nothing gets used before it is built once from scratch in plain numpy,
small enough to check by hand. No number appears in the prose without
the code that produced it sitting right above, and the numbers that
matter get computed a second way, by a method the first one shares no
code with, before I let myself believe them. When a tool has a
weakness, a cell demonstrates the weakness instead of hoping you never
meet it. And everything runs offline from data bundled in the repo, so
what you read is exactly what you can run.

## 📚 The notebooks

**[01 · Fourier from scratch](notebooks/01_fourier_from_scratch.ipynb).**
What the transform actually does, built as a hand-made "probe scan"
before any library call, then verified against `rfft` to machine
precision. Amplitude, frequency, and phase; and the three practical
traps, each demonstrated rather than described: aliasing (a 20 Hz wave
sampled at 15 per second swears it is 5 Hz), spectral leakage and the
Hann window, and why noise mostly cannot hide a real cycle.

**[02 · Seasonality in the Keeling curve](notebooks/02_seasonality_in_the_keeling_curve.ipynb).**
Real data, and the raw FFT stumbles at once: the CO2 trend floods the
spectrum with leakage, which is the most common practical mistake in
this field (the 2020 version of this tutorial quietly dropped two
frequency bins to hide it). Detrend properly and the annual cycle
stands clear, after which four independent witnesses are made to agree:
the spectrum, brute-force monthly averaging, the autocorrelation
function, and STL decomposition, including a reconciliation of why the
nearest-bin FFT readout (2 ppm), the true fundamental (2.8 ppm), and
the calendar swing (6.3 ppm) are all telling the truth. A permutation
test turns the peak into a defensible claim, and a synthetic stress
test maps where each detector starts lying, including the ACF's
built-in weakness of confusing a period with its multiples.

**[03 · Demand rhythms and staffing](notebooks/03_demand_rhythms_and_staffing.ipynb).**
The business notebook, on hourly Interstate 94 traffic. The spectrum
names the rhythms (daily, weekly, harmonics that are rush hours in
disguise, sidebands that encode weekends), and then gets outranked on
held-out data: as a forecasting baseline, a 168-slot hour-of-week
lookup table beats truncated Fourier regression on 2018 data, 267
versus roughly 500 vehicles per hour of error, and the notebook
explains why that is the right lesson rather than an embarrassment.
The baseline then powers an anomaly alarm (1.9% of hours flagged, landing on the
holidays and the snowstorms, including a sub-freezing April weekend
that cut demand by 60%) and a capacity table showing what sizing to the
mean, the 80th, or the 95th percentile actually buys.

## 💼 Where this applies in the real world

The traffic sensor is a stand-in. The same three-step arc (diagnose the
rhythms, build a baseline, act on deviations) is the daily bread of
several jobs, and notebook 03 is deliberately written so you can replace
the CSV and keep the code.

- **Workforce and capacity planning.** Contact centers, field service,
  emergency departments, and warehouses all staff against an
  hour-of-week demand profile. Notebook 03's baseline comparison and
  its capacity table (what sizing to the mean, the 80th, or the 95th
  percentile actually buys) is that conversation with numbers attached.
- **Operations monitoring and alerting.** The per-slot z-score alarm is
  seasonally aware anomaly detection: it knows a quiet Monday 8am is an
  incident while a quiet Sunday 3am is just Sunday. The same pattern
  monitors network load, API request rates, payment volumes, and IoT
  telemetry, and the notebook shows it finding real holidays and real
  snowstorms with a 1.9% flag rate.
- **Forecasting features.** The detected periods become the calendar
  and Fourier features that downstream forecasting models feed on, and
  the climatology-versus-harmonics backtest is the honest way to decide
  whether a fancier model earns its complexity.
- **Sensor and telemetry forensics.** Aliasing, leakage, and the
  regular-grid requirement are the traps waiting inside any downsampled
  or gappy telemetry. Notebook 01 demonstrates each one on data where
  the truth is known, which is the cheapest place to learn them.
- **Trended seasonal series of any kind.** The Keeling-curve workflow
  in notebook 02 (detrend, transform, cross-check, significance-test)
  is the template for energy consumption, retail sales riding growth,
  temperature records, and any other series where a trend and a season
  share the data.

## 🚀 Running it yourself

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

Everything runs offline. The two datasets ship in `data/`:

- `co2_mm_mlo.csv`: monthly mean CO2 at Mauna Loa, 1958 to 2026, from
  NOAA's Global Monitoring Laboratory.
- `metro_traffic.csv`: hourly vehicle counts on I-94 (UCI Machine
  Learning Repository), January 2016 to September 2018, cleaned onto a
  strict hourly grid.

`python data/build_dataset.py` refreshes both from their public sources
and documents every cleaning decision (duplicate hours, the 2014-2015
sensor outage, the 4.2% of hours interpolated, a holiday flag that
needed spreading across its day).

## 🔁 What changed since 2020

The original single notebook is retired in favor of the sequence above.
Beyond the plumbing repairs (bundled data, current pandas, scipy, and
statsmodels APIs), the material that was missing is now present: proper
detrending instead of dropped bins, amplitude normalization that
survives a known-answer test, aliasing and leakage demonstrated, a
significance test, method comparisons with failure points, and an
application a business would recognize. The original's peak-to-months
translation table and its FFT-versus-decomposition cross-check survive,
upgraded, in notebook 02.

---

Written by [Satsawat Natakarnkitkul](https://satsawat.ai), a data and AI
practitioner in ASEAN. Companion series: [Markov chains and hidden
Markov models](https://github.com/netsatsawat/markov-and-hmm)
applies the same write-it-by-hand, verify-it-twice standard to a
different corner of applied mathematics. Newsletter:
[AI in Practice](https://satsawat.ai/#newsletter)

License: MIT
