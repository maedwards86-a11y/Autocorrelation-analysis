#!/usr/bin/env python3
"""
autocorrelation_analysis.py

Generic autocorrelation analysis for time-series intensity traces.

Input CSV format:

time,trace_1,trace_2,trace_3
0,1234,1188,1450
1,1201,1160,1442
2,1168,1125,1439
...

The first column should contain time values or frame numbers.
Each remaining column is treated as an independent time-series trace.

Outputs:
1. One autocorrelation plot per trace as PDF and PNG
2. A summary CSV containing the estimated first non-zero autocorrelation peak
3. A CSV containing the autocorrelation curves for all traces
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_autocorrelation(trace):
    """
    Calculate the normalized autocorrelation of a one-dimensional time series.

    The trace is mean-centered, full discrete autocorrelation is calculated,
    zero and positive lags are retained, and the autocorrelation is normalized
    to the zero-lag value.

    Parameters
    ----------
    trace : array-like
        One-dimensional time-series data.

    Returns
    -------
    ac : numpy.ndarray
        Normalized autocorrelation values for zero and positive lags.
    """
    trace = np.asarray(trace, dtype=float)
    trace = trace[np.isfinite(trace)]

    if len(trace) < 3:
        raise ValueError("Trace is too short for autocorrelation analysis.")

    centered = trace - np.mean(trace)
    ac_full = np.correlate(centered, centered, mode="full")

    # Retain zero and positive lags only.
    ac = ac_full[ac_full.size // 2:]

    # Normalize to zero-lag autocorrelation.
    if ac[0] == 0:
        return np.full_like(ac, np.nan)

    return ac / ac[0]


def find_first_nonzero_peak(ac, lag_values, min_lag=2.0, min_height=0.1):
    """
    Identify the first local autocorrelation peak after a minimum lag.

    This avoids counting the zero-lag peak and helps exclude short-lag noise.

    Parameters
    ----------
    ac : array-like
        Normalized autocorrelation values.
    lag_values : array-like
        Lag values in time units.
    min_lag : float
        Minimum lag to consider when searching for a peak.
    min_height : float
        Minimum normalized autocorrelation value required for peak calling.

    Returns
    -------
    peak_lag : float
        Lag value of the first qualifying peak.
    peak_value : float
        Autocorrelation value at the first qualifying peak.

    If no qualifying peak is found, returns np.nan, np.nan.
    """
    for i in range(1, len(ac) - 1):
        if lag_values[i] < min_lag:
            continue

        is_local_maximum = ac[i] > ac[i - 1] and ac[i] > ac[i + 1]
        is_above_threshold = ac[i] >= min_height

        if is_local_maximum and is_above_threshold:
            return lag_values[i], ac[i]

    return np.nan, np.nan


def analyze_csv(
    input_csv,
    output_prefix,
    time_step=None,
    max_lag=None,
    min_peak_lag=2.0,
    min_peak_height=0.1,
):
    """
    Analyze all traces in a CSV file and export autocorrelation outputs.
    """
    data = pd.read_csv(input_csv)

    if data.shape[1] < 2:
        raise ValueError(
            "Input CSV must contain a time column and at least one trace column."
        )

    time_column = data.columns[0]
    time_values = data[time_column].to_numpy(dtype=float)

    if time_step is None:
        dt = np.nanmedian(np.diff(time_values))
    else:
        dt = float(time_step)

    if not np.isfinite(dt) or dt <= 0:
        raise ValueError(
            "Could not determine a valid positive time step from the first "
            "column. Supply one explicitly with --time-step."
        )

    summary_rows = []
    autocorrelation_tables = {}

    for trace_name in data.columns[1:]:
        trace = data[trace_name].to_numpy(dtype=float)
        trace = trace[np.isfinite(trace)]

        ac = compute_autocorrelation(trace)
        lags = np.arange(len(ac)) * dt

        if max_lag is not None:
            keep = lags <= max_lag
            lags_to_plot = lags[keep]
            ac_to_plot = ac[keep]
        else:
            lags_to_plot = lags
            ac_to_plot = ac

        peak_lag, peak_value = find_first_nonzero_peak(
            ac_to_plot,
            lags_to_plot,
            min_lag=min_peak_lag,
            min_height=min_peak_height,
        )

        summary_rows.append(
            {
                "trace": trace_name,
                "estimated_period": peak_lag,
                "peak_autocorrelation": peak_value,
                "time_step": dt,
                "n_points": len(trace),
            }
        )

        autocorrelation_tables[f"{trace_name}_lag"] = lags_to_plot
        autocorrelation_tables[f"{trace_name}_autocorrelation"] = ac_to_plot

        plt.figure(figsize=(5, 4))
        plt.plot(lags_to_plot, ac_to_plot)
        plt.axhline(0, linewidth=0.8)

        if np.isfinite(peak_lag):
            plt.plot(peak_lag, peak_value, marker="o")
            plt.text(
                peak_lag,
                peak_value,
                f"  {peak_lag:.2f}",
                va="bottom",
            )

        plt.xlabel("Lag")
        plt.ylabel("Normalized autocorrelation")
        plt.title(str(trace_name))
        plt.tight_layout()

        safe_trace_name = (
            str(trace_name)
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

        plt.savefig(
            f"{output_prefix}_{safe_trace_name}_autocorrelation.pdf"
        )
        plt.savefig(
            f"{output_prefix}_{safe_trace_name}_autocorrelation.png",
            dpi=300,
        )
        plt.close()

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(
        f"{output_prefix}_autocorrelation_summary.csv",
        index=False,
    )

    autocorrelation_df = pd.DataFrame(
        {
            key: pd.Series(value)
            for key, value in autocorrelation_tables.items()
        }
    )

    autocorrelation_df.to_csv(
        f"{output_prefix}_autocorrelation_curves.csv",
        index=False,
    )

    return summary


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Calculate normalized autocorrelation curves from "
            "time-series traces."
        )
    )

    parser.add_argument(
        "input_csv",
        help=(
            "CSV file with time or frame number in the first column "
            "and traces in the remaining columns."
        ),
    )

    parser.add_argument(
        "--output-prefix",
        default="autocorrelation",
        help="Prefix for output files.",
    )

    parser.add_argument(
        "--time-step",
        type=float,
        default=None,
        help=(
            "Time between frames. If omitted, the script estimates "
            "this from the first column."
        ),
    )

    parser.add_argument(
        "--max-lag",
        type=float,
        default=None,
        help="Maximum lag to include in plots and output tables.",
    )

    parser.add_argument(
        "--min-peak-lag",
        type=float,
        default=2.0,
        help=(
            "Minimum lag to consider when identifying the first "
            "non-zero peak."
        ),
    )

    parser.add_argument(
        "--min-peak-height",
        type=float,
        default=0.1,
        help=(
            "Minimum normalized autocorrelation value required "
            "for peak calling."
        ),
    )

    args = parser.parse_args()

    output_dir = os.path.dirname(args.output_prefix)

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    summary = analyze_csv(
        input_csv=args.input_csv,
        output_prefix=args.output_prefix,
        time_step=args.time_step,
        max_lag=args.max_lag,
        min_peak_lag=args.min_peak_lag,
        min_peak_height=args.min_peak_height,
    )

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
