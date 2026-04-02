Write-Host "Criando ambiente virtual local (.venv)..."
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Write-Host "Instalando dependências locais para o IntelliSense..."
pip install -r requirements.txt
Write-Host "Ambiente local configurado com sucesso!"
