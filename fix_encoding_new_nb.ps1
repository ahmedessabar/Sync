$path = "c:\Users\es-sabar\Documents\PreTest\Sync\Duration_Analysis.ipynb"
$content = Get-Content -Raw -Path $path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
Write-Host "Re-encoded file to UTF-8 without BOM."
