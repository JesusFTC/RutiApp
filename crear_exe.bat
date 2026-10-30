@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === NutriSemana: crear .exe ===
echo Carpeta: %cd%
echo.

REM 1) Verificar que esten los archivos necesarios
for %%F in (app.py cristal.py logica.py) do (
  if not exist "%%F" (
    echo [ERROR] Falta el archivo %%F en esta carpeta.
    echo Deben estar juntos: app.py, cristal.py y logica.py
    pause
    exit /b 1
  )
)

REM 2) Buscar Python
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (
  where python >nul 2>nul
  if %errorlevel%==0 (set PY=python) else (
    echo [ERROR] No se encontro Python en esta computadora.
    echo Instalalo desde https://www.python.org/downloads/ y marca la casilla
    echo "Add python.exe to PATH" en la primera pantalla del instalador.
    pause
    exit /b 1
  )
)
echo Usando: %PY%

REM 3) Cerrar la app si esta abierta y borrar compilaciones anteriores
taskkill /f /im NutriSemana.exe >nul 2>nul
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist NutriSemana.spec del /q NutriSemana.spec
if exist dist (
  echo [ERROR] No se pudo borrar la carpeta "dist". Cierra NutriSemana y vuelve a intentar.
  pause
  exit /b 1
)

REM 4) Dependencias
echo Instalando PyInstaller y Pillow...
%PY% -m pip install --upgrade pyinstaller pillow
if errorlevel 1 ( echo [ERROR] Fallo la instalacion de las dependencias. & pause & exit /b 1 )

REM 5) Compilar
echo Creando el .exe...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name NutriSemana app.py
if errorlevel 1 ( echo [ERROR] Fallo la creacion del .exe. & pause & exit /b 1 )

if not exist "dist\NutriSemana.exe" (
  echo [ERROR] No se genero dist\NutriSemana.exe
  pause
  exit /b 1
)

echo.
echo Listo! Tu programa esta en: %cd%\dist\NutriSemana.exe
explorer dist
pause
