# 1. 启动基础设施
Write-Host "🚀 启动 Docker 基础设施..." -ForegroundColor Cyan
docker compose -f deploy/docker-compose.yml up -d

# 2. 等待 PostgreSQL 5432 端口开放
Write-Host "⏳ 等待数据库启动..." -ForegroundColor Yellow
while (-not (Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue).TcpTestSucceeded) {
    Start-Sleep -Seconds 1
}
Write-Host "✅ 数据库已就绪！" -ForegroundColor Green

# 3. 等待 Redis 6379 端口开放
Write-Host "⏳ 等待 Redis 启动..." -ForegroundColor Yellow
while (-not (Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue).TcpTestSucceeded) {
    Start-Sleep -Seconds 1
}
Write-Host "✅ Redis 已就绪！" -ForegroundColor Green

# 4. 启动服务
Write-Host "📦 启动微服务全家桶..." -ForegroundColor Green

# Backend
Start-Process cmd.exe `
    -ArgumentList '/k title Backend-Service && .venv\Scripts\uvicorn.exe main:app --reload --port 5000' `
    -WorkingDirectory 'core-service'

# Datahub Service
Start-Process cmd.exe `
    -ArgumentList '/k title Datahub-Service && .venv\Scripts\uvicorn.exe app.main:app --reload --port 8000' `
    -WorkingDirectory 'datahub-service'

# Gateway
Start-Process cmd.exe `
    -ArgumentList '/k title Gateway-Service && volta run --node 22 npm run dev' `
    -WorkingDirectory 'gateway'

# Admin
Start-Process cmd.exe `
    -ArgumentList '/k title Admin-Service && volta run --node 22 --pnpm 10 pnpm dev' `
    -WorkingDirectory '../nexuskit-admin'

Write-Host "🎉 所有服务已启动，请查看各窗口输出。" -ForegroundColor Green
