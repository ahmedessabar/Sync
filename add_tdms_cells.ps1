
$path = "c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json

# Define new cells content
$cell1_source = @(
    "import sys`n",
    "!{sys.executable} -m pip install nptdms`n",
    "from nptdms import TdmsFile`n",
    "import glob`n",
    "import os`n",
    "import numpy as np`n"
)

$cell2_source = @(
    "# 1.b Load Matching TDMS Data`n",
    "tdms_pattern = f'*_{speed}*_{passage}*.tdms'`n",
    "print(f'Looking for TDMS file with pattern: {tdms_pattern}')`n",
    "tdms_files = glob.glob(tdms_pattern)`n",
    "`n",
    "tdms_path = None`n",
    "if tdms_files:`n",
    "    tdms_path = tdms_files[0]`n",
    "    print(f'Found TDMS file: {tdms_path}')`n",
    "else:`n",
    "    print('No matching TDMS file found. using fallback search...')`n",
    "    # Fallback: try just speed`n",
    "    tdms_files = glob.glob(f'*_{speed}*.tdms')`n",
    "    if tdms_files:`n",
    "        tdms_path = tdms_files[0]`n",
    "        print(f'Found TDMS file (fallback): {tdms_path}')`n"
)

$cell3_source = @(
    "# 1.c Process TDMS Edges`n",
    "tdms_acc = None`n",
    "tdms_time = None`n",
    "if tdms_path:`n",
    "    try:`n",
    "        tdms_file = TdmsFile(tdms_path)`n",
    "        group = tdms_file.groups()[0]`n",
    "        if 'Edges_RoueAR' in group:`n",
    "            edges_ch = group['Edges_RoueAR']`n",
    "            edges_data = edges_ch[:]`n",
    "            print(f'Loaded {len(edges_data)} edges from TDMS.')`n",
    "            # Basic Time construction for TDMS`n",
    "            # Assuming constant sample rate properties usually available in waveform`n",
    "            # For now, we will perform synchronization and more complex derivation later.`n",
    "            # Just proving we can read it.`n",
    "            print('TDMS properties:', edges_ch.properties)`n",
    "        else:`n",
    "            print('Edges_RoueAR channel not found in TDMS group.')`n",
    "    except Exception as e:`n",
    "        print(f'Error reading TDMS: {e}')`n"
)

# Helper to create cell object
function New-Cell {
    param($src)
    return [PSCustomObject]@{
        cell_type = "code"
        execution_count = $null
        metadata = @{}
        outputs = @()
        source = $src
    }
}

$new_cells = @()
$inserted = $false

foreach ($cell in $json.cells) {
    $new_cells += $cell
    
    # Check if this lies the "speed = 80" cell
    if ($cell.cell_type -eq 'code' -and -not $inserted) {
        $src_str = $cell.source -join ""
        if ($src_str -like "*speed = 80*") {
            Write-Host "Found insertion point."
            $new_cells += (New-Cell -src $cell1_source)
            $new_cells += (New-Cell -src $cell2_source)
            $new_cells += (New-Cell -src $cell3_source)
            $inserted = $true
        }
    }
}

if ($inserted) {
    $json.cells = $new_cells
    $json | ConvertTo-Json -Depth 100 | Set-Content -Path $path
    Write-Host "Notebook updated with new cells."
} else {
    Write-Host "Insertion point not found."
}
