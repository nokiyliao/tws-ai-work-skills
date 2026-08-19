[CmdletBinding()]
param(
    [ValidateSet("Install", "Check")]
    [string]$Mode = "Install",
    [switch]$SkipRemote
)

$ErrorActionPreference = "Stop"
$MinimumPython = [Version]"3.10"
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$Bootstrap = Join-Path $CodexHome "skills\nokiy-deck-orchestrator\scripts\runtime_bootstrap.py"
$WorkspaceSetup = Join-Path $PSScriptRoot "setup_workspace.py"

function Resolve-Python {
    $candidates = @(
        @{ Command = "py"; Prefix = @("-3.12") },
        @{ Command = "py"; Prefix = @("-3.11") },
        @{ Command = "py"; Prefix = @("-3.10") },
        @{ Command = "python"; Prefix = @() },
        @{ Command = "python3"; Prefix = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) { continue }
        try {
            $versionText = & $candidate.Command @($candidate.Prefix) -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
            $version = [Version]$versionText.Trim()
            if ($version -ge $MinimumPython) {
                return @($candidate.Command) + @($candidate.Prefix)
            }
        } catch { continue }
    }
    throw "找不到 Python 3.10 以上版本。請安裝官方 Python，並勾選加入 PATH，完成後重新執行。"
}

if (-not (Test-Path -LiteralPath $Bootstrap -PathType Leaf)) {
    throw "找不到已安裝的 nokiy-deck-orchestrator：$Bootstrap"
}
if (-not (Test-Path -LiteralPath $WorkspaceSetup -PathType Leaf)) {
    throw "找不到學員工作區建置程式：$WorkspaceSetup"
}

$Python = Resolve-Python
$PythonCommand = $Python[0]
$PythonPrefix = if ($Python.Count -gt 1) { $Python[1..($Python.Count - 1)] } else { @() }

& $PythonCommand @PythonPrefix $WorkspaceSetup $Mode.ToLowerInvariant()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# runtime_bootstrap can discover uv in PATH and standard per-user Windows paths.
# If unavailable, install it only for the current Windows user.
$uvReady = $false
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    try { & uv --version *> $null; $uvReady = ($LASTEXITCODE -eq 0) } catch { $uvReady = $false }
}
if (-not $uvReady) {
    & $PythonCommand @PythonPrefix -m pip install --user --disable-pip-version-check uv
    if ($LASTEXITCODE -ne 0) { throw "無法在目前使用者帳號安裝 uv。" }
}

$Arguments = @($Bootstrap, $Mode.ToLowerInvariant())
if ($SkipRemote) { $Arguments += "--skip-remote" }
& $PythonCommand @PythonPrefix @Arguments
exit $LASTEXITCODE
