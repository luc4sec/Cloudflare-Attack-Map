import json
import time
import ws_mngr


def on_ws_close(ws, close_status_code, close_msg):
    print(f"[WARNING] WebSocket fechado: {close_status_code} - {close_msg}")
    # ws_retry_connection(ws)

def on_ws_error(ws, error):
    print(f"[ERROR] Erro no WebSocket: {error}")
    # ws_retry_connection(ws)

def ws_retry_connection(ws, max_retries=5, initial_delay=1):
    """Tenta reconectar ao WebSocket com backoff exponencial"""
    retry_count = 0
    delay = initial_delay
    
    while retry_count < max_retries:
        try:
            print(f"[INFO] Tentativa de reconexão {retry_count + 1}/{max_retries} após {delay} segundos...")
            time.sleep(delay)
            ws.run_forever()
            return  # Se conseguir conectar, sai da função
        except Exception as e:
            print(f"[ERROR] Falha na reconexão: {e}")
            retry_count += 1
            delay *= 2  # Backoff exponencial

def on_ws_message(ws, message):
    try:
        # print(f"[DEBUG] Mensagem WebSocket recebida: {message}...") #{message[:200]}
        data = json.loads(message)
        print(json.dumps(data, indent=4))
        # processed_data = process_cloudflare_data(data)
        # if processed_data:
        #     # print("[DEBUG] Enviando dados processados para push()")
        #     push([processed_data])
        # else:
        #     print("[WARNING] Dados processados retornaram None")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Erro ao decodificar JSON: {e}")
    except Exception as e:
        print(f"[ERROR] Erro ao receber mensagem: {str(e)}")
