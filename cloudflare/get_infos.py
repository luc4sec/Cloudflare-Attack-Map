from utils.requests import http_request2
from utils.logger import logE, logI

def get_account_info():
    res = http_request2(
        method="GET",
        endpoint=f"/accounts",
        params={
            "per_page": 1000,
            "page": 1
        }
    )
    if res.status_code != 200:
        logE(f"Erro ao buscar nome da conta: {res.status_code} - {res.text}")
    return res.json()

def get_zones(account_id):
    params = {
        # "status": "active",
        "per_page": 1000,
        "page": 1,
        "order": "plan.id"
    }
    
    if account_id:
        params["account.id"] = account_id        

    res = http_request2(
        method="GET",
        endpoint="/zones",
        params=params
    )
    if res.status_code != 200:
        logE(f"Erro ao buscar zonas: {res.status_code} - {res.text}")
    zones_id = []

    res = res.json()
    for zone in res.get('result', []):
        # if "Enterprise" in zone.get('plan').get('name'):
        zones_id.append({"name": zone.get('name'), "id": zone.get('id') , "plan": zone.get('plan').get('name')})

    return zones_id

def get_cloudflare_ws_url(zone_id):
    body = {
        "fields": "ClientIP,ClientRequestHost,ClientRequestMethod,ClientRequestURI,EdgeResponseStatus,EdgeStartTimestamp,ClientLatitude,ClientLongitude,ClientCountry,ClientCity",
        "sample": 1,
        "filter": "{\"where\":{\"and\":[{\"key\":\"EdgeResponseStatus\",\"operator\":\"eq\",\"value\":403}]}}",
        "kind": "instant-logs"
    }

    try:
        res = http_request2(
            method="POST",
            endpoint=f"/zones/{zone_id}/logpush/edge/jobs",
            data=body
        )

        response_json = res.json()
        
        if response_json['success'] and response_json['result']:
            logI(f"WebSocket URL obtido com sucesso para conta {zone_id}")
            return response_json['result']['destination_conf']
        else:
            error_msg = response_json.get('errors', [{'message': 'Unknown error'}])[0]['message']
            logE(f"Falha ao obter WebSocket URL para zona {zone_id}: {error_msg}")
            return None
            
    except Exception as e:
        logE(f"Exceção ao obter WebSocket URL para zona {zone_id}: {str(e)}")
        return None