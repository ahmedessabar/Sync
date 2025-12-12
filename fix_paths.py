import json
import os

nb_path = r'c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb'

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    changes_made = 0

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            new_source = []
            for line in cell['source']:
                # Update .txt file path
                if "file_path = f'Moto_Chicane_mouille_{speed}_{passage}.txt'" in line:
                    new_line = "file_path = f'../Moto_Chicane_mouille_{speed}_{passage}.txt'\n"
                    new_source.append(new_line)
                    changes_made += 1
                    print(f"Fixed txt path definition: {line.strip()} -> {new_line.strip()}")
                
                # Update TDMS primary pattern
                elif "tdms_pattern = f'*_{speed}*_{passage}*.tdms'" in line:
                    new_line = "tdms_pattern = f'../*_{speed}*_{passage}*.tdms'\n"
                    new_source.append(new_line)
                    changes_made += 1
                    print(f"Fixed TDMS pattern 1: {line.strip()} -> {new_line.strip()}")

                # Update TDMS fallback pattern
                elif "tdms_files = glob.glob(f'*_{speed}*.tdms')" in line:
                    new_line = "    tdms_files = glob.glob(f'../*_{speed}*.tdms')\n"
                    new_source.append(new_line)
                    changes_made += 1
                    print(f"Fixed TDMS pattern 2: {line.strip()} -> {new_line.strip()}")
                
                else:
                    new_source.append(line)
            
            cell['source'] = new_source

    if changes_made > 0:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Successfully updated {changes_made} paths in notebook.")
    else:
        print("No changes needed or patterns not found.")

except Exception as e:
    print(f"Error: {e}")
