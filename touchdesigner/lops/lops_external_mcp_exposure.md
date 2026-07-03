# LOPs — Exponer un tool_manager a clientes MCP externos

> Patrón para hacer que un `tool_manager` + `Any` de TD sea alcanzable desde
> cualquier cliente MCP fuera de tu red local (ChatGPT, y en teoría cualquier
> otro cliente que soporte MCP remoto) — no solo Claude Desktop en LAN.
>
> Ver también: `lops_snippets.md` (patrón Any + tools dedicadas),
> `lops_pitfalls.md` (parche del `_dispatcher`, sync de Tool Toggle, riesgo
> de auto-bloqueo al testear el propio servidor desde dentro de TD).
>
> Última revisión: julio 2026.

---

## Por qué esto es distinto de "configurar el Tool Manager para Claude Desktop"

`lops_tool_manager.md` cubre el caso de un container de desarrollo en LAN,
pensado para que Claude Desktop lo alcance en la misma red. Esto es un caso
distinto: **exposición pública a internet**, para interoperar con clientes
MCP de otros proveedores. Cambia la superficie de riesgo (cualquiera con la
URL puede llegar, no solo dispositivos de tu red) y hace falta pensar en dos
cosas que en LAN no importan tanto: qué tools quedan expuestas, y quién puede
invocarlas.

---

## 1. Construir el tool_manager con tools curadas

Ver `lops_snippets.md` → "Crear tools dedicadas con el operador Any". Un
`tool_manager` propio (puerto dedicado, no el de desarrollo) con un `Any`
cuyo módulo expone solo las funciones que quieres hacer disponibles
externamente — no reutilices el tool_manager de desarrollo (18766) para esto,
crea uno nuevo.

## 2. Filtrar qué tools quedan expuestas — la página "Tool Toggle"

El `tool_manager` genera automáticamente una página de parámetros **Tool
Toggle** con un switch booleano por cada tool detectada en el `Any`
conectado (`Enable<nombretool>`). Antes de exponer nada a internet, apaga
las tools que:
- Tengan efecto físico (controlar hardware, luces, actuadores)
- Tengan coste de cómputo o dinero (generación de imagen, llamadas a APIs de pago)
- Escriban datos persistentes que no quieras que un cliente externo toque

Deja encendidas solo las de lectura.

```python
tm = op('/ruta/tool_manager')
tm.par.Enablegivahgenerarimagen = False   # escritura/coste → off
tm.par.Enablegivahcontexto = True         # lectura → on
```

**⚠️ Tras cambiar qué tools expone el `Any` (añadir/quitar del módulo), la
página Tool Toggle no se resincroniza solo con `Refreshtools.pulse()` — hace
falta también `Restartserver.pulse()` para que aparezcan los switches de las
tools nuevas.** Ver detalle en `lops_pitfalls.md`.

## 3. Exponer el puerto con Tailscale Funnel

Requiere tener Tailscale instalado y HTTPS habilitado en el tailnet (Admin
console → DNS → HTTPS Certificates).

```powershell
tailscale funnel --bg <puerto>
```

La primera vez, si el tailnet no tiene el atributo `funnel` habilitado, el
propio comando te da un link de consentimiento web — lo sigues una vez y
queda resuelto. No hace falta editar el ACL a mano salvo que quieras
restringir por tag/usuario.

```powershell
tailscale funnel status          # ver URL pública activa
tailscale funnel <puerto> off    # apagar cuando termines
```

La URL resultante es `https://<maquina>.<tailnet>.ts.net` — el
`tool_manager` de dotsimulate sirve su endpoint MCP en el path `/mcp`, así
que la URL completa a dar al cliente externo es
`https://<maquina>.<tailnet>.ts.net/mcp`.

**Importante:** Tailscale Funnel es distinto de Tailscale Serve. Serve solo
deja pasar tráfico de dispositivos dentro de tu tailnet (privado). Funnel
expone el puerto a cualquiera en internet, sin necesidad de cuenta Tailscale
del otro lado — es equivalente a ngrok, con mejor infraestructura si ya usas
Tailscale.

**No confundir con Tailscale App Connectors** (pestaña "Apps" del panel).
Van en la dirección contraria: sirven para que dispositivos *dentro* de tu
tailnet salgan hacia SaaS externos (Salesforce, GitHub...) por una IP fija,
no para dejar entrar a un cliente externo hacia un servicio tuyo. Tampoco
ayudan aquí las Access Controls / ACLs del panel — gobiernan tráfico entre
miembros del tailnet, y Funnel existe precisamente para saltarse esa
frontera y servir a cualquiera en internet.

## 4. Autenticación — patrón validado: middleware de token compartido

**Confirmado por inspección de código y por el propio doc oficial de
dotsimulate** (páginas `Config` de `Tool Manager` y de `MCP Server`, el
operador hermano basado en FastMCP): ninguno de los dos trae parámetro de
auth. El `tool_manager`, tal como viene, acepta cualquier request en el
puerto configurado sin comprobar nada. Esto es el estado de esta
implementación concreta, no una limitación del protocolo MCP — MCP soporta
auth perfectamente bien (OAuth 2.1, tokens, headers), dotsimulate
simplemente no la ha implementado todavía en ninguno de sus dos operadores
de servidor MCP.

**Patrón probado end-to-end** (peticiones sin token → 401; con token
correcto por query param o por cabecera `Authorization` → 200): el
`tool_manager` sirve su endpoint sobre `aiohttp` puro (no `webserverDAT` de
TD). El DAT `td_mcp_adapter` construye el `web.Application()` en un método
`create_http_app()` que ya registra un middleware de CORS — es el punto de
enganche correcto para añadir uno de autenticación, sin tocar la lógica de
despacho de tools.

Localizar el bloque (dentro del `Any`/`tool_manager` ya clonado, **no** en
el operador fuente de `/dot_lops`):

```python
adapter_dat = op('/ruta/tool_manager/td_mcp_adapter')
```

Insertar el middleware justo antes de `app.middlewares.append(add_cors_headers)`
/ `return app`, dentro de `create_http_app()`:

```python
        # --- Shared-secret auth ---
        # Vacio = sin bloquear (modo abierto). Con texto = exige ese token
        # via 'Authorization: Bearer <token>' o via query param '?token=<token>'
        # (compatible con clientes que solo permiten pegar una URL simple,
        # como ChatGPT Developer Mode).
        AUTH_TOKEN = ""   # <-- rellenar con un secreto generado, nunca committear el valor real

        @web.middleware
        async def check_shared_token(request, handler):
            expected = AUTH_TOKEN.strip()
            if not expected:
                return await handler(request)
            supplied = request.query.get('token', '')
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                supplied = auth_header[7:]
            if supplied != expected:
                return web.json_response(
                    {"jsonrpc": "2.0", "id": None,
                     "error": {"code": -32001, "message": "Unauthorized: token invalido o ausente"}},
                    status=401
                )
            return await handler(request)

        app.middlewares.append(add_cors_headers)
        app.middlewares.append(check_shared_token)
        return app
```

Tras editar el texto del DAT, `Restartserver.pulse()` — `create_http_app()`
solo se ejecuta al arrancar el servidor, así que un `Refreshtools` no basta.

**Generar el token:**
```python
import secrets
token = secrets.token_urlsafe(20)
```

**Dar la URL al cliente externo con el token embebido** (mismo patrón que
usan servidores MCP reales como el de Xweather:
`https://mcp.api.xweather.com/mcp?api_key=...`):
```
https://<maquina>.<tailnet>.ts.net/mcp?token=<el_token_generado>
```

En ChatGPT Developer Mode, "Autenticación" sigue siendo **"Sin
autenticación"** — el token no es un flujo OAuth, va camuflado en la propia
URL del servidor, así que el cliente lo manda automáticamente en cada
petición sin que nadie tenga que reintroducirlo.

**Qué protege y qué no protege este patrón:** sube muchísimo la barrera de
entrada (adivinar una URL de Funnel + una cadena aleatoria es
inviable en la práctica) pero sigue siendo un secreto compartido, no
identidad real — el servidor no sabe *quién* hizo cada llamada, solo que
llevaba el secreto correcto. Para eso hace falta OAuth de verdad (ver más
abajo). Para un prototipo o demo puntual, es la relación
esfuerzo/protección correcta.

**Opciones más allá de esto, si algún día hace falta identidad real:**
- **Proxy delante del puerto** (Caddy/nginx) — misma idea que el middleware
  pero fuera del código de dotsimulate, útil si no quieres tocar el DAT.
- **OAuth real** — Tailscale mismo publicó un ejemplo de cómo construir un
  proveedor de identidad ligero (`tsidp`) combinando `tsnet` + Funnel +
  grants de capacidad de aplicación: exponen los endpoints públicos por
  Funnel pero mantienen `/authorize` accesible solo desde dentro del
  tailnet, así el login lo resuelve gratis la identidad de Tailscale. Es
  código propio (Go + `tsnet`), no un botón del panel — referencia útil si
  se aborda un Nivel 3 de verdad.

## 5. Conectar desde un cliente externo (ejemplo: ChatGPT)

ChatGPT requiere plan Plus/Pro/Business/Enterprise/Edu y activar Developer
Mode (Settings → Apps → Advanced settings). Ahí, añadir la URL del paso 3
(con `?token=...` si se implementó el paso 4) como servidor MCP custom,
autenticación "Sin autenticación", revisar las tools que detecta, y
activarlas.

## 6. Apagar tras la prueba

El `tool_manager` no tiene rate limiting ni logging de acceso más allá del
log estándar del operador. Sin el middleware de token, cualquiera con la URL
de Funnel tiene el mismo acceso que el cliente autorizado mientras el túnel
esté activo. Tratar Funnel como algo que se enciende para la sesión de
prueba y se apaga después, no como infraestructura siempre activa —
especialmente si alguna tool de escritura queda encendida por descuido.

```powershell
tailscale funnel <puerto> off
```
