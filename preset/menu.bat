@echo off
cls
choice /c bcc /n /m "Quelle option voulez-vous ? (B)ureau, (C)ode, (C)hill: "

if errorlevel 3 goto Chill
if errorlevel 2 goto Code
if errorlevel 1 goto Bureau

:Bureau
start https://mail.google.com
start https://calendar.google.com
goto Fin

:Code
start "VSCode" "C:\Program Files\Microsoft VS Code\Code.exe"
start https://github.com
goto Fin

:Chill
start https://www.youtube.com
goto Fin

:Fin
