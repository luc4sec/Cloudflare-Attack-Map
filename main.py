import os
import websocket
import time
import json
import threading
import sys

from dotenv import load_dotenv
load_dotenv()

from utils.logger import logE, logI
from cloudflare.get_infos import get_zones, get_cloudflare_ws_url, get_account_info
from ws_mngr.ws_manager import on_ws_close, on_ws_error
from redis_handler.data_push import init_redis, process_cloudflare_data, push
from frontend.server import start_web_server


try:
    CLOUDFLARE_ACCOUNT_ID = os.environ['CLOUDFLARE_ACCOUNT_ID']
except:
    logI("Variável de ambiente CLOUDFLARE_ACCOUNT_ID não definida. Buscando todas as contas.")
    CLOUDFLARE_ACCOUNT_ID = None

try:
    CLOUDFLARE_ZONE_NAMES = os.environ['CLOUDFLARE_ZONE_NAMES'].split(',')
    CLOUDFLARE_ZONE_NAMES = [name.strip() for name in CLOUDFLARE_ZONE_NAMES]
except:
    logI("Variável de ambiente CLOUDFLARE_ZONE_NAMES não definida. Buscando todas as zonas.")
    CLOUDFLARE_ZONE_NAMES = None

def attack_data_controller(zones):
    websockets = []
    threads = []
    
    for zone in zones:
        logI(f"Zona: {zone['name']} | ID: {zone['id']} | Plano: {zone['plan']}")
        ws_url = get_cloudflare_ws_url(zone['id'])
        if ws_url:
            logI(f"Iniciando logging de dados para zona {zone['name']}...")
            
            def create_on_open(zone_name):
                return lambda ws: logI(f"WebSocket conectado para zona {zone_name}")
            
            def create_on_message(zone_name):
                def on_message(ws, message):
                    try:
                        data = json.loads(message)
                        processed_data = process_cloudflare_data(data)
                        if processed_data:
                            processed_data['zone'] = zone_name
                            # Envia para o Redis
                            if not push([processed_data]):
                                logE(f"[{zone_name}] Falha ao enviar dados ao Redis")
                        else:
                            logE(f"[{zone_name}] Dados processados retornaram None")
                    except json.JSONDecodeError as e:
                        logE(f"[{zone_name}] Erro ao decodificar JSON: {e}")
                    except Exception as e:
                        logE(f"[{zone_name}] Erro ao receber mensagem: {str(e)}")
                return on_message
            
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=create_on_message(zone['name']),
                on_close=on_ws_close,
                on_error=on_ws_error,
                on_open=create_on_open(zone['name'])
            )
            websockets.append(ws)

            # Criar thread para cada WebSocket
            thread = threading.Thread(target=ws.run_forever, daemon=True)
            threads.append(thread)
        else:
            logE(f"Não foi possível obter o WebSocket URL para zona {zone['name']}")

    # Iniciar todas as threads
    for thread in threads:
        thread.start()

    logI(f"Todos os {len(threads)} WebSockets iniciados simultaneamente")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logI("Encerrando conexões WebSocket...")
        for ws in websockets:
            ws.close()


if __name__ == '__main__':

    try:
        logI("Iniciando conexão com Redis...")
        if not init_redis():
            logE("Falha ao conectar no Redis. Verifique as configurações.")
            sys.exit(1)
        
        logI("Buscando zonas da Cloudflare...")
        zones = []
        for account in get_account_info().get('result', []):
            if CLOUDFLARE_ACCOUNT_ID and account.get('id') != CLOUDFLARE_ACCOUNT_ID:
                continue
            
            for zone in get_zones(account.get('id')):
                if CLOUDFLARE_ZONE_NAMES:
                    if zone['name'] in CLOUDFLARE_ZONE_NAMES:
                        zones.append(zone)
                else:
                    zones.append(zone)

        if not zones:
            logE("Nenhuma zona encontrada.")
            sys.exit(1)
        
        logI(f"Zonas encontradas: {len(zones)}")
        
        start_web_server()
        
        attack_data_controller(zones)



        
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN')
        sys.exit(0)