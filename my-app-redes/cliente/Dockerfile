
# Usar uma imagem base do Python 3.9
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo requirements.txt (se houver) para o diretório de trabalho
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação para o diretório de trabalho
COPY . .

# Expor a porta que o servidor usa

# Comando para rodar o servidor
