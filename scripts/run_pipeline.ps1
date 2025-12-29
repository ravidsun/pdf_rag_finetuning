<#
.SYNOPSIS
    Convenience wrapper to run the PDF processing pipeline with the shared IO folders.

.DESCRIPTION
    Ensures the default input/output directories exist under
    C:\LLM\tools\pdf_rag_in_out and then invokes scripts/process_pdfs.py.
    Uses config/settings.yaml if present (unless overridden). You can override
    directories, batch size, or run a single PDF via parameters.

.EXAMPLE
    pwsh -File scripts/run_pipeline.ps1

.EXAMPLE
    pwsh -File scripts/run_pipeline.ps1 -SinglePdf C:\docs\paper.pdf -BatchSize 2
#>

param(
    [string]$PythonExe = "$PSScriptRoot\..\.\venv\Scripts\python.exe",
    [string]$InputDir = "C:\LLM\tools\pdf_rag_in_out\input",
    [string]$OutputDir = "C:\LLM\tools\pdf_rag_in_out\output",
    [int]$BatchSize,
    [string]$SinglePdf,
    [string]$Config
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$Candidate)
    if ($Candidate -and (Test-Path $Candidate)) {
        return (Resolve-Path $Candidate).Path
    }
    Write-Verbose "Specified python executable not found, falling back to system python."
    return "python"
}

function New-DirectoryIfMissing {
    param([string]$PathToEnsure)
    if (-not (Test-Path $PathToEnsure)) {
        New-Item -ItemType Directory -Path $PathToEnsure -Force | Out-Null
    }
}

New-DirectoryIfMissing -PathToEnsure $InputDir
New-DirectoryIfMissing -PathToEnsure $OutputDir

$pythonPath = Resolve-Python -Candidate $PythonExe
$repoRoot = Resolve-Path "$PSScriptRoot\.."
Push-Location $repoRoot

try {
    $arguments = @("scripts/process_pdfs.py", "--input-dir", $InputDir, "--output-dir", $OutputDir)

    if (-not $Config) {
        $defaultConfig = Join-Path $repoRoot "config\settings.yaml"
        if (Test-Path $defaultConfig) {
            $Config = $defaultConfig
        }
    }

    if ($BatchSize) {
        $arguments += @("--batch-size", $BatchSize)
    }

    if ($SinglePdf) {
        $arguments += @("--single-pdf", $SinglePdf)
    }

    if ($Config) {
        $arguments += @("--config", $Config)
    }

    Write-Host "Running pipeline with:"
    Write-Host "  Python   : $pythonPath"
    Write-Host "  InputDir : $InputDir"
    Write-Host "  OutputDir: $OutputDir"
    if ($BatchSize) { Write-Host "  BatchSize: $BatchSize" }
    if ($SinglePdf) { Write-Host "  SinglePdf: $SinglePdf" }
    if ($Config) { Write-Host "  Config   : $Config" }

    & $pythonPath @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Process exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
