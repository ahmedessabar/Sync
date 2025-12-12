$nbPath = "c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb"
$content = Get-Content -Raw -Path $nbPath

# Replace txt path
$content = $content -replace "file_path = f'Moto_Chicane_mouille_\{speed\}_\{passage\}.txt'", "file_path = f'../Moto_Chicane_mouille_{speed}_{passage}.txt'"

# Replace TDMS pattern 1
$content = $content -replace "tdms_pattern = f'\*_\{speed\}\*_\{passage\}\*.tdms'", "tdms_pattern = f'../*_{speed}*_{passage}*.tdms'"

# Replace TDMS pattern 2 (fallback)
# Note: treating this as simple string replacement, might need to be careful with indentation in JSON
# The original line in JSON is: "    tdms_files = glob.glob(f'*_{speed}*.tdms')\n"
# We want to change the glob pattern.
$content = $content -replace "glob.glob\(f'\*_\{speed\}\*.tdms'\)", "glob.glob(f'../*_{speed}*.tdms')"

Set-Content -Path $nbPath -Value $content -Encoding UTF8
Write-Host "Notebook paths updated to use parent directory."
