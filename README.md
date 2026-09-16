# Autocorrelation-analysis
Autocorrelation analyis from Bahlouli et al.# Autocorrelation Analysis of Time-Series Intensity Traces

A small Python script for calculating normalized autocorrelation curves from multiple time-series intensity traces and estimating an oscillation period from the first qualifying non-zero autocorrelation peak.

The script was designed for intensity measurements collected over time, including fluorescence reporter traces, but it can be used with any evenly sampled one-dimensional time series.

## Input format

Input should be a CSV file in which the first column contains time values or frame numbers and each remaining column contains an independent intensity trace.

For example:

```csv
time,trace_1,trace_2,trace_3
0,1234,1188,1450
1,1201,1160,1442
2,1168,1125,1439
3,1140,1098,1447
```

The script assumes that measurements are evenly spaced in time.

If the first column contains actual time values, the program estimates the time step from the median difference between consecutive values. If the first column contains frame numbers, use `--time-step` to specify the time between frames in the units you want reported.

## What the script does

For each trace, the script:

1. Removes non-finite values.
2. Mean-centers the intensity trace.
3. Calculates the full discrete autocorrelation using `numpy.correlate`.
4. Retains zero and positive lags.
5. Normalizes the autocorrelation to the zero-lag value.
6. Searches for the first local maximum after a user-defined minimum lag.
7. Calls that maximum as the estimated period if its normalized autocorrelation is at least the specified threshold.

The estimated period is therefore the lag of the **first qualifying non-zero local autocorrelation maximum**. It should be interpreted in the context of the chosen minimum lag and peak-height threshold.

## Requirements

Python 3 and the following packages are required:

- NumPy
- pandas
- Matplotlib

Install them with:

```bash
pip install numpy pandas matplotlib
```

## Usage

Basic usage:

```bash
python autocorrelation_analysis.py data.csv
```

This writes output files using the default prefix `autocorrelation`.

To specify an output prefix:

```bash
python autocorrelation_analysis.py data.csv \
    --output-prefix results/flamindo
```

If your first column contains frame numbers rather than actual time values, specify the interval between frames:

```bash
python autocorrelation_analysis.py data.csv \
    --output-prefix results/flamindo \
    --time-step 1
```

For a trace collected once per minute, `--time-step 1` reports lag and estimated period in minutes. For a trace collected every 60 seconds, `--time-step 60` reports them in seconds.

A more complete example:

```bash
python autocorrelation_analysis.py data.csv \
    --output-prefix results/flamindo \
    --time-step 1 \
    --max-lag 60 \
    --min-peak-lag 5 \
    --min-peak-height 0.1
```

## Command-line options

`input_csv`  
CSV file containing time or frame number in the first column and one or more traces in the remaining columns.

`--output-prefix`  
Prefix used for all output files. Default: `autocorrelation`.

`--time-step`  
Time between consecutive measurements. If omitted, the script estimates it from the first column.

`--max-lag`  
Maximum lag included in plots, exported autocorrelation curves, and peak detection.

`--min-peak-lag`  
Minimum lag that can be considered when identifying the first non-zero autocorrelation peak. Default: `2.0`.

`--min-peak-height`  
Minimum normalized autocorrelation value required for a local maximum to be called as a peak. Default: `0.1`.

## Outputs

For each trace, the script generates:

```text
<prefix>_<trace_name>_autocorrelation.pdf
<prefix>_<trace_name>_autocorrelation.png
```

It also generates:

```text
<prefix>_autocorrelation_summary.csv
<prefix>_autocorrelation_curves.csv
```

The summary file contains:

- trace name
- estimated period
- autocorrelation value at the selected peak
- time step
- number of data points analyzed

If no local maximum satisfies the minimum-lag and minimum-height criteria, the estimated period and peak autocorrelation are reported as `NaN`.

## Example output summary

```text
trace,estimated_period,peak_autocorrelation,time_step,n_points
cell_1,6.0,0.51,1.0,240
cell_2,7.0,0.43,1.0,240
cell_3,6.0,0.48,1.0,240
```

## Notes and limitations

The analysis uses the standard discrete autocorrelation and does not correct for the decreasing number of overlapping observations at long lags. Period estimates are based on the first qualifying local maximum rather than on a fitted oscillatory model.

The approach works best for traces with reasonably regular oscillatory behavior and a sampling interval substantially shorter than the expected period. Peak calls should be inspected alongside the autocorrelation plots, particularly for noisy, weakly periodic, or short traces.

Missing or non-finite intensity values are removed independently from each trace before analysis. If missing measurements occur within a time series rather than only at its beginning or end, removal changes the effective temporal spacing of the remaining values. Such traces should be interpolated or otherwise handled appropriately before running this script.

## Repository contents

```text
autocorrelation_analysis.py
README.md
```



