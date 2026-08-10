<#
.SYNOPSIS
    Removes the "wsg" command of the current user.

.DESCRIPTION
    Deletes the launcher, removes its folder from the user PATH and clears the
    WSG_HOME environment variable. The folder with the program itself is kept.

.PARAMETER BinDir
    Folder the launcher was installed into. Default:
    %LOCALAPPDATA%\Programs\wsg\bin

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
#>
[CmdletBinding()]
param(
    [string]$BinDir = (Join-Path $env:LOCALAPPDATA 'Programs\wsg\bin')
)

$ErrorActionPreference = 'Stop'
$environmentKey = 'HKCU:\Environment'

function Publish-EnvironmentChange {
    try {
        if (-not ('Wsg.NativeMethods' -as [type])) {
            Add-Type -Namespace 'Wsg' -Name 'NativeMethods' -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true, CharSet = System.Runtime.InteropServices.CharSet.Auto)]
public static extern System.IntPtr SendMessageTimeout(System.IntPtr hWnd, uint msg, System.UIntPtr wParam, string lParam, uint flags, uint timeout, out System.UIntPtr result);
'@
        }
        $unused = [System.UIntPtr]::Zero
        $null = [Wsg.NativeMethods]::SendMessageTimeout(
            [System.IntPtr]0xffff, 0x1A, [System.UIntPtr]::Zero, 'Environment', 0x0002, 3000, [ref]$unused)
        return $true
    }
    catch {
        return $false
    }
}

# --- launcher ----------------------------------------------------------------
$cmdPath = Join-Path $BinDir 'wsg.cmd'
if (Test-Path -LiteralPath $cmdPath) {
    Remove-Item -LiteralPath $cmdPath -Force
    Write-Host "[wsg] launcher removed: $cmdPath"
}
else {
    Write-Host "[wsg] launcher not found: $cmdPath"
}

if ((Test-Path -LiteralPath $BinDir) -and -not (Get-ChildItem -LiteralPath $BinDir -Force)) {
    Remove-Item -LiteralPath $BinDir -Force
    Write-Host "[wsg] empty folder removed: $BinDir"
}

# --- user PATH ---------------------------------------------------------------
$item = Get-Item -LiteralPath $environmentKey
if ($item.GetValueNames() -contains 'Path') {
    $kind = [string]$item.GetValueKind('Path')
    $raw = [string]$item.GetValue('Path', '', 'DoNotExpandEnvironmentNames')
    $parts = @($raw.Split(';') | Where-Object { $_ -ne '' })
    $kept = @($parts | Where-Object { $_ -ne $BinDir })
    if ($kept.Count -ne $parts.Count) {
        Set-ItemProperty -LiteralPath $environmentKey -Name 'Path' -Value ($kept -join ';') -Type $kind
        Write-Host "[wsg] removed from the user PATH: $BinDir"
    }
}

# --- environment variable ----------------------------------------------------
if ([Environment]::GetEnvironmentVariable('WSG_HOME', 'User')) {
    [Environment]::SetEnvironmentVariable('WSG_HOME', $null, 'User')
    Write-Host '[wsg] WSG_HOME removed'
}
$env:WSG_HOME = ''

if (Publish-EnvironmentChange) {
    Write-Host '[wsg] environment change broadcast to the system'
}

Write-Host ''
Write-Host '[wsg] done. Terminals that are already running keep the old environment'
Write-Host '      until they are closed completely and started again.'
