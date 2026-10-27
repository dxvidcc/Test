# Einmalige Einrichtung von chess-glasses auf Windows. Start: Doppelklick auf Einrichten.bat
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Ok($text) { Write-Host "   OK: $text" -ForegroundColor Green }
function Todo($text) { Write-Host "   TODO: $text" -ForegroundColor Yellow }

Step "Python"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python -or $python.Source -like "*WindowsApps*") {
    Write-Host "   Python fehlt, wird installiert..."
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    Todo "Python ist installiert. Dieses Fenster schliessen und Einrichten.bat NOCHMAL starten."
    exit 1
}
Ok (python --version)

Step "Python-Pakete"
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
Ok "installiert"

Step "Stockfish"
if (Test-Path "stockfish.exe") {
    Ok "schon da"
} else {
    $zip = Join-Path $env:TEMP "stockfish.zip"
    $unzip = Join-Path $env:TEMP "stockfish-unzip"
    $base = "https://github.com/official-stockfish/Stockfish/releases/latest/download"
    try {
        Invoke-WebRequest "$base/stockfish-windows-x86-64-avx2.zip" -OutFile $zip
    } catch {
        Invoke-WebRequest "$base/stockfish-windows-x86-64.zip" -OutFile $zip
    }
    if (Test-Path $unzip) { Remove-Item $unzip -Recurse -Force }
    Expand-Archive $zip -DestinationPath $unzip
    $exe = Get-ChildItem $unzip -Recurse -Filter "stockfish*.exe" | Select-Object -First 1
    Copy-Item $exe.FullName "stockfish.exe"
    Remove-Item $zip, $unzip -Recurse -Force
    # Old CPUs can't run the AVX2 build: check it starts, else fall back to the generic one.
    $check = "uci`nquit`n" | .\stockfish.exe 2>$null | Select-String "uciok"
    if (-not $check) {
        Remove-Item "stockfish.exe"
        Invoke-WebRequest "$base/stockfish-windows-x86-64.zip" -OutFile $zip
        Expand-Archive $zip -DestinationPath $unzip
        $exe = Get-ChildItem $unzip -Recurse -Filter "stockfish*.exe" | Select-Object -First 1
        Copy-Item $exe.FullName "stockfish.exe"
        Remove-Item $zip, $unzip -Recurse -Force
    }
    Ok "heruntergeladen"
}

Step "Anthropic API-Key"
if ([Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")) {
    Ok "schon gespeichert"
} else {
    $key = Read-Host "   Key von console.anthropic.com einfuegen (sk-ant-...)"
    if ($key) {
        [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $key.Trim(), "User")
        Ok "gespeichert"
    } else {
        Todo "Kein Key eingegeben. Einrichten.bat spaeter nochmal starten."
    }
}

Step "VB-CABLE (virtuelles Mikrofon)"
$cable = python -c "import sounddevice as s; print(any('CABLE Input' in d['name'] for d in s.query_devices()))"
if ($cable -eq "True") {
    Ok "installiert"
} else {
    Todo "VB-CABLE fehlt. Die Seite oeffnet sich gleich: ZIP laden, entpacken,"
    Todo "VBCABLE_Setup_x64.exe mit Rechtsklick 'Als Administrator ausfuehren', danach PC neu starten."
    Start-Process "https://vb-audio.com/Cable/"
}

Step "Fertig"
Write-Host "   Zum Testen: Fotos von einem Schachbrett auf 'Foto-Test.bat' ziehen."
Write-Host "   Zum Spielen: Anruf annehmen, Mikrofon 'CABLE Output' waehlen, 'Schach.bat' doppelklicken."
