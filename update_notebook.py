import json

notebook_path = r'c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb'

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Locate the cell with the file_path definition
    target_cell_index = None
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = cell.get('source', [])
            # Search for the specific line we want to replace
            for line in source:
                if "file_path = 'Moto_chicane_100_P1.txt'" in line:
                    target_cell_index = i
                    break
        if target_cell_index is not None:
            break
            
    if target_cell_index is not None:
        print(f"Found target code at cell {target_cell_index}")
        cell = nb['cells'][target_cell_index]
        new_source = []
        
        # Construct new source with parameterized variables
        # We replace the hardcoded line and prepend the new variables
        found = False
        for line in cell['source']:
            if "file_path = 'Moto_chicane_100_P1.txt'" in line:
                new_source.append("speed = 80\n")
                new_source.append("passage = 'P1'\n")
                new_source.append("file_path = f'Moto_Chicane_mouille_{speed}_{passage}.txt'\n")
                new_source.append("print(f\"Analyzing file: {file_path}\")\n")
                found = True
            else:
                new_source.append(line)
        
        if found:
            cell['source'] = new_source
            
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(nb, f, indent=1) # Keeping indentation minimal to avoid huge diffs if possible, or just default
            print("Notebook updated successfully.")
        else:
             print("Target line not found in the cell source list during processing.")

    else:
        print("Target cell not found.")

except Exception as e:
    print(f"Error updating notebook: {e}")
