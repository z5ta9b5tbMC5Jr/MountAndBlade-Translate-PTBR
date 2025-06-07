@echo off
chcp 65001 >nul
echo ========================================
echo  Mount and Blade Warband - Tradutor
echo   para Português Brasileiro
echo ========================================
echo.

echo Verificando instalação do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python não encontrado!
    echo Por favor, instale o Python 3.7+ em https://python.org
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Instalando dependências...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha na instalação das dependências!
    pause
    exit /b 1
)

echo.
echo Dependências instaladas com sucesso!
echo.
echo Iniciando tradução dos arquivos CSV...
echo.

python translate_optimized.py

echo.
echo ========================================
echo Tradução concluída!
echo Verifique a pasta 'output' para os arquivos traduzidos.
echo ========================================
pause