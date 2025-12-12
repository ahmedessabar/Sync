$path = "c:\Users\es-sabar\Documents\PreTest\Sync\Xsens_Time_Analysis.ipynb"
$content = [System.IO.File]::ReadAllText($path)
$utf8NoBom = new-object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
Write-Host "Re-encoded file to UTF-8 without BOM."
