Set-Location $PSScriptRoot\..
.\.venv\Scripts\graphify.exe vscode-build .
git add graphify-out/graph.json graphify-out/metadata.json
git commit -m "chore: refresh graphify graph"
