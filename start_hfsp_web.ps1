$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{
            Exe = "py"
            Args = @("-3")
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{
            Exe = "python"
            Args = @()
        }
    }
    throw "Python was not found in PATH. Install Python 3.12+ and try again."
}

function Test-HfspRunning([int]$Port) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        return $resp.status -eq "ok"
    } catch {
        return $false
    }
}

function Test-PortAvailable([int]$Port) {
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

function Get-PortPids([int]$Port) {
    $pids = @()
    try {
        $pids += Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    } catch {
    }

    if (-not $pids) {
        $netstatLines = netstat -ano -p tcp | Select-String -Pattern "127\.0\.0\.1:$Port\s+.*LISTENING\s+(\d+)$"
        foreach ($line in $netstatLines) {
            if ($line.Matches.Count -gt 0) {
                $pids += [int]$line.Matches[0].Groups[1].Value
            }
        }
    }

    return $pids | Where-Object { $_ -and $_ -ne $PID } | Select-Object -Unique
}

function Stop-HfspProcess([int]$Port) {
    $pids = Get-PortPids -Port $Port
    foreach ($processId in $pids) {
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "[INFO] Stopped existing HFSP process on port $Port (PID $processId)."
        } catch {
            Write-Host "[WARN] Failed to stop process PID $processId on port $Port."
        }
    }
}

$python = Get-PythonCommand

try {
    & $python.Exe @($python.Args) -c "import fastapi, uvicorn" | Out-Null
} catch {
    throw "Missing Python packages: fastapi and/or uvicorn. Run: pip install fastapi uvicorn"
}

$ports = 8000..8005
$selectedPort = $null

foreach ($port in $ports) {
    if (Test-HfspRunning -Port $port) {
        Write-Host "[INFO] Existing HFSP instance detected on port $port."
        Write-Host "[INFO] Restarting to load the latest frontend files."
        Stop-HfspProcess -Port $port
        Start-Sleep -Seconds 1
    }

    if (Test-PortAvailable -Port $port) {
        $selectedPort = $port
        break
    }
}

if (-not $selectedPort) {
    throw "No available port found in 8000-8005."
}

Write-Host "[INFO] Starting HFSP Web app..."
Write-Host "[INFO] URL: http://127.0.0.1:$selectedPort"

$cacheBust = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:$selectedPort/login?v=$cacheBust'"
)

$env:HFSP_HOST = "127.0.0.1"
$env:HFSP_PORT = "$selectedPort"
& $python.Exe @($python.Args) "$PSScriptRoot\src\web_app.py"
