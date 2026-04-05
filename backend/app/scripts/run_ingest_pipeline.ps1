param(
    [string]$StartDate = "2025-09-01",
    [int]$WeeksBack = 7,
    [switch]$ResetWeaviate,
    [switch]$DropFirst,
    [switch]$CleanOutputs,
    [switch]$KeepAwake,
    [string]$ManifestPath = "backend/validation/master_patent_manifest.csv",
    [string]$CheckpointPath = "backend/validation/ingest_completed_dates.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Push-Location $RepoRoot

function Enable-KeepAwake {
    Add-Type @"
using System.Runtime.InteropServices;
public static class SleepBlock {
  [DllImport("kernel32.dll")]
  public static extern uint SetThreadExecutionState(uint esFlags);
}
"@ | Out-Null

    $ES_CONTINUOUS = [Convert]::ToUInt32("80000000", 16)
    $ES_SYSTEM_REQUIRED = [Convert]::ToUInt32("00000001", 16)
    $ES_AWAYMODE_REQUIRED = [Convert]::ToUInt32("00000040", 16)
    $flags = [uint32]($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_AWAYMODE_REQUIRED)
    [SleepBlock]::SetThreadExecutionState($flags) | Out-Null
}

function Disable-KeepAwake {
    $ES_CONTINUOUS = [Convert]::ToUInt32("80000000", 16)
    try {
        [SleepBlock]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
    }
    catch {
    }
}

try {
    if ($CleanOutputs) {
        Remove-Item -Recurse -Force "backend\lmdb\colbert_128_f16.lmdb" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "backend\lmdb\colbert_128_f32.lmdb" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "backend\lmdb\patent_metadata.lmdb" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "backend\lmdb\claim_payloads.lmdb" -ErrorAction SilentlyContinue
        Remove-Item "backend\validation\master_patent_manifest.csv" -ErrorAction SilentlyContinue
        Remove-Item "backend\validation\ingest_completed_dates.txt" -ErrorAction SilentlyContinue
    }

    if ($ResetWeaviate) {
        Push-Location "backend\app"
        try {
            docker compose down -v
            docker compose up -d
        }
        finally {
            Pop-Location
        }
    }

    if ($KeepAwake) {
        Enable-KeepAwake
    }

    $env:INGEST_MODE = "real-store"
    $env:DROP_FIRST = $(if ($DropFirst) { "1" } else { "0" })
    $env:INGEST_DATES = ""
    $env:INGEST_START_DATE = $StartDate
    $env:INGEST_WEEKS_BACK = [string][Math]::Max(0, $WeeksBack)

    $env:TOKEN_VECTOR_DIM = "128"
    $env:TOKEN_VECTOR_DTYPE = "float16"
    $env:PROJECTION_MODE = "trained"
    # Must point to trained [128,768] (or [768,128]) projection checkpoint.
    if (-not $env:PROJECTION_PATH) {
        throw "PROJECTION_PATH must be set to trained projection weights before ingest."
    }
    $env:COLBERT_VARIANTS = "128_f16,128_f32"
    $env:LMDB_WRITE_VARIANTS = "128_f16"
    $env:LMDB_SHARDING_MODE = "none"
    $env:WRITE_LMDB = "1"

    $env:MASTER_MANIFEST_CSV = $ManifestPath
    $env:INGEST_CHECKPOINT_PATH = $CheckpointPath

    Write-Host "[run] Repo root: $RepoRoot"
    Write-Host "[run] StartDate=$StartDate WeeksBack=$WeeksBack DropFirst=$($env:DROP_FIRST)"
    Write-Host "[run] Manifest=$ManifestPath"
    Write-Host "[run] Checkpoint=$CheckpointPath"

    poetry run python backend/app/test_connection.py
}
finally {
    if ($KeepAwake) {
        Disable-KeepAwake
    }
    Pop-Location
}
