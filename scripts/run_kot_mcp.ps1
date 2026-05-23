# Claude Desktop 用 KOT MCP ランチャー
# トークンは Windows のユーザー環境変数 KOT_ACCESS_TOKEN から読み込みます（設定ファイルには書きません）。

$ErrorActionPreference = "Stop"

$token = [Environment]::GetEnvironmentVariable("KOT_ACCESS_TOKEN", "User")
if ([string]::IsNullOrWhiteSpace($token)) {
    $token = [Environment]::GetEnvironmentVariable("KOT_ACCESS_TOKEN", "Machine")
}
if ([string]::IsNullOrWhiteSpace($token)) {
    [Console]::Error.WriteLine(
        "KOT_ACCESS_TOKEN is not set. Add it under User or Machine environment variables, then restart Claude Desktop."
    )
    exit 1
}

$env:KOT_ACCESS_TOKEN = $token

$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $projectRoot "kot_mcp_server.py"))) {
    [Console]::Error.WriteLine("kot_mcp_server.py not found: $projectRoot")
    exit 1
}

$uv = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\Scripts\uv.exe"
if (-not (Test-Path $uv)) {
    $uv = "uv"
}

& $uv run --directory $projectRoot python kot_mcp_server.py
