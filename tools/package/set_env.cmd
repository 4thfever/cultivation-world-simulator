@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

echo 请输入 Qwen API Key：
set /p QWEN_API_KEY=

if defined QWEN_API_KEY (
  setx QWEN_API_KEY "%QWEN_API_KEY%" >nul
  set QWEN_API_KEY=%QWEN_API_KEY%
  echo 已设置环境变量 QWEN_API_KEY（当前窗口已生效，系统环境变量将对新进程生效）。
) else (
  echo 未输入，请关闭窗口后重新运行并输入。
)
endlocal
exit /b 0