import json
import os

notebook_path = r'c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb'
output_path = r'c:\Users\es-sabar\Documents\PreTest\code_dump.txt'

try:
    if not os.path.exists(notebook_path):
        with open(output_path, 'w') as f:
            f.write(f"Error: File not found at {notebook_path}")
        exit(1)

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Notebook Loaded successfully.\n")
        
        for i, cell in enumerate(nb['cells']):
            if cell['cell_type'] == 'code':
                f.write(f"\n--- Cell {i} Source ---\n")
                source_lines = cell.get('source', [])
                if isinstance(source_lines, str):
                    f.write(source_lines + "\n")
                else:
                    f.write(''.join(source_lines) + "\n")
    print("Done writing to file.")

except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"Error reading notebook: {e}")
    print(f"Error: {e}")
