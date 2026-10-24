param(
    [int]$Repetitions = 10,
    [int]$Duration = 360,
    [int]$Warmup = 60,
    [string]$HostUrl = "http://localhost:8085"
)

$ErrorActionPreference = "Stop"

# Sobe os containers da aplicacao
Write-Host "Iniciando containers Docker do Spring PetClinic..." -ForegroundColor Cyan
docker compose up -d

# Aguarda o API Gateway responder na rota de veterinarios
Write-Host "Aguardando API Gateway em $HostUrl..." -ForegroundColor Cyan
$maxAttempts = 60
$attempt = 0
$ready = $false
while ($attempt -lt $maxAttempts) {
    $attempt++
    try {
        $resp = Invoke-WebRequest -Uri "$HostUrl/api/vet/vets" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) {
            $ready = $true
            Write-Host "API Gateway disponivel (HTTP 200)." -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "Aguardando registro dos servicos no Eureka ($attempt/$maxAttempts)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $ready) {
    Write-Warning "API Gateway nao respondeu HTTP 200. Verifique 'docker compose ps'."
}

# Executa os experimentos no Locust e gera os graficos
Write-Host "Executando experimentos no Locust..." -ForegroundColor Cyan
python scripts/run_experiments.py --host $HostUrl --repetitions $Repetitions --duration $Duration --warmup $Warmup

Write-Host "Consolidando resultados e gerando graficos..." -ForegroundColor Cyan
python scripts/analyze_results.py

Write-Host "Concluido." -ForegroundColor Green
