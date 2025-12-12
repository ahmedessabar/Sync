import codecs

file_path = r'c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb'

try:
    # Read the file with utf-8-sig to handle BOM
    with codecs.open(file_path, 'r', 'utf-8-sig') as f:
        content = f.read()
    
    # Write it back as standard utf-8 without BOM
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(content)
        
    print("Successfully removed BOM and saved as UTF-8.")

except Exception as e:
    print(f"Error fixing encoding: {e}")
