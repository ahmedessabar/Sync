
$path = "c:\Users\es-sabar\Documents\PreTest\Merge_Data.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json
foreach ($cell in $json.cells) {
    if ($cell.cell_type -eq 'code') {
        Write-Host "--- CODE CELL ---"
        $cell.source | ForEach-Object { Write-Host $_ -NoNewline }
        Write-Host "`n"
    }
}
