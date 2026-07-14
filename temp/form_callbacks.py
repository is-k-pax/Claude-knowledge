# form_callbacks - webserverDAT del sesion_tools
#
# Rutas:
#   GET  /                -> form_html (formulario iPad)
#   GET  /form            -> form_html
#   GET  /empresas        -> {ok, empresas: [...]} desde el catalogo local
#   POST /submit          -> payload -> mod.iniciar_sesion_desde_formulario()
#   GET  /informe/<sid>   -> HTML del informe (si existe en sessions/<sid>_informe.html)

import json
import os


def _mod():
    return op("../module").module


def _cors(response):
    response["headers"]["Access-Control-Allow-Origin"] = "*"
    response["headers"]["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["headers"]["Access-Control-Allow-Headers"] = "Content-Type"


def _json(response, code, obj):
    response["statusCode"] = code
    response["statusReason"] = "OK" if code == 200 else "Error"
    response["data"] = json.dumps(obj, ensure_ascii=False)
    response["headers"]["Content-Type"] = "application/json; charset=utf-8"
    _cors(response)


def _html(response, code, text):
    response["statusCode"] = code
    response["statusReason"] = "OK" if code == 200 else "Error"
    response["data"] = text
    response["headers"]["Content-Type"] = "text/html; charset=utf-8"
    _cors(response)


def onHTTPRequest(webServerDAT, request, response):
    method = (request.get("method") or "GET").upper()
    uri = request.get("uri") or "/"
    path = uri.split("?", 1)[0].rstrip("/") or "/"

    # Preflight CORS
    if method == "OPTIONS":
        response["statusCode"] = 204
        _cors(response)
        return response

    # GET /, /form
    if method == "GET" and path in ("/", "/form"):
        html = op("../form_html").text
        _html(response, 200, html)
        return response

    # GET /empresas
    if method == "GET" and path == "/empresas":
        try:
            empresas = _mod()._empresas_disponibles()
            _json(response, 200, {"ok": True, "empresas": empresas})
        except Exception as e:
            _json(response, 500, {"ok": False, "error": str(e)})
        return response

    # POST /submit
    if method == "POST" and path == "/submit":
        try:
            body = request.get("data") or "{}"
            payload = json.loads(body) if isinstance(body, str) else body
            session_id, disk_path = _mod().iniciar_sesion_desde_formulario(payload)
            _json(response, 200, {
                "ok": True,
                "session_id": session_id,
                "path": disk_path,
            })
        except Exception as e:
            _json(response, 400, {"ok": False, "error": str(e)})
        return response

    # GET /informe/<sid>
    if method == "GET" and path.startswith("/informe/"):
        sid = path[len("/informe/"):]
        sessions_dir = _mod()._sessions_dir()
        html_path = os.path.join(sessions_dir, sid + "_informe.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                _html(response, 200, f.read())
        else:
            _html(response, 404, "<h1>404</h1><p>No hay informe para " + sid + ".</p>")
        return response

    # Fallback
    _json(response, 404, {"ok": False, "error": "ruta desconocida: " + method + " " + path})
    return response


# WebSocket callbacks (definidos para evitar errores; no se usan por ahora)

def onWebSocketOpen(webServerDAT, client, uri):
    return

def onWebSocketClose(webServerDAT, client):
    return

def onWebSocketReceiveText(webServerDAT, client, data):
    return

def onWebSocketReceiveBinary(webServerDAT, client, data):
    return

def onWebSocketReceivePing(webServerDAT, client, data):
    return

def onServerStart(webServerDAT):
    debug("[sesion_tools/form_server] arrancado en puerto " + str(webServerDAT.par.port.eval()))

def onServerStop(webServerDAT):
    return
