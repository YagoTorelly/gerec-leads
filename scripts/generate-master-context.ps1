param(
    [string]$OutputPath = "docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputFile = Join-Path $repoRoot $OutputPath

function Get-RelativePath([string]$Path) {
    return $Path.Substring($repoRoot.Length + 1).Replace("\", "/")
}

function Get-Language([string]$Path) {
    switch ([IO.Path]::GetExtension($Path).ToLowerInvariant()) {
        ".py" { return "python" }
        ".ts" { return "typescript" }
        ".tsx" { return "tsx" }
        ".css" { return "css" }
        ".json" { return "json" }
        ".toml" { return "toml" }
        ".yml" { return "yaml" }
        ".yaml" { return "yaml" }
        ".ps1" { return "powershell" }
        default { return "text" }
    }
}

function Add-Source([System.Collections.Generic.List[string]]$Lines, [string]$Path, [string]$Kind) {
    $relativePath = Get-RelativePath $Path
    $content = Get-Content -LiteralPath $Path -Encoding utf8

    $Lines.Add("")
    $Lines.Add(('## {0}: `{1}`' -f $Kind, $relativePath))
    $Lines.Add("")

    if ($Path.EndsWith(".md", [StringComparison]::OrdinalIgnoreCase)) {
        $Lines.AddRange([string[]]($content | ForEach-Object { $_.TrimEnd() }))
        return
    }

    $Lines.Add(('````{0}' -f (Get-Language $Path)))
    $Lines.AddRange([string[]]$content)
    $Lines.Add('````')
}

$lines = [System.Collections.Generic.List[string]]::new()
$generatedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss 'UTC'")

$lines.Add("# Contexto Mestre - Gerenciador de Leads WTG")
$lines.Add("")
$lines.Add(('> Gerado em {0} por `scripts/generate-master-context.ps1`.' -f $generatedAt))
$lines.Add("")
$lines.Add("## Como usar este documento")
$lines.Add("")
$lines.Add("Este é um pacote de contexto autocontido para desenvolvimento e revisão. Ele consolida fontes documentais e um retrato do código relevante; não substitui os arquivos de origem.")
$lines.Add("")
$lines.Add("### Hierarquia de autoridade")
$lines.Add("")
$lines.Add('1. `SPEC_GERENCIADOR_DE_LEADS_WTG.md` é a regra funcional canônica.')
$lines.Add("2. Decisões de governança aprovadas por Yago alteram explicitamente o SPEC.")
$lines.Add('3. `AGENTS.md` contém regras permanentes para o trabalho no repositório.')
$lines.Add("4. Desenhos, planos, evidências e relatórios explicam contexto, histórico e execução; divergências devem ser apontadas antes de qualquer implementação.")
$lines.Add("5. O código e as configurações são um retrato técnico do branch que gerou este arquivo e nunca substituem uma regra de negócio canônica.")
$lines.Add("")
$lines.Add("### Escopo incluído")
$lines.Add("")
$lines.Add("- documentação Markdown rastreada do projeto;")
$lines.Add("- configurações de build e deploy sem segredos;")
$lines.Add("- código Python da API e automações;")
$lines.Add("- código TypeScript/TSX/CSS do frontend, incluindo testes próximos ao código.")
$lines.Add("")
$lines.Add("Arquivos de ambiente, credenciais, dumps, planilhas e dependências geradas são excluídos por segurança e para evitar contexto inútil.")

$canonical = Join-Path $repoRoot "SPEC_GERENCIADOR_DE_LEADS_WTG.md"
Add-Source $lines $canonical "Fonte canônica"

$documentationFiles = @(
    "AGENTS.md",
    "README.md",
    "ROADMAP.md",
    "docs/ARQUITETURA.md",
    "docs/DECISOES.md"
) | ForEach-Object { Join-Path $repoRoot $_ } | Where-Object { Test-Path -LiteralPath $_ }

foreach ($file in $documentationFiles) {
    Add-Source $lines $file "Documento de orientação"
}

$specDirectory = Join-Path $repoRoot "docs/superpowers/specs"
Get-ChildItem -LiteralPath $specDirectory -File -Filter "*.md" | Sort-Object Name | ForEach-Object {
    Add-Source $lines $_.FullName "Desenho de produto"
}

$planDirectory = Join-Path $repoRoot "docs/superpowers/plans"
Get-ChildItem -LiteralPath $planDirectory -File -Filter "*.md" | Sort-Object Name | ForEach-Object {
    Add-Source $lines $_.FullName "Plano histórico ou executável"
}

$supportDocuments = @(
    "apps/web/README.md",
    "infra/railway/README.md",
    "integrations/n8n/README.md",
    "tests/contracts/README.md"
) | ForEach-Object { Join-Path $repoRoot $_ } | Where-Object { Test-Path -LiteralPath $_ }

foreach ($file in $supportDocuments) {
    Add-Source $lines $file "Documento complementar"
}

Get-ChildItem -LiteralPath (Join-Path $repoRoot "docs/evidencias") -File -Filter "*.md" -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
    Add-Source $lines $_.FullName "Evidência"
}

Get-ChildItem -LiteralPath $repoRoot -File -Filter "task-*-report.md" | Sort-Object Name | ForEach-Object {
    Add-Source $lines $_.FullName "Relatório histórico"
}

$configurationPatterns = @(
    "package.json",
    "apps/api/pyproject.toml",
    "apps/api/Dockerfile",
    "apps/web/package.json",
    "railway.json",
    "vercel.json",
    "infra/railway/*"
)

foreach ($pattern in $configurationPatterns) {
    Get-ChildItem -Path (Join-Path $repoRoot $pattern) -File -ErrorAction SilentlyContinue | Sort-Object FullName | ForEach-Object {
        if ($_.Name -notmatch "^\.env") {
            Add-Source $lines $_.FullName "Configuração técnica"
        }
    }
}

$sourceRoots = @(
    (Join-Path $repoRoot "apps/api/src"),
    (Join-Path $repoRoot "apps/web/src")
)

foreach ($sourceRoot in $sourceRoots) {
    Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
        Where-Object {
            $_.Extension -in ".py", ".ts", ".tsx", ".css" -and
            $_.FullName -notmatch "[\\/](?:__pycache__|node_modules|\\.next)[\\/]"
        } |
        Sort-Object FullName |
        ForEach-Object { Add-Source $lines $_.FullName "Snapshot de código" }
}

$directory = Split-Path -Parent $outputFile
New-Item -ItemType Directory -Path $directory -Force | Out-Null
Set-Content -LiteralPath $outputFile -Value $lines -Encoding utf8

Write-Output "Gerado: $(Get-RelativePath $outputFile)"
Write-Output "Linhas: $($lines.Count)"
