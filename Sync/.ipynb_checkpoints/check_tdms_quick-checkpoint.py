
try:
    from nptdms import TdmsFile
    print("nptdms is available")
    f = TdmsFile.read(r"c:\Users\es-sabar\Documents\PreTest\Moto_Chicane_50.tdms")
    for group in f.groups():
        print(f"Group: {group.name}")
        for channel in group.channels():
             print(f"  Channel: {channel.name}")
             if len(group.channels()) > 5 and channel.name == group.channels()[4].name:
                 print("  ... (truncated)")
                 break
except ImportError:
    print("nptdms is MISSING")
except Exception as e:
    print(f"Error: {e}")
