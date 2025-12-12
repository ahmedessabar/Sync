
$path = "c:\Users\es-sabar\Documents\PreTest\Merge_Data.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json
$found = $false
foreach ($cell in $json.cells) {
    if ($cell.cell_type -eq 'code') {
        $src = $cell.source -join ""
        if ($src -like "*Edges_RoueAR*") {
            Write-Host "--- TARGET CODE FOUND ---"
            $cell.source | ForEach-Object { Write-Host $_ -NoNewline }
            Write-Host "`n--- END CODE ---"
            $found = $true
            break
        }
    }
}
if (-not $found) { Write-Host "Code not found." }
