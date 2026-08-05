"""Rebuild the two bundled datasets from their public sources.

The notebooks read the tidy CSVs shipped in this folder, so they run
offline and reproduce exactly. Run this script only if you want fresher
snapshots.

Sources, both fully open:

1. co2_mm_mlo.csv
   Monthly mean atmospheric CO2 at Mauna Loa Observatory (the Keeling
   curve), from NOAA Global Monitoring Laboratory:
   https://gml.noaa.gov/ccgg/trends/data.html
   Direct file: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv

2. metro_traffic.csv
   Metro Interstate Traffic Volume (hourly vehicle counts on I-94
   westbound between Minneapolis and St Paul), UCI Machine Learning
   Repository, dataset 492:
   https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume

The raw UCI file needs real cleaning, all of it done here and reported
as it happens: duplicate timestamps (weather providers file several rows
for one hour), a long outage from mid-2014 to mid-2015, scattered
missing hours, and a holiday flag that is only stamped on the midnight
row of each holiday. We keep the span from January 2016 onward, where
no gap exceeds nine hours, put it on a strict hourly grid, interpolate
the small gaps, and spread the holiday flag across its whole day.
"""

import io
import gzip
import pathlib
import urllib.request

import numpy as np
import pandas as pd

CO2_URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv"
METRO_URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
             "00492/Metro_Interstate_Traffic_Volume.csv.gz")
OUT = pathlib.Path(__file__).resolve().parent


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def build_co2():
    raw = fetch(CO2_URL).decode()
    df = pd.read_csv(io.StringIO(raw), comment="#")
    df = df.rename(columns=str.strip)
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    out = df[["date", "average"]].rename(columns={"average": "co2"})
    out = out[out["co2"] > 0]                     # -99.99 marks missing
    out.to_csv(OUT / "co2_mm_mlo.csv", index=False)
    print(f"co2_mm_mlo.csv: {len(out)} monthly rows, "
          f"{out['date'].min():%Y-%m} to {out['date'].max():%Y-%m}")


def build_metro():
    raw = gzip.decompress(fetch(METRO_URL))
    # keep_default_na=False: the holiday column uses the literal string
    # "None", which pandas would otherwise silently turn into NaN.
    df = pd.read_csv(io.BytesIO(raw), parse_dates=["date_time"],
                     keep_default_na=False)
    df["temp"] = pd.to_numeric(df["temp"], errors="coerce")
    df["traffic_volume"] = pd.to_numeric(df["traffic_volume"], errors="coerce")

    n_raw = len(df)
    # The holiday name is stamped only on the 00:00 row of its day.
    holiday_days = set(
        df.loc[df["holiday"] != "None", "date_time"].dt.date.unique())

    # Several rows can share one timestamp (one per weather record).
    df = (df.groupby("date_time")
            .agg(traffic_volume=("traffic_volume", "mean"),
                 temp_k=("temp", "mean"))
            .sort_index())
    print(f"raw rows {n_raw}, unique hours {len(df)}")

    # Keep the span where the record is nearly continuous: from 2016 on,
    # no gap is longer than nine hours. (Mid-2014 to mid-2015 is a
    # months-long outage, and late 2015 still has a multi-day hole.)
    df = df.loc["2016-01-01":]

    # Strict hourly grid; count and fill what is missing.
    full = pd.date_range(df.index.min(), df.index.max(), freq="h")
    missing = full.difference(df.index)
    df = df.reindex(full)
    df["traffic_volume"] = df["traffic_volume"].interpolate(limit_direction="both")
    df["is_holiday"] = pd.Index(df.index.date).isin(holiday_days)
    print(f"grid {len(full)} hours, interpolated {len(missing)} missing "
          f"({len(missing) / len(full):.2%})")

    # Temperature is in Kelvin with a few impossible zeros; make Celsius.
    df["temp_c"] = df["temp_k"] - 273.15
    df.loc[df["temp_c"] < -50, "temp_c"] = np.nan
    df["temp_c"] = df["temp_c"].interpolate(limit_direction="both").round(1)

    out = df.reset_index().rename(columns={"index": "date_time"})
    out["traffic_volume"] = out["traffic_volume"].round(1)
    out[["date_time", "traffic_volume", "is_holiday", "temp_c"]].to_csv(
        OUT / "metro_traffic.csv", index=False)
    print(f"metro_traffic.csv: {len(out)} hourly rows, "
          f"{out['date_time'].min():%Y-%m-%d} to {out['date_time'].max():%Y-%m-%d}")


if __name__ == "__main__":
    build_co2()
    build_metro()
