param(
    [string]$Compiler = "g++",
    [switch]$StaticRuntime
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $root "cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.cpp"
$output = Join-Path $root "cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe"

$arguments = @(
    "-std=c++17",
    "-O2",
    "-pthread"
)
if ($StaticRuntime) {
    $arguments += "-static-libgcc"
    $arguments += "-static-libstdc++"
}
$arguments += $source
$arguments += "-o"
$arguments += $output

Write-Host "Compiler: $Compiler"
Write-Host "Source:   $source"
Write-Host "Output:   $output"
& $Compiler @arguments
if ($LASTEXITCODE -ne 0) {
    throw "C++ compilation failed with exit code $LASTEXITCODE."
}

Write-Host "Build completed."
