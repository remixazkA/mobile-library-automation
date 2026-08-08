[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $ProjectRoot,

    [Parameter(Mandatory)]
    [string] $DeviceName,

    [string] $StorageName = 'Internal storage',

    [string[]] $SourceRoots = @('DCIM', 'Pictures', 'Download', 'Movies'),

    [switch] $Commit
)

$ErrorActionPreference = 'Stop'
$destinationRoot = Join-Path $ProjectRoot 'staging'
$statusPath = Join-Path $ProjectRoot 'run\mtp-copy-status.json'

function Write-Status {
    param([string] $State, [string] $Detail)
    $parent = Split-Path -Parent $statusPath
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $payload = [ordered]@{
        state = $State
        detail = $Detail
        updated = (Get-Date).ToString('o')
    }
    [IO.File]::WriteAllText(
        $statusPath,
        ($payload | ConvertTo-Json),
        [Text.UTF8Encoding]::new($false)
    )
}

if (-not $Commit) {
    Write-Host 'Dry run only. No phone content will be copied.'
    Write-Host "Device: $DeviceName"
    Write-Host "Storage: $StorageName"
    Write-Host "Roots: $($SourceRoots -join ', ')"
    Write-Host "Destination: $destinationRoot"
    Write-Host 'Run again with -Commit to perform the read-only copy.'
    exit 0
}

[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
Write-Status -State 'starting' -Detail 'Connecting to MTP device'

$shell = New-Object -ComObject Shell.Application
$computer = $shell.Namespace(17)
$phone = @($computer.Items()) |
    Where-Object { $_.Name -eq $DeviceName } |
    Select-Object -First 1
if (-not $phone) {
    throw "MTP device not found: $DeviceName. Connect and unlock the phone."
}

$storage = @($phone.GetFolder.Items()) |
    Where-Object { $_.Name -eq $StorageName } |
    Select-Object -First 1
if (-not $storage) {
    throw "Storage not found: $StorageName"
}

foreach ($name in $SourceRoots) {
    $source = @($storage.GetFolder.Items()) |
        Where-Object { $_.Name -eq $name } |
        Select-Object -First 1
    if (-not $source) {
        Write-Warning "MTP root not found: $name"
        continue
    }
    $destination = Join-Path $destinationRoot $name
    [IO.Directory]::CreateDirectory($destination) | Out-Null
    $namespace = $shell.Namespace($destination)
    if (-not $namespace) {
        throw "Could not open local destination: $destination"
    }
    Write-Status -State 'copying' -Detail $name
    # CopyHere is asynchronous. The inventory stage provides the authoritative
    # file-level verification after the device copy has settled.
    $namespace.CopyHere($source, 20)
}

Write-Status -State 'submitted' -Detail 'MTP copy requests submitted; run inventory verification next'
Write-Host 'Copy requests submitted. This script never deletes phone content.'
