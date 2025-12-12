
$path = "c:\Users\es-sabar\Documents\PreTest\Xsens_Time_Analysis.ipynb"
$json = Get-Content -Raw -Path $path | ConvertFrom-Json

$deriv_src = Get-Content -Raw -Path "c:\Users\es-sabar\Documents\PreTest\tdms_derivation.py"
$plot_src = Get-Content -Raw -Path "c:\Users\es-sabar\Documents\PreTest\tdms_plotting.py"

# Function to create cell
function New-Cell {
    param($src_content)
    # Split into lines for JSON array format, though single string often works too
    # But notebook usually prefers array of strings with \n
    $lines = $src_content -split "`r`n"
    for ($i=0; $i -lt $lines.Length; $i++) {
        $lines[$i] = $lines[$i] + "`n"
    }
    
    return [PSCustomObject]@{
        cell_type = "code"
        execution_count = $null
        metadata = @{}
        outputs = @()
        source = $lines
    }
}

$json.cells += (New-Cell -src_content $deriv_src)
$json.cells += (New-Cell -src_content $plot_src)

$json | ConvertTo-Json -Depth 100 | Set-Content -Path $path
Write-Host "Success: Injected derivation and plotting cells."
