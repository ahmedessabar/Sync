
$path = "c:\Users\es-sabar\Documents\PreTest\Merge_Data.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json
$found = $false

foreach ($cell in $json.cells) {
    if ($cell.cell_type -eq 'code') {
        $source_lines = $cell.source
        $src_text = $source_lines -join ""
        
        # Look for the calculation logic cell, often contains 'Edges_RoueAR' or 'diff'
        if ($src_text -like "*Edges_RoueAR*" -or $src_text -like "*deriv*") {
            Write-Host "--- RELEVANT CODE CELL ---"
            if ($source_lines -is [string]) {
                 Write-Host $source_lines
            } else {
                 $source_lines | ForEach-Object { Write-Host $_ -NoNewline }
            }
            Write-Host "`n--- END CELL ---`n"
        }
    }
}
