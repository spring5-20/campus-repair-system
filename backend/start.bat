@echo off
rem 校园报修系统后端一键启动（Windows）
rem 双击本文件即可启动，启动成功后浏览器打开 http://127.0.0.1:3000/docs
rem 关闭窗口（或按 Ctrl+C）即停止服务
cd /d "%~dp0"
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 3000
