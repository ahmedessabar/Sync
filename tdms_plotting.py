
# 4. Visualization / Consistency Check
import matplotlib.pyplot as plt

if 'derived_speed_mps' in locals() and derived_speed_mps is not None:
    plt.figure(figsize=(12, 10))
    
    # Subplot 1: Speed
    plt.subplot(2,1,1)
    
    # Xsens Speed
    # Try different potential column names
    speed_col = None
    for c in ['GPS_Speed', 'Velocity', 'Speed']:
        if c in df_txt.columns:
            speed_col = c
            break
            
    if speed_col:
        plt.plot(df_txt['AbsoluteTime'], df_txt[speed_col], label=f'Xsens {speed_col}')
    
    # TDMS Speed
    plt.plot(tdms_time, derived_speed_mps, label='TDMS Derived Speed', alpha=0.7)
    plt.title(f'Speed Comparison (Wheel={WHEEL_DIA_INCH}")')
    plt.legend()
    plt.grid(True)
    
    # Subplot 2: Acc
    plt.subplot(2,1,2)
    # Xsens Acc
    if 'Acc_X' in df_txt.columns:
        plt.plot(df_txt['AbsoluteTime'], df_txt['Acc_X'], label='Xsens Acc_X (Longitudinal)')
    
    # TDMS Acc
    plt.plot(tdms_time, derived_acc_mps2, label='TDMS Derived Acc', alpha=0.7)
    plt.title('Acceleration Comparison')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
else:
    print("No derived speed to plot.")
