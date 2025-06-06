@echo off
REM 等待 2 秒讓主程式退出
timeout /T 2 /NOBREAK

REM 使用 git 更新程式
git pull

REM 顯示提示
echo.
echo [INFO] Update completed.
echo Please open MNYA_WordCodeGen.exe manually.
echo This window will close in 5 seconds...

timeout /T 5 /NOBREAK

exit
