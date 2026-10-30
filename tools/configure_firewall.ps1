# Explicit setup helper. Never invoked automatically by the game/build.
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$Executable,
    [ValidateRange(1024,65535)][int]$Port = 12345,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$resolvedExecutable = (Resolve-Path -LiteralPath $Executable).Path
if (-not (Test-Path -LiteralPath $resolvedExecutable -PathType Leaf) -or
    [IO.Path]::GetFileName($resolvedExecutable) -ne 'openlf2.exe') {
    throw 'Wybierz plik openlf2.exe gry.'
}
$digest = [Security.Cryptography.SHA256]::Create()
try {
    $identity = [BitConverter]::ToString($digest.ComputeHash(
        [Text.Encoding]::UTF8.GetBytes($resolvedExecutable.ToLowerInvariant()))).Replace('-','').Substring(0,16)
} finally { $digest.Dispose() }
$ruleName = "PolishFighters-LAN-$identity-$Port"
if ($Remove) {
    if ($PSCmdlet.ShouldProcess($ruleName, 'Usuń regułę Polish Fighters')) {
        Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    }
} elseif ($PSCmdlet.ShouldProcess("$resolvedExecutable TCP $Port, Private, LocalSubnet", 'Dodaj regułę LAN')) {
    if (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue) {
        throw 'Reguła już istnieje. Usuń ją jawnie przez -Remove przed ponowną konfiguracją.'
    }
    New-NetFirewallRule -Name $ruleName -DisplayName "Polish Fighters LAN ($Port)" `
        -Group 'Polish Fighters' -Direction Inbound -Action Allow -Enabled True `
        -Program $resolvedExecutable -Protocol TCP -LocalPort $Port `
        -Profile Private -RemoteAddress LocalSubnet -EdgeTraversalPolicy Block
}
