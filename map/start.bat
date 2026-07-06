@echo off
where python >nul 2>nul
if %errorlevel%==0 (
    echo Starting server on http://localhost:8080 ...
    start http://localhost:8080
    python -m http.server 8080
) else (
    echo Python not found. Starting with PowerShell...
    start http://localhost:8080
    powershell -ExecutionPolicy Bypass -Command "$listener = [System.Net.HttpListener]::new(); $listener.Prefixes.Add('http://localhost:8080/'); $listener.Start(); Write-Host 'Server running on http://localhost:8080 (Ctrl+C to stop)'; while ($listener.IsListening) { $ctx = $listener.GetContext(); $path = $ctx.Request.Url.LocalPath; if ($path -eq '/') { $path = '/index.html' }; $file = Join-Path '%~dp0' ($path -replace '/','\'); if (Test-Path $file -PathType Leaf) { $bytes = [IO.File]::ReadAllBytes($file); $ext = [IO.Path]::GetExtension($file); $mime = @{'.html'='text/html;charset=utf-8';'.css'='text/css';'.js'='application/javascript';'.json'='application/json';'.png'='image/png';'.jpg'='image/jpeg';'.svg'='image/svg+xml';'.ico'='image/x-icon'}[$ext]; if (-not $mime) { $mime='application/octet-stream' }; $ctx.Response.ContentType = $mime; $ctx.Response.OutputStream.Write($bytes,0,$bytes.Length) } else { $ctx.Response.StatusCode = 404; $bytes = [Text.Encoding]::UTF8.GetBytes('Not Found'); $ctx.Response.OutputStream.Write($bytes,0,$bytes.Length) }; $ctx.Response.Close() }"
)
