@echo off
echo ========================================
echo  COMPILATION CHAT COLOC .EXE
echo ========================================

rem Vérifier que PyInstaller est installé
python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo Installation de PyInstaller...
    pip install pyinstaller
)

rem Nettoyer les anciennes compilations
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del chat.spec 2>nul

echo.
echo [1/3] Conversion PNG vers ICO (si nécessaire)...
if exist "logo.png" (
    python -c "from PIL import Image; img = Image.open('logo.png'); img.save('chat_icon.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])"
    echo ✓ Icône créée : chat_icon.ico
) else (
    echo ℹ PNG non trouvé, utilisation icône existante...
)

echo.
echo [2/3] Vérification des métadonnées...
if not exist "version_info.txt" (
    echo ❌ version_info.txt manquant!
    pause
    exit /b 1
)

echo.
echo [3/3] Compilation avec PyInstaller...
pyinstaller --onefile ^
            --icon=chat_icon.ico ^
            --name "ChatSMB" ^
            --version-file=version_info.txt ^
            --add-data "chat_icon.ico;." ^
            --clean ^
            --noconsole ^
            chat.py

echo.
if exist "dist\ChatSMB.exe" (
    echo ✅ COMPILATION RÉUSSIE !
    echo Fichier : dist\ChatSMB.exe
    echo Taille : 
    for %%F in ("dist\ChatSMB.exe") do echo   %%~zF octets
    echo.
    echo 📋 Métadonnées incluses :
    echo   - Copyright : github.com/berru-g/OTTO/SMBchat/
    echo   - Version : 1.0.0.0
    echo   - Compagnie : Berru-G
) else (
    echo ❌ Échec de la compilation
)

echo.
pause