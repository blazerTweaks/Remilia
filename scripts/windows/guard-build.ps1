# SPDX-License-Identifier: MPL-2.0
<#
.SYNOPSIS
  Resource monitor and safety guard for the REMILIA build container (guard v2).

.DESCRIPTION
  Samples Windows and WSL2-VM memory every few seconds while a build container
  runs, writes one CSV row per sample, and stops the build in a controlled way
  (SIGINT to the build processes, never a WSL or Docker shutdown) when memory
  runs out. Start it BEFORE the build container; it waits for the container to
  appear and ends when the container has exited.

  Stop rules (defaults = the values validated during the Phase 2 builds):
    Windows available memory < WinLowGB for WinLowSeconds       -> stop
    Windows available memory < WinEmergencyGB                   -> stop now
    Windows commit headroom < CommitEmergencyGB                 -> stop now
    this loop stalled for more than StallSeconds                -> stop now
    VM swap used > VmSwapEmergencyPct                           -> stop now
    VM MemAvailable < VmLowGB for VmLowSeconds                  -> stop
  Docker errors are not treated as "build finished": the build counts as
  finished only when `docker ps` succeeds and no longer lists the container.

  The build container must be started with --name <Container> (BUILD.md).

.PARAMETER Csv
  Output CSV file (one row per sample). Required.
.PARAMETER Events
  Output event log. Required.
.PARAMETER ConfigFile
  Optional .psd1 file with any of the parameters below as keys. Values given
  on the command line win over the file; the file wins over the defaults.

.EXAMPLE
  .\scripts\windows\guard-build.ps1 -Csv "$env:TEMP\guard.csv" -Events "$env:TEMP\guard-events.log"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Csv,
    [Parameter(Mandatory = $true)][string]$Events,
    [string]$ConfigFile,
    [string]$Container = "remilia-build-run",
    [string]$WorkPath = "/builds/work",
    [string]$WslDistro = "docker-desktop",
    [int]$IntervalSeconds = 15,
    [double]$WinLowGB = 4,
    [int]$WinLowSeconds = 300,
    [double]$WinEmergencyGB = 2,
    [double]$CommitEmergencyGB = 1.5,
    [int]$StallSeconds = 90,
    [double]$VmSwapEmergencyPct = 90,
    [double]$VmLowGB = 0.5,
    [int]$VmLowSeconds = 60
)

if ($ConfigFile) {
    $cfg = Import-PowerShellDataFile -Path $ConfigFile
    foreach ($key in $cfg.Keys) {
        if ($key -in @("Csv", "Events", "ConfigFile")) { throw "$key cannot be set in the config file" }
        if (-not (Get-Variable -Name $key -Scope Local -ErrorAction SilentlyContinue)) { throw "unknown setting in ${ConfigFile}: $key" }
        if (-not $PSBoundParameters.ContainsKey($key)) { Set-Variable -Name $key -Value $cfg[$key] }
    }
}

$inv = [System.Globalization.CultureInfo]::InvariantCulture
"utc,win_available_gb,win_commit_free_gb,vmmem_ws_gb,vm_available_gb,vm_used_gb,vm_cache_gb,vm_swap_used_gb,vm_swap_pct,win_cpu_pct,ctr_cpu_pct,disk_free_gb,win_low_s,vm_low_s,docker_ok" | Out-File -Encoding utf8 $Csv
function Log($msg) { "$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) $msg" | Out-File -Append -Encoding utf8 $Events }
function Stop-Build($why) {
    Log "CONTROLLED STOP: $why"
    docker exec $Container sh -c 'kill -INT -1' 2>$null
    if ($LASTEXITCODE -ne 0) {
        Log "docker exec failed; sending SIGINT via WSL to processes whose cmdline contains $WorkPath/"
        wsl.exe -d $WslDistro -e sh -c "for p in /proc/[0-9]*; do grep -q $WorkPath/ `$p/cmdline 2>/dev/null && kill -INT `${p#/proc/} 2>/dev/null; done"
    }
    $script:stopped = $true
}
function Get-VmMeminfo {
    $m = @{}
    $lines = docker exec $Container cat /proc/meminfo 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $lines) { $lines = wsl.exe -d $WslDistro -e cat /proc/meminfo 2>$null }
    foreach ($line in $lines) { $p = "$line" -split '\s+'; if ($p.Count -ge 2) { $m[$p[0].TrimEnd(':')] = [double]$p[1] } }
    return $m
}
Log ([string]::Format($inv, "guard v2 started (container {0}, interval {1} s, Windows low {2} GB/{3} s, emergency {4} GB, commit {5} GB, stall {6} s, VM swap {7}%, VM low {8} GB/{9} s)",
    $Container, $IntervalSeconds, $WinLowGB, $WinLowSeconds, $WinEmergencyGB, $CommitEmergencyGB, $StallSeconds, $VmSwapEmergencyPct, $VmLowGB, $VmLowSeconds))
$seen = $false; $winLow = $null; $vmLow = $null; $stopped = $false; $last = Get-Date; $dockerDownSince = $null
while ($true) {
    $now = Get-Date; $gap = ($now - $last).TotalSeconds; $last = $now
    $names = docker ps --format "{{.Names}}" 2>$null
    $dockerOk = ($LASTEXITCODE -eq 0)
    $running = $dockerOk -and ($names -contains $Container)
    if ($dockerOk) {
        if ($dockerDownSince) { Log "docker responding again"; $dockerDownSince = $null }
        if ($running -and -not $seen) { $seen = $true; Log "build container detected" }
        if (-not $running -and $seen) { Log "build container exited (docker ps OK, container not listed)"; break }
    } elseif (-not $dockerDownSince) { $dockerDownSince = $now; Log "WARNING docker not responding" }
    $perf = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
    $os = Get-CimInstance Win32_OperatingSystem
    $avail = $perf.AvailableMBytes / 1024
    $commitFree = $os.FreeVirtualMemory / 1MB
    $vmws = (Get-Process VmmemWSL, vmmem -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum / 1GB
    $cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
    $vmAvail = $null; $vmUsed = $null; $vmCache = $null; $swapUsed = $null; $swapPct = $null
    if ($seen) {
        $m = Get-VmMeminfo
        if ($m.MemTotal) {
            $vmAvail = $m.MemAvailable / 1MB; $vmUsed = ($m.MemTotal - $m.MemAvailable) / 1MB
            $vmCache = ($m.Cached + $m.Buffers) / 1MB; $swapUsed = ($m.SwapTotal - $m.SwapFree) / 1MB
            $swapPct = if ($m.SwapTotal) { 100 * ($m.SwapTotal - $m.SwapFree) / $m.SwapTotal } else { 0 }
        }
    }
    $ctrCpu = ""; $disk = ""
    if ($running) {
        $ctrCpu = (docker stats --no-stream --format "{{.CPUPerc}}" $Container 2>$null) -replace '%', ''
        $df = docker exec $Container sh -c "df -k --output=avail $WorkPath | tail -1" 2>$null
        if ($df) { $disk = [string]::Format($inv, "{0:F1}", [double]$df / 1MB) }
    }
    if ($avail -lt $WinLowGB) { if (-not $winLow) { $winLow = $now } } else { $winLow = $null }
    if ($vmAvail -ne $null -and $vmAvail -lt $VmLowGB) { if (-not $vmLow) { $vmLow = $now } } else { $vmLow = $null }
    $winLowS = if ($winLow) { [int]($now - $winLow).TotalSeconds } else { 0 }
    $vmLowS = if ($vmLow) { [int]($now - $vmLow).TotalSeconds } else { 0 }
    $f = { param($x) if ($x -eq $null) { "" } else { [string]::Format($inv, "{0:F2}", $x) } }
    [string]::Format($inv, "{0},{1:F2},{2:F2},{3:F2},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}",
        $now.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'), $avail, $commitFree, $vmws,
        (& $f $vmAvail), (& $f $vmUsed), (& $f $vmCache), (& $f $swapUsed), (& $f $swapPct),
        $cpu, $ctrCpu, $disk, $winLowS, $vmLowS, $dockerOk) | Out-File -Append -Encoding utf8 $Csv
    if ($seen -and -not $stopped) {
        if ($avail -lt $WinEmergencyGB) { Stop-Build ([string]::Format($inv, "EMERGENCY Windows available {0:F2} GB < {1} GB", $avail, $WinEmergencyGB)) }
        elseif ($commitFree -lt $CommitEmergencyGB) { Stop-Build ([string]::Format($inv, "EMERGENCY Windows commit headroom {0:F2} GB < {1} GB", $commitFree, $CommitEmergencyGB)) }
        elseif ($gap -gt $StallSeconds) { Stop-Build "EMERGENCY monitor loop stalled $([int]$gap) s" }
        elseif ($swapPct -ne $null -and $swapPct -gt $VmSwapEmergencyPct) { Stop-Build ([string]::Format($inv, "EMERGENCY VM swap {0:F0}% used (> {1}%)", $swapPct, $VmSwapEmergencyPct)) }
        elseif ($vmLowS -ge $VmLowSeconds) { Stop-Build ([string]::Format($inv, "VM MemAvailable < {0} GB for {1} s", $VmLowGB, $vmLowS)) }
        elseif ($winLowS -ge $WinLowSeconds) { Stop-Build ([string]::Format($inv, "Windows available < {0} GB for {1} s", $WinLowGB, $winLowS)) }
    }
    Start-Sleep -Seconds $IntervalSeconds
}
Log "guard v2 finished"
