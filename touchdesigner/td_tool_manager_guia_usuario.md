# Qué puede hacer Claude con el Tool Manager

Referencia rápida para saber qué pedirle a Claude cuando tiene el Tool Manager activo.

**Cuándo está activo:** cuando en Claude Desktop tienes el conector `touchdesigner-lop` activado y el proyecto TD tiene el container `/claude_desktop_tool_manager` corriendo.

---

## Lo que Claude puede hacer sin que le expliques nada

- **Ver tu proyecto en tiempo real:** navegar la red de nodos, leer parámetros, conexiones y errores de cualquier operador — sin que le cuentes nada
- **Ver qué estás tocando tú:** con `get_recent_activity` puede ver qué operadores estás seleccionando y qué parámetros estás cambiando en los últimos segundos
- **Hacerse una foto de la red:** captura visual del network editor tal como lo ves tú

---

## Lo que Claude puede crear y modificar en TD

- **Ejecutar Python dentro de TD** — puede crear operadores, modificar parámetros, disparar pulsos, lanzar procesos. Básicamente todo lo que puedes hacer desde el Textport, lo puede hacer él
- **Editar DATs con precisión quirúrgica** — puede abrir cualquier DAT (scripts Python, shaders GLSL, configs JSON), reemplazar un fragmento exacto, insertar líneas en una posición concreta, sin tocar el resto del archivo
- **Leer el contenido de cualquier DAT** — shaders, scripts, tablas, configuraciones

---

## Lo que Claude puede guardar entre sesiones

- **Sistema de archivos virtual (VFS)** dentro del container — puede guardar notas, documentación, configuraciones, código. Estos archivos viajan con el `.tox` y están disponibles en cualquier PC donde lleves el container
- **Ejemplo de uso:** "guarda un resumen de lo que hemos construido hoy para que lo puedas leer mañana"

---

## Lo que Claude puede buscar

- **Buscar en la web** (requiere Serper API key configurada) — puede buscar documentación, ejemplos, errores de TD o LOPs directamente durante la conversación sin salir de contexto

---

## Qué pedirle en la práctica

| Quieres | Dile |
|---|---|
| Que vea el estado de tu proyecto | "¿qué hay en mi proyecto?" o simplemente empieza a preguntar |
| Que cree un operador | "crea un noiseTOP en /project1 llamado ruido_fondo" |
| Que modifique un shader | "en el DAT glsl_pixel1 cambia el color de salida a rojo" |
| Que depure un error | "el operador X tiene un error, míralo" |
| Que documente algo | "guarda en el VFS un resumen de esta red para futuras sesiones" |
| Que busque doc de LOPs | "busca cómo funciona el Agent Swarm en docs.dotsimulate.com" |
| Que vea lo que estás tocando | "mira mi actividad reciente y dime qué estoy intentando hacer" (úsalo con moderación — pesa mucho en el contexto) |
| Que haga un screenshot | "hazme una foto de la red" (una vez, no repetidamente) |

---

## Lo que NO puede hacer (limitaciones reales)

- **No puede modificar parámetros directamente** sin pasar por código Python — no hay un botón mágico, lo hace via `td_code`
- **No recuerda sesiones anteriores** — cada chat nuevo empieza desde cero. El VFS y la repo de GitHub son su memoria entre sesiones
- **No puede conectar operadores visualmente** sin ejecutar código
- **Las tool calls con respuestas muy largas** (como `get_recent_activity`) pesan mucho en el contexto — úsalas con criterio, no repetidamente en la misma sesión
- **Los cambios que hace via MCP no disparan callbacks** en datexecuteDAT ni parameterexecuteDAT — esto es una limitación de TD, no del Tool Manager

---

## Cómo orientarle al inicio de una sesión nueva

Lo más eficiente es darle contexto en texto — es más barato que hacer que inspeccione el proyecto:

> "Tengo el Tool Manager activo. Estoy trabajando en /project1, hay un agente LOP llamado agent1 y quiero que me ayudes a..."

O si prefieres que lo descubra solo:

> "Mira el proyecto y dime qué hay"

---

## Nota sobre el coste

Cada sesión nueva con Tool Manager activo consume ~5.400 tokens solo de arranque (leer la repo + schemas de tools). No es caro, pero saberlo ayuda:
- Explicarle el contexto en texto es más eficiente que pedirle que lo descubra
- `get_recent_activity` y los screenshots pesan ~5.000 tokens cada llamada — úsalos una vez por sesión, no en bucle
- Las sesiones largas con muchas tool calls pesan más que abrir sesiones nuevas
