#!/usr/bin/python3

"""
Original code (tornado based) by Matthew May - mcmay.web@gmail.com
Adjusted code for asyncio, aiohttp and redis (asynchronous support) by t3chn0m4g3
"""

import asyncio
import json
import os

import redis.asyncio as redis
from aiohttp import web

# Diretório base do frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# redis_url = 'redis://10.1.10.69:6379'
redis_url = f'redis://{os.environ.get("REDIS_IP", "localhost")}:6379'
web_port = 8083
version = os.getenv('VERSION', '1.0.0')
channel = os.environ.get('REDIS_CHANNEL', 'cf_attack_map')

async def redis_subscriber(websockets):
    while True:
        try:
            print("[DEBUG] Conectando ao Redis...")
            r = redis.Redis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(channel)
            print(f"[DEBUG] Inscrito no canal Redis: {channel}")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    try:
                        data = message['data']
                        
                        # Garantir que os dados sejam JSON válido
                        if isinstance(data, str):
                            json_data = data
                            # Validar se é JSON válido
                            json.loads(data)
                        else:
                            json_data = json.dumps(data)
                        
                        if len(websockets) > 0:
                            await asyncio.gather(*[ws.send_str(json_data) for ws in websockets])
                        # Removido warning de nenhum cliente - é esperado quando ninguém está conectado
                    except Exception as e:
                        print(f"[ERROR] Erro ao processar mensagem: {e}")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Erro na conexão Redis: {e}")
            await asyncio.sleep(5)

async def my_websocket_handler(request):
    ws = web.WebSocketResponse(heartbeat=30)  # Adiciona heartbeat para manter conexão
    await ws.prepare(request)
    
    print(f"[DEBUG] Nova conexão WebSocket de {request.remote}")
    request.app['websockets'].append(ws)
    print(f"[INFO] Clientes WebSocket ativos: {len(request.app['websockets'])}")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # print(f"[DEBUG] Mensagem recebida do cliente: {msg.data[:200]}")
                await ws.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"[ERROR] Erro WebSocket de {request.remote}: {ws.exception()}")
    finally:
        request.app['websockets'].remove(ws)
        print(f"[INFO] Cliente {request.remote} desconectado. Clientes ativos: {len(request.app['websockets'])}")
    return ws

async def my_index_handler(request):
    return web.FileResponse(os.path.join(BASE_DIR, 'index.html'))

async def start_background_tasks(app):
    app['websockets'] = []
    app['redis_subscriber'] = asyncio.create_task(redis_subscriber(app['websockets']))

async def cleanup_background_tasks(app):
    app['redis_subscriber'].cancel()
    await app['redis_subscriber']

async def make_webapp():
    app = web.Application()
    
    # Inicializar a lista de websockets
    app['websockets'] = []
    
    # Configurar CORS e cabeçalhos de segurança
    async def security_middleware(app, handler):
        async def middleware_handler(request):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        return middleware_handler

    # Adicionar middleware e rotas
    app.middlewares.append(security_middleware)
    app.router.add_routes([
        web.get('/', my_index_handler),
        web.get('/websocket', my_websocket_handler),
        web.static('/static/', os.path.join(BASE_DIR, 'static')),
        web.static('/images/', os.path.join(BASE_DIR, 'static/images')),
        web.static('/flags/', os.path.join(BASE_DIR, 'static/flags'))
    ])

    # Configurar eventos de inicialização e limpeza
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    return app


def start_web_server():
    """Inicia o servidor web em uma thread separada."""
    import threading
    from aiohttp.web import AppRunner, TCPSite
    
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            app = loop.run_until_complete(make_webapp())
            runner = AppRunner(app)
            loop.run_until_complete(runner.setup())
            site = TCPSite(runner, '0.0.0.0', web_port)
            loop.run_until_complete(site.start())
            print(f"[WEB] Servidor rodando em http://0.0.0.0:{web_port}")
            loop.run_forever()
        except Exception as e:
            print(f"[ERROR] Erro no servidor web: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"[INFO] Servidor web iniciado na porta {web_port}")
    return thread