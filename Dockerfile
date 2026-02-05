FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta do servidor web
EXPOSE 8083

# Define variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Sao_Paulo

# Comando para iniciar a aplicação
CMD ["python", "main.py"]
