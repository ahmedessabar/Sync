$path = "c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb"
$content = Get-Content -Raw -Path $path
$content = $content -replace "df_txt", "df"
Set-Content -Path $path -Value $content -Encoding UTF8
Write-Host "Replaced all 'df_txt' with 'df'."
