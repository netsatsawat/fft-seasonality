# FFT and the art of finding seasonality

A three-notebook tutorial on finding repeating patterns in time series
data, written for someone with basic Python and no signal processing
background. It starts by building the Fourier transform by hand in four
lines of numpy, proves the toolkit on sixty-eight years of atmospheric
CO2, and ends where an operations team would spend the results: a demand
baseline, an anomaly alarm, and a capacity table for thirty-three months
of real hourly traffic.

![The spectrum of a working week](pic/traffic_spectrum.png)

## Why this repository exists

I published the first version in 2020 as a single quick notebook: two
synthetic sine waves, one FFT of a CO2 emissions series, one
cross-check against a seasonal decomposition. People kept landing on
it, and it aged the way quick notebooks do. The data file lived outside
the repository, so the real-data half could not run at all; two of the
library calls it used have since been removed from scipy and
statsmodels, with a third deprecated in pandas; and the explanations
skipped the ideas that actually
trip people up, like why a trend floods a spectrum or why an amplitude
needs a 2/N in front of it.

This rewrite keeps what was good about the original, especially its
habit of translating frequencies into human units and cross-checking
the FFT against an independent decomposition, and rebuilds everything
else around three rules: build each idea from something small enough to
check by hand, get every important number twice by methods that cannot
share a bug, and say what each tool assumes and where it breaks. The
notebooks run offline, top to bottom, from data that ships in the repo.

## The notebooks

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

## Running it yourself

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

## What changed since 2020

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
Markov models](https://github.com/netsatsawat/markov_and_hidden_markov_model)
applies the same write-it-by-hand, verify-it-twice standard to a
different corner of applied mathematics. Newsletter:
[AI in Practice](https://satsawat.ai/#newsletter)

License: MIT
