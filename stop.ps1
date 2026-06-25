# NexusKit 一键停止脚本
# 只关闭本脚本启动的服务窗口，不影响其他进程

Write-Host "🛑 正在停止 NexusKit 服务..." -ForegroundColor Yellow

# 根据窗口标题查找并关闭（与 start.ps1 中 -Title 对应）
$titles = @("Backend-Service", "Datahub-Service", "Gateway-Service", "Admin-Service")
foreach ($title in $titles) {
    $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$title*" }
    if ($proc) {
        $proc | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
        Write-Host "  ✔ 已关闭: $title" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ 未找到: $title (可能已关闭)" -ForegroundColor DarkGray
    }
}

# 可选：停止 Docker 容器
$containers = @("nexuskit-db", "nexuskit-redis")
foreach ($c in $containers) {
    $result = docker inspect $c 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker stop $c | Out-Null
        Write-Host "  ✔ 已停止容器: $c" -ForegroundColor Green
    }
}

Write-Host "✨ 所有 NexusKit 服务已停止。" -ForegroundColor Cyan
