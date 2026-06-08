# Claude-knowledge

Base de conocimiento acumulado trabajando con Claude en proyectos de audiovisual, generación de imagen, música y herramientas creativas.

**Mantenido por:** vuski / is-k-pax  
**Última revisión:** junio 2026

---

## Cómo usar este repo

Este repo está diseñado para ser leído por Claude al inicio de una sesión de trabajo. En cualquier conversación nueva, puedes compartir la URL raw de un archivo concreto y Claude lo leerá como contexto.

URL raw base: `https://raw.githubusercontent.com/is-k-pax/Claude-knowledge/main/`

Ejemplo:
```
https://raw.githubusercontent.com/is-k-pax/Claude-knowledge/main/touchdesigner/setups/lops_mcp_setup.md
```

---

## Estructura

```
Claude-knowledge/
├── touchdesigner/
│   ├── setups/        ← instalaciones, MCP, LOPs, configuraciones
│   ├── shaders/       ← conocimiento GLSL acumulado
│   ├── workflows/     ← pipelines y flujos de trabajo descubiertos
│   └── skills/        ← skills de Claude específicas para TD
├── resolume/
├── ableton/
├── comfyui/
├── general/
└── meta/
```

---

## Índice de documentos

### TouchDesigner
| Archivo | Descripción |
|---|---|
| [touchdesigner/setups/lops_mcp_setup.md](touchdesigner/setups/lops_mcp_setup.md) | Comunicación Claude ↔ TD via LOPs (dotsimulate) — guía completa |

### Meta
| Archivo | Descripción |
|---|---|
| [meta/how_to_use_with_claude.md](meta/how_to_use_with_claude.md) | Instrucciones para onboard de Claude con este repo |
| [meta/conventions.md](meta/conventions.md) | Convenciones de nombrado y estructura |
