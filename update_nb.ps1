$path = "c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb"
$txt = Get-Content -Raw -Path $path

# The target string exactly as it appears in the JSON (escaped for PS)
# Original: "file_path = 'Moto_chicane_100_P1.txt'\n",
$target = '"file_path = ''Moto_chicane_100_P1.txt''\n",'

# The replacement content (escaped for PS)
# We want to insert:
# "speed = 80\n",
# "passage = 'P1'\n",
# "file_path = f'Moto_Chicane_mouille_{speed}_{passage}.txt'\n",
# "print(f\"Analyzing file: {file_path}\")\n",

$replacement = '"speed = 80\n",
    "passage = ''P1''\n",
    "file_path = f''Moto_Chicane_mouille_{speed}_{passage}.txt''\n",
    "print(f\"Analyzing file: {file_path}\")\n",'

if ($txt.Contains($target)) {
    $txt = $txt.Replace($target, $replacement)
    Set-Content -Path $path -Value $txt -NoNewline
    Write-Host "Replaced successfully"
} else {
    Write-Host "Target string not found in file:"
    Write-Host $target
}
