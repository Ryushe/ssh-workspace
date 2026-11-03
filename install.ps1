# Build and install the Windows client for the current user.
$ErrorActionPreference = 'Stop'
$python = Get-Command py.exe -ErrorAction SilentlyContinue
$pythonArgs = @('-3')
if (-not $python) {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    $pythonArgs = @()
}
if (-not $python) { throw 'Install Python 3.8 or newer from python.org, then rerun install.ps1.' }
if (-not (Get-Command ssh.exe -ErrorAction SilentlyContinue)) {
    throw 'Install the Windows OpenSSH Client optional feature, then rerun install.ps1.'
}
& $python.Source @pythonArgs -c 'import sys; sys.exit(sys.version_info < (3, 8))'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.8 or newer is required.' }
& $python.Source @pythonArgs -c 'import importlib.util, sys; sys.exit(importlib.util.find_spec(sys.argv[1]) is None)' PyInstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Installing PyInstaller for the current user...'
    & $python.Source @pythonArgs -m pip install --user pyinstaller
    if ($LASTEXITCODE -ne 0) { throw 'Could not install PyInstaller; check pip and rerun.' }
}
$build = Join-Path ([IO.Path]::GetTempPath()) ('ssh-workspace-' + [guid]::NewGuid())
$install = Join-Path $env:LOCALAPPDATA 'ssh-workspace\bin'
try {
    New-Item -ItemType Directory -Path $build, $install -Force | Out-Null
    $source = Join-Path $build 'ssh_workspace.py'
    Copy-Item (Join-Path $PSScriptRoot 'bin\ssh-workspace') $source
    & $python.Source @pythonArgs -m PyInstaller --noconfirm --onefile --name ssh-workspace `
        --distpath (Join-Path $build 'dist') --workpath (Join-Path $build 'work') `
        --specpath $build $source
    if ($LASTEXITCODE -ne 0) { throw 'Building ssh-workspace.exe failed.' }
    Copy-Item (Join-Path $build 'dist\ssh-workspace.exe') (Join-Path $install 'ssh-workspace.exe') -Force
    $userPath = [string][Environment]::GetEnvironmentVariable('Path', 'User')
    if (($userPath -split ';' | Where-Object { $_.TrimEnd('\') -ieq $install.TrimEnd('\') }).Count -eq 0) {
        [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $install).TrimStart(';')), 'User')
    }
    if (($env:Path -split ';' | Where-Object { $_.TrimEnd('\') -ieq $install.TrimEnd('\') }).Count -eq 0) {
        $env:Path += ';' + $install
    }
    Write-Host "Installed $install\ssh-workspace.exe. Open a new PowerShell window to refresh PATH."
} finally {
    if (Test-Path $build) { Remove-Item -LiteralPath $build -Recurse -Force }
}
