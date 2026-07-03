# LOPs — Exponer un tool_manager a clientes MCP externos

> Patrón para hacer que un `tool_manager` + `Any` de TD sea alcanzable desde
> cualquier cliente MCP fuera de tu red local (ChatGPT, y en teoría cualquier
> otro cliente que soporte MCP remoto) — no solo Claude Desktop en LAN.
>
> Ver también: `lops_snippets.md` (patrón Any + tools dedicadas),
> `lops_pitfalls.md` (parche del `_dispatcher`, sync de Tool Toggle).
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

## 4. Autenticación — estado actual del operador y cómo añadirla si hace falta

**Verificado por inspección directa del código**, no por ausencia de
parámetros en la UI: revisando el texto completo de `td_mcp_adapter` y
`ToolMCPBridgeEXT` (los DATs que implementan el puente MCP del
`tool_manager`), no hay ninguna mención a `oauth`, `bearer`,
`authorization`, `api_key` ni manejo de `401`/`WWW-Authenticate` en todo el
código. El servidor acepta cualquier request en el puerto configurado sin
comprobar credenciales.

**Esto es el estado de esta implementación concreta — no una limitación del
protocolo MCP ni algo intrínsecamente imposible de resolver.** MCP soporta
auth (OAuth 2.1, tokens, headers custom) perfectamente bien; el `tool_manager`
de dotsimulate, tal como viene, simplemente no la implementa todavía. Nada
impide construirla si hace falta:

- **Proxy delante del puerto** (Caddy/nginx con 2-3 líneas de config) que
  exija un header o token compartido antes de reenviar al `tool_manager`.
  Es la opción más rápida de montar y no toca el código de dotsimulate.
- **Extender `ToolMCPBridgeEXT`** para validar una cabecera `Authorization`
  antes de despachar cualquier tool call. Más integrado, pero requiere tocar
  el código del operador — no se ha hecho todavía en ningún proyecto de este
  repo.

**Al conectar un cliente externo que sí soporta auth (ChatGPT Developer
Mode, por ejemplo), si el `tool_manager` no la implementa, hay que elegir
"Sin autenticación" en el cliente — no porque sea imposible tener auth, sino
porque hasta que se construya (proxy o extensión del bridge) no hay nada al
otro lado que la responda.** Si el cliente exige OAuth y el servidor no lo
implementa, el descubrimiento OAuth falla antes de listar las tools.

## 5. Conectar desde un cliente externo (ejemplo: ChatGPT)

ChatGPT requiere plan Plus/Pro/Business/Enterprise/Edu y activar Developer
Mode (Settings → Apps → Advanced settings). Ahí, añadir la URL del paso 3
(`.../mcp`) como servidor MCP custom, autenticación "Sin autenticación" (o
lo que corresponda si has montado un proxy con auth), revisar las tools que
detecta, y activarlas.

## 6. Apagar tras la prueba

El `tool_manager` no tiene rate limiting ni logging de acceso más allá del
log estándar del operador. Sin auth añadida, cualquiera con la URL de
Funnel tiene el mismo acceso que el cliente autorizado mientras el túnel
esté activo. Tratar Funnel como algo que se enciende para la sesión de
prueba y se apaga después, no como infraestructura siempre activa —
especialmente si alguna tool de escritura queda encendida por descuido.

```powershell
tailscale funnel <puerto> off
```
