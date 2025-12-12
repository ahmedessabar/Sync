import json

nb_path = r'c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb'

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    changes = 0
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            new_source = []
            for line in cell['source']:
                if 'df_txt' in line:
                    new_line = line.replace('df_txt', 'df')
                    new_source.append(new_line)
                    changes += 1
                else:
                    new_source.append(line)
            cell['source'] = new_source

    if changes > 0:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Fixed {changes} instances of 'df_txt' to 'df'.")
    else:
        print("No instances of 'df_txt' found.")

except Exception as e:
    print(f"Error: {e}")
