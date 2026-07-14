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


def _reason(code):
    return {
        200: "OK", 204: "No Content", 400: "Bad Request",
        404: "Not Found", 500: "Internal Server Error",
    }.get(code, "OK")


def _fill(response, status, body, content_type="text/html; charset=utf-8"):
    response["statusCode"] = status
    response["statusReason"] = _reason(status)
    response["data"] = body
    response["Content-Type"] = content_type
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def onHTTPRequest(webServerDAT, request, response):
    try:
        method = (request.get("method") or "GET").upper()
        uri = request.get("uri") or "/"
        path = uri.split("?", 1)[0].rstrip("/") or "/"

        # Preflight CORS
        if method == "OPTIONS":
            return _fill(response, 204, "", "text/plain")

        # GET /, /form
        if method == "GET" and path in ("/", "/form", "/index.html"):
            html = op("../form_html").text
            return _fill(response, 200, html, "text/html; charset=utf-8")

        # GET /empresas
        if method == "GET" and path == "/empresas":
            try:
                empresas = _mod()._empresas_disponibles()
                return _fill(response, 200,
                             json.dumps({"ok": True, "empresas": empresas}),
                             "application/json; charset=utf-8")
            except Exception as e:
                return _fill(response, 200,
                             json.dumps({"ok": False, "error": str(e), "empresas": []}),
                             "application/json; charset=utf-8")

        # POST /submit
        if method == "POST" and path == "/submit":
            try:
                body = request.get("data", "")
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                payload = json.loads(body) if isinstance(body, str) and body else {}
                session_id, disk_path = _mod().iniciar_sesion_desde_formulario(payload)
                return _fill(response, 200,
                             json.dumps({"ok": True, "session_id": session_id, "path": disk_path}),
                             "application/json; charset=utf-8")
            except Exception as e:
                print("[sesion_tools/form] /submit error:", e)
                return _fill(response, 400,
                             json.dumps({"ok": False, "error": str(e)}),
                             "application/json; charset=utf-8")

        # GET /informe/<sid>
        if method == "GET" and path.startswith("/informe/"):
            sid = path[len("/informe/"):]
            sessions_dir = _mod()._sessions_dir()
            html_path = os.path.join(sessions_dir, sid + "_informe.html")
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    return _fill(response, 200, f.read(), "text/html; charset=utf-8")
            return _fill(response, 404,
                         "<h1>404</h1><p>No hay informe para " + sid + ".</p>",
                         "text/html; charset=utf-8")

        # Fallback
        return _fill(response, 404,
                     json.dumps({"ok": False, "error": "ruta desconocida: " + method + " " + path}),
                     "application/json; charset=utf-8")

    except Exception as e:
        print("[sesion_tools/form] excepcion no capturada:", e)
        return _fill(response, 500,
                     json.dumps({"ok": False, "error": str(e)}),
                     "application/json; charset=utf-8")


# WebSocket callbacks (no usados por ahora)

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
    print("[sesion_tools/form_server] arrancado en puerto", webServerDAT.par.port.eval())

def onServerStop(webServerDAT):
    print("[sesion_tools/form_server] detenido")
