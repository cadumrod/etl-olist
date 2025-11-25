# Imagem Base
FROM python:3.10-slim

# Cria pasta de trabalho
WORKDIR /app

# Instala ferramentas básicas do Linux
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Mantém o container rodando para o VS Code conectar
CMD ["sleep", "infinity"]