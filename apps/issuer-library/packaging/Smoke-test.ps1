# Offline acceptance on the target Windows host: the bundled Python, an offline run review and a
# library update in a temporary workspace. No provider is called and nothing is sent.
$ErrorActionPreference = 'Stop'
$Python = Join-Path $PSScriptRoot 'engine\runtime\python.exe'
$Engine = Join-Path $PSScriptRoot 'engine'
$Work = Join-Path $env:TEMP ('issuer-library-smoke-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path (Join-Path $Work 'issuer') | Out-Null
Set-Content -Path (Join-Path $Work 'issuer\annual.txt') -Value 'Net sales were 100.'
Copy-Item (Join-Path $Engine 'smoke-context.json') (Join-Path $Work 'context.json')
& $Python -I -B -X utf8 (Join-Path $Engine 'run_workflow.py') --context (Join-Path $Work 'context.json') `
  --sources (Join-Path $Work 'issuer') --config sol-medium --cap 25 --out (Join-Path $Work 'runs\smoke')
if ($LASTEXITCODE -ne 0) { throw 'The offline run review failed' }
& $Python -I -B -X utf8 (Join-Path $Engine 'update_library.py') --workspace $Work
if ($LASTEXITCODE -ne 0) { throw 'The library update failed' }
if (-not (Test-Path (Join-Path $Work 'library\index.html'))) { throw 'No library page was written' }
Write-Output "Smoke test passed. Workspace: $Work"
