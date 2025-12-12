
import sys
try:
    from nptdms import TdmsFile
except ImportError:
    print("npTDMS not installed")
    sys.exit(1)

file_path = r"c:\Users\es-sabar\Documents\PreTest\Moto_Chicane_50.tdms"

try:
    tdms_file = TdmsFile.read(file_path)
    print("Groups in TDMS file:")
    for group in tdms_file.groups():
        print(f" - {group.name}")
        if group.name == 'P1': # specifically check for P1 as requested
             print(f"   Channels in group {group.name}:")
             for channel in group.channels():
                 print(f"     - {channel.name}")
except Exception as e:
    print(f"Error reading TDMS file: {e}")
