@echo off
setlocal enabledelayedexpansion

:: =============================================
:: CONFIGURACIÓN DE COLORES
:: =============================================
for /F "delims=#" %%a in ('"prompt #$E# & for %%b in (1) do rem"') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "BLUE=%ESC%[94m"
set "YELLOW=%ESC%[93m"
set "RED=%ESC%[91m"
set "CYAN=%ESC%[96m"
set "MAGENTA=%ESC%[95m"
set "RESET=%ESC%[0m"

:: =============================================
:: CONFIGURACIÓN AUTOMÁTICA
:: =============================================
:: Detectamos Python automáticamente para evitar errores de ruta
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.base_prefix)"') do set "PYTHON_PATH=%%i"

set OUTPUT_NAME=GestorMinecraft
set PROJECT_ROOT=%~dp0
set DIST_PATH=%PROJECT_ROOT%dist
set FINAL_EXE=%DIST_PATH%\%OUTPUT_NAME%.exe
set UPX_PATH=.\upx\upx.exe
set USE_UPX=true

:: =============================================
:: VERIFICAR DEPENDENCIAS
:: =============================================
echo %CYAN%[INFO]%RESET% %GREEN%Verificando dependencias...%RESET%
echo %GREEN%[OK]%RESET% Python detectado en: %PYTHON_PATH%
echo %GREEN%[OK]%RESET% UPX detectado en: %UPX_PATH%

pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% PyInstaller no está instalado.
    echo %YELLOW%Instala con:%RESET% pip install pyinstaller
    pause
    exit /b 1
)

:: =============================================
:: PASO 1: LIMPIEZA PREVIA
:: =============================================
echo %BLUE%[Paso 1/5]%RESET% %GREEN%Limpiando archivos anteriores...%RESET%
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist dist_obf rmdir /s /q dist_obf >nul 2>&1
if exist "%OUTPUT_NAME%.spec" del /q "%OUTPUT_NAME%.spec" >nul 2>&1
if exist "%PROJECT_ROOT%%OUTPUT_NAME%.exe" del /q "%PROJECT_ROOT%%OUTPUT_NAME%.exe" >nul 2>&1

:: =============================================
:: PASO 3: EMPAQUETAR CON PYINSTALLER
:: =============================================
echo %BLUE%[Paso 2/5]%RESET% %GREEN%Empaquetando con PyInstaller...%RESET%

pyinstaller --noconfirm --onefile --windowed --noupx --clean ^
 --name "%OUTPUT_NAME%" ^
 --icon "icon.ico" ^
 --collect-all customtkinter ^
 --hidden-import PIL ^
 --hidden-import PIL.Image ^
 --hidden-import requests ^
 --hidden-import plyer ^
 --hidden-import packaging ^
 --add-data "config;config" ^
 --add-data "core;core" ^
 --add-data "services;services" ^
 --add-data "ui;ui" ^
 --add-data "utils;utils" ^
 --add-data "icon.ico;." ^
 --add-data "icon.png;." ^
 --add-data "%PYTHON_PATH%\tcl;tcl" ^
 --add-data "%PYTHON_PATH%\DLLs\_tkinter.pyd;." ^
 --add-data "%PYTHON_PATH%\DLLs\tk86t.dll;." ^
 --add-data "%PYTHON_PATH%\DLLs\tcl86t.dll;." ^
main.py >nul 2>&1

if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Error en el empaquetado. Revisa las dependencias.
    pause
    exit /b 1
)

:: =============================================
:: PASO 4: COMPRESIÓN UPX (Solo si está activo)
:: =============================================
if "%USE_UPX%"=="true" (
    echo %BLUE%[Paso 3/5]%RESET% %GREEN%Comprimiendo con UPX...%RESET%
    if exist "%UPX_PATH%" (
        "%UPX_PATH%" --best --force "%FINAL_EXE%" >nul 2>&1
    ) else (
        echo %YELLOW%[SKIP]%RESET% UPX no encontrado en la carpeta del proyecto.
    )
) else (
    echo %BLUE%[Paso 3/5]%RESET% %YELLOW%Saltando compresion UPX...%RESET%
)

:: =============================================
:: PASO 5: MOVER EJECUTABLE
:: =============================================
echo %BLUE%[Paso 4/5]%RESET% %GREEN%Moviendo ejecutable...%RESET%

if not exist "%FINAL_EXE%" (
    echo %RED%[ERROR]%RESET% No se encontró el ejecutable generado.
    pause
    exit /b 1
)

move /Y "%FINAL_EXE%" "%PROJECT_ROOT%" >nul 2>&1

:: =============================================
:: PASO 6: LIMPIEZA FINAL
:: =============================================
echo %BLUE%[Paso 5/5]%RESET% %GREEN%Limpiando temporales...%RESET%
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1
rmdir /s /q dist_obf >nul 2>&1
del /q %OUTPUT_NAME%.spec >nul 2>&1

:: =============================================
:: FIN
:: =============================================
echo.
echo %GREEN%========================================%RESET%
echo %GREEN%    PROCESO COMPLETADO EXITOSAMENTE     %RESET%
echo %GREEN%========================================%RESET%
echo.
if exist "%PROJECT_ROOT%%OUTPUT_NAME%.exe" (
    echo %YELLOW%Archivo generado:%RESET% %OUTPUT_NAME%.exe
)
echo.
pause
