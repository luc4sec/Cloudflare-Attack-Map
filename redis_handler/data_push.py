import redis
import json
import random
import os
from datetime import datetime
from utils.logger import logE, logI

# Contadores globais
event_count = 1
ips_tracked = {}
ports = {}
ip_to_code = {}
countries_to_code = {}
countries_tracked = {}
continent_tracked = {}
hosts_tracked = {}

# Configuração Redis
redis_ip = os.environ.get('REDIS_IP', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_channel = os.environ.get('REDIS_CHANNEL', 'cloudflare_events')

# Instância Redis global (singleton)
_redis_instance = None

colors = [
    '#ff0000',
    '#ff8000',
    '#ffff00',
    '#80ff00',
    '#00ff00',
    '#00ff80',
    '#00ffff',
    '#0080ff',
    '#0000ff',
    '#8000ff',
    '#bf00ff',
    '#ff00ff',
    '#ff0060',
    '#ffccff',
    '#ffcccc',
    '#ffffff'
]


def init_redis():
    """Inicializa a conexão Redis. Deve ser chamada antes de iniciar os WebSockets."""
    global _redis_instance
    try:
        _redis_instance = redis.StrictRedis(
            host=redis_ip, 
            port=redis_port, 
            db=0,
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True
        )
        # Testa a conexão
        _redis_instance.ping()
        logI(f"Conexão Redis estabelecida com sucesso em {redis_ip}:{redis_port}")
        return True
    except redis.ConnectionError as e:
        logE(f"Falha ao conectar no Redis ({redis_ip}:{redis_port}): {e}")
        _redis_instance = None
        return False
    except Exception as e:
        logE(f"Erro inesperado ao conectar no Redis: {e}")
        _redis_instance = None
        return False


def get_redis_instance():
    """Retorna a instância Redis, reconectando se necessário."""
    global _redis_instance
    if _redis_instance is None:
        init_redis()
    else:
        try:
            _redis_instance.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            logI("Reconectando ao Redis...")
            init_redis()
    return _redis_instance


def is_redis_connected():
    """Verifica se o Redis está conectado."""
    try:
        instance = get_redis_instance()
        if instance:
            instance.ping()
            return True
    except:
        pass
    return False


def convert_cloudflare_timestamp(timestamp):
    """Converte EdgeStartTimestamp da Cloudflare para formato datetime legível.
    
    O EdgeStartTimestamp pode vir em diferentes formatos:
    - Unix timestamp em nanosegundos (ex: 1738656000000000000)
    - Unix timestamp em milissegundos (ex: 1738656000000)
    - ISO 8601 string (ex: 2026-02-04T12:00:00Z)
    """
    try:
        if timestamp is None:
            return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(timestamp, str):
            # Tenta parsear como ISO 8601
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Tenta converter string numérica para int
                timestamp = int(timestamp)
        
        if isinstance(timestamp, (int, float)):
            # Detecta se é nanosegundos, microsegundos, milissegundos ou segundos
            if timestamp > 1e18:  # Nanosegundos
                timestamp = timestamp / 1e9
            elif timestamp > 1e15:  # Microsegundos
                timestamp = timestamp / 1e6
            elif timestamp > 1e12:  # Milissegundos
                timestamp = timestamp / 1e3
            # Agora está em segundos
            dt = datetime.utcfromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logE(f"Erro ao converter timestamp {timestamp}: {e}")
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def process_cloudflare_data(data):
    try:
        client_ip = data.get('ClientIP')
        host = data.get('ClientRequestHost', 'unknown')
        
        alert = {
            "type": "Traffic",
            "honeypot": "Cloudflare",
            "country": data.get('ClientCity', "Unknown"),
            "country_code": data.get('ClientCountry', 'XX'),
            "iso_code": data.get('ClientCountry', 'XX'),
            "continent_code": data.get('ClientContinent', 'XX'),
            "latitude": float(data.get('ClientLatitude', 0)),  # Coordenadas da origem
            "longitude": float(data.get('ClientLongitude', 0)),
            "src_ip": client_ip,
            "dst_ip": host,
            "dst_port": 443,
            "src_port": 0,
            "protocol": "HTTPS",
            "event_time": convert_cloudflare_timestamp(data.get('EdgeStartTimestamp')),
            "color": random.choice(colors),
            "ip_rep": "Unknown",
            "dst_lat": -15.7801,
            "dst_long": -47.9292,
            "dst_iso_code": "BR",
            "dst_country_name": "Brazil",
            "event_count": 1,
            "ips_tracked": {},
            "countries_tracked": {},
            "continents_tracked": {},
            "ip_to_code": {},
            "country_to_code": {}
        }
        
        return alert
    except Exception as e:
        logE(f"Erro ao processar dados: {str(e)}")
        logE(f"Dados recebidos: {data}")
        return None


def push_honeypot_stats(honeypot_stats):
    """Envia estatísticas do honeypot para o Redis."""
    try:
        instance = get_redis_instance()
        if instance:
            tmp = json.dumps(honeypot_stats)
            instance.publish(redis_channel, tmp)
            return True
    except Exception as e:
        logE(f"Erro ao enviar honeypot stats: {e}")
    return False


def push(alerts):
    """Envia alertas para o Redis."""
    global ips_tracked, countries_tracked, ip_to_code, countries_to_code, hosts_tracked
    
    try:
        instance = get_redis_instance()
        if not instance:
            logE("Redis não está conectado. Alertas não serão enviados.")
            return False
        
        success_count = 0
        for alert in alerts:
            if not alert:
                continue

            # Atualizar contadores
            src_ip = alert.get("src_ip")
            dst_ip = alert.get("dst_ip")
            country = alert.get("country", "Unknown")
            iso_code = alert.get("iso_code", "XX")
            country_code = alert.get("country_code", "XX")
            
            if src_ip:
                ips_tracked[src_ip] = ips_tracked.get(src_ip, 0) + 1
                ip_to_code[src_ip] = iso_code
            
            if country:
                countries_tracked[country] = countries_tracked.get(country, 0) + 1
                countries_to_code[country] = country_code
            
            if dst_ip:
                hosts_tracked[dst_ip] = hosts_tracked.get(dst_ip, 0) + 1

            # Adicionar estatísticas de rastreamento ao alerta
            alert["ips_tracked"] = dict(ips_tracked)
            alert["countries_tracked"] = dict(countries_tracked)
            alert["hosts_tracked"] = dict(hosts_tracked)
            alert["ip_to_code"] = dict(ip_to_code)
            alert["country_to_code"] = dict(countries_to_code)

            try:
                instance.publish(redis_channel, json.dumps(alert))
                success_count += 1
            except redis.ConnectionError as e:
                logE(f"Conexão perdida ao publicar no Redis: {e}")
                # Tenta reconectar
                init_redis()
            except Exception as e:
                logE(f"Erro ao publicar no Redis: {e}")

        return success_count > 0
        
    except Exception as e:
        logE(f"Erro no push: {str(e)}")
        return False


def get_stats():
    """Retorna estatísticas atuais de tracking."""
    return {
        "ips_tracked": dict(ips_tracked),
        "countries_tracked": dict(countries_tracked),
        "hosts_tracked": dict(hosts_tracked),
        "ip_to_code": dict(ip_to_code),
        "countries_to_code": dict(countries_to_code),
        "total_ips": len(ips_tracked),
        "total_countries": len(countries_tracked),
        "total_hosts": len(hosts_tracked)
    }