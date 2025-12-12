
$path = "c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json

# Helper to create cell
function New-CodeCell {
    param($lines)
    return [PSCustomObject]@{
        cell_type = "code"
        execution_count = $null
        metadata = @{}
        outputs = @()
        source = $lines
    }
}

$cell_time_src = @(
    "# 2. Construct TDMS Time Axis`n",
    "import pandas as pd`n",
    "import numpy as np`n",
    "from scipy import signal`n",
    "`n",
    "tdms_time = None`n",
    "if 'edges_data' in locals() and 'edges_ch' in locals():`n",
    "    try:`n",
    "        props = edges_ch.properties`n",
    "        start_time = props.get('wf_start_time')`n",
    "        increment = props.get('wf_increment')`n",
    "        `n",
    "        if start_time is not None and increment is not None:`n",
    "            # Construct time array`n",
    "            # handle datetime format`n",
    "            start_dt = pd.to_datetime(start_time).tz_localize(None)`n",
    "            # Create array of seconds offsets`n",
    "            n_samples = len(edges_data)`n",
    "            seconds = np.arange(n_samples) * increment`n",
    "            tdms_time = start_dt + pd.to_timedelta(seconds, unit='s')`n",
    "            print(f'TDMS Time constructed: {len(tdms_time)} samples, {1/increment:.1f} Hz')`n",
    "        else:`n",
    "            print('Warning: wf_start_time or wf_increment missing in TDMS properties')`n",
    "    except Exception as e:`n",
    "        print(f'Error constructing time: {e}')`n"
)

$cell_derive_src = @(
    "# 3. Derive Speed/Acceleration (Edge-Step Method)`n",
    "# LOGIC FROM Merge_Data.ipynb (Adapted)`n",
    "`n",
    "derived_speed_mps = None`n",
    "derived_acc_mps2 = None`n",
    "`n",
    "if tdms_time is not None and 'edges_data' in locals():`n",
    "    try:`n",
    "        # Parameters`n",
    "        WHEEL_DIA_INCH = 17.0 # User preference`n",
    "        EDGES_PER_REV = 50.0`n",
    "        STEP_EDGES = 150`n",
    "        `n",
    "        wheel_circum_m = WHEEL_DIA_INCH * 0.0254 * np.pi`n",
    "        meters_per_edge = wheel_circum_m / EDGES_PER_REV`n",
    "        `n",
    "        # Create DataFrame for derivation logic`n",
    "        df_t = pd.DataFrame({'Edges': edges_data, 'Time': tdms_time})`n",
    "        df_t['Time_ns'] = df_t['Time'].astype(np.int64)`n",
    "        `n",
    "        # 1. Unique edges for interpolation`n",
    "        df_unique = df_t.drop_duplicates(subset=['Edges'], keep='first')`n",
    "        `n",
    "        if len(df_unique) > 100:`n",
    "            u_counts = df_unique['Edges'].values`n",
    "            u_times_ns = df_unique['Time_ns'].values`n",
    "            `n",
    "            # 2. Grid of edges`n",
    "            min_edge = u_counts.min()`n",
    "            max_edge = u_counts.max()`n",
    "            edge_grid = np.arange(np.ceil(min_edge/STEP_EDGES)*STEP_EDGES, max_edge, STEP_EDGES)`n",
    "            `n",
    "            # 3. Interpolate Time at grid`n",
    "            t_grid_ns = np.interp(edge_grid, u_counts, u_times_ns)`n",
    "            `n",
    "            # 4. Calc Speed (Step / dTime)`n",
    "            dt_grid_s = np.diff(t_grid_ns) * 1e-9`n",
    "            speed_grid_edges_s = STEP_EDGES / dt_grid_s`n",
    "            speed_grid_mps = speed_grid_edges_s * meters_per_edge`n",
    "            `n",
    "            # Map back to full time`n",
    "            t_mid_ns = (t_grid_ns[:-1] + t_grid_ns[1:]) / 2`n",
    "            # Interpolate onto original time`n",
    "            full_time_ns = df_t['Time_ns'].values`n",
    "            derived_speed_mps = np.interp(full_time_ns, t_mid_ns, speed_grid_mps, left=0, right=0)`n",
    "            `n",
    "            # Calc Accel (diff of speed)`n",
    "            # fs is approx`n",
    "            fs = 1.0 / increment`n",
    "            # Simple diff for now or gradient`n",
    "            # derived_acc = np.gradient(derived_speed_mps, increment)`n",
    "            # Using diff + filter as per source`n",
    "            acc_raw = np.diff(derived_speed_mps, prepend=derived_speed_mps[0]) * fs`n",
    "            `n",
    "            # Low pass filter`n",
    "            b, a = signal.butter(2, 5, fs=fs, btype='low')`n",
    "            derived_acc_mps2 = signal.filtfilt(b, a, acc_raw)`n",
    "            `n",
    "            print('Derivation Complete.')`n",
    "        else:`n",
    "            print('Not enough unique edges for derivation')`n",
    "    except Exception as e:`n",
    "        print(f'Derivation Error: {e}')`n"
)

$cell_plot_src = @(
    "# 4. Visualization / Consistency Check`n",
    "import matplotlib.pyplot as plt`n",
    "`n",
    "if derived_speed_mps is not None:`n",
    "    plt.figure(figsize=(12, 10))`n",
    "    `n",
    "    # Subplot 1: Speed`n",
    "    plt.subplot(2,1,1)`n",
    "    # Attempt to plot Xsens speed if available`n",
    "    # Check dataframe columns for 'GPS_Speed' or similar`n",
    "    cols = [c for c in df_txt.columns if 'Speed' in c or 'Velocity' in c]`n",
    "    if cols:`n",
    "        # Assume GPS_Speed or Velocity is m/s? or km/h? `n",
    "        # usually Xsens is m/s. `n",
    "        plt.plot(df_txt['AbsoluteTime'], df_txt[cols[0]], label=f'Xsens {cols[0]}')`n",
    "    `n",
    "    plt.plot(tdms_time, derived_speed_mps, label='TDMS Derived Speed', alpha=0.7)`n",
    "    plt.title(f'Speed Comparison (Wheel={WHEEL_DIA_INCH}\\\")')`n",
    "    plt.legend()`n",
    "    plt.grid(True)`n",
    "    `n",
    "    # Subplot 2: Acc`n",
    "    plt.subplot(2,1,2)`n",
    "    # Xsens Acc_X (Longitudinal)`n",
    "    if 'Acc_X' in df_txt.columns:`n",
    "        plt.plot(df_txt['AbsoluteTime'], df_txt['Acc_X'], label='Xsens Acc_X')`n",
    "    `n",
    "    plt.plot(tdms_time, derived_acc_mps2, label='TDMS Derived Acc', alpha=0.7)`n",
    "    plt.title('Acceleration Comparison')`n",
    "    plt.legend()`n",
    "    plt.grid(True)`n",
    "    `n",
    "    plt.tight_layout()`n",
    "    plt.show()`n"
)

# Append cells at the end of the notebook or after previous insertion?
# Let's append to the end for simplicity, or find the previous cell.
# The user wants this "To verify consistency".
# We previously inserted 3 cells. Let's append these 3 new ones.

$json.cells += (New-CodeCell -lines $cell_time_src)
$json.cells += (New-CodeCell -lines $cell_derive_src)
$json.cells += (New-CodeCell -lines $cell_plot_src)

$json | ConvertTo-Json -Depth 100 | Set-Content -Path $path
Write-Host "Injected derivation logic."
