# GuardNet - Cloudflare Attack Map

Mapa de ataques em tempo real utilizando logs da Cloudflare. Visualiza requisições bloqueadas (status 403) em um mapa interativo.

![Attack Map Preview](frontend/static/images/marker.svg)

## Requisitos

- Python 3.8+
- Redis
- Conta Cloudflare com plano Enterprise (necessário para Instant Logs)

## Instalação

### 1. Clone o repositório

```bash
git clone <repo-url>
cd guardnet-mapAttack
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `REDIS_IP` | IP do servidor Redis | Sim |
| `REDIS_CHANNEL` | Canal Redis para pub/sub | Sim |
| `CLOUDFLARE_API_TOKEN` | Token da API Cloudflare | Sim |
| `CLOUDFLARE_ZONE_NAMES` | Lista de zonas separadas por vírgula | Não |
| `CLOUDFLARE_ACCOUNT_ID` | ID da conta Cloudflare | Não |

### 4. Inicie o Redis

Usando Docker:

```bash
docker-compose up -d redis
```

Ou manualmente se já tiver o Redis instalado.

### 5. Execute a aplicação

```bash
python main.py
```

## Acesso

Após iniciar, acesse o mapa em:

```
http://localhost:8083
```

## Estrutura do Projeto

```
├── main.py                 # Ponto de entrada principal
├── cloudflare/             # Integração com API da Cloudflare
│   └── get_infos.py
├── frontend/               # Interface web do mapa
│   ├── server.py           # Servidor web
│   ├── index.html
│   └── static/
│       ├── map.js          # Lógica do mapa Leaflet
│       └── websocket.js    # Conexão WebSocket
├── redis_handler/          # Gerenciamento do Redis
│   └── data_push.py
├── ws_mngr/                # Gerenciador de WebSocket
│   └── ws_manager.py
└── utils/                  # Utilitários
    ├── logger.py
    └── requests.py
```

## Funcionalidades

- 🗺️ Mapa interativo com visualização de ataques em tempo real
- 📊 Dashboard com estatísticas de IPs, países e hosts
- 🔴 Animações de tráfego malicioso no mapa
- 🌍 Suporte a múltiplas zonas Cloudflare simultaneamente

## Configuração do Token Cloudflare

O token da API precisa das seguintes permissões:

- `Zone:Logs:Read` - Para acessar os Instant Logs
- `Zone:Zone:Read` - Para listar as zonas

## Licença

MIT
