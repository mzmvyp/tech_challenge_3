# Dockerfile - Sistema de Previsão de Acidentes PRF

# Imagem base com Python
FROM python:3.13-slim

# Metadados
LABEL maintainer="mzmvyp <github.com/mzmvyp>"
LABEL version="1.0.0"
LABEL description="Sistema de Previsão de Gravidade de Acidentes em Rodovias Federais"

# Definindo diretório de trabalho
WORKDIR /app

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    DASHBOARD_PORT=8501

# Instalando dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiando arquivo de requirements
COPY requirements.txt .

# Instalando dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiando código da aplicação
COPY . .

# Criando diretórios necessários
RUN mkdir -p data/raw data/models logs

# Criando usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expondo portas
EXPOSE 8000 8501

# Comando padrão - executa o sistema completo
CMD ["python", "main.py"]