# Convenciones del repo

Reglas de nombrado, estructura y commits para Claude-knowledge.

**Ultima revision:** junio 2026.

---

## Nombrado de archivos

- Prefijo por programa: `td_`, `resolume_`, `glsl_`, etc.
- Snake_case, sin espacios, sin mayusculas.
- Nombres descriptivos y buscables.

## Estructura

- Maximo 2 niveles de carpetas.
- Archivos < 10KB. Si crece mas, dividir.
- Un tema por archivo.

## Commits

Formato: `[carpeta] accion breve`

Ejemplos:
- `[touchdesigner] añade pitfall sobre timeout de MCP`
- `[general] actualiza mcp_troubleshooting`
- `[meta] crea conventions.md`

## Contenido

- Cero datos personales: sin nombres de usuario, rutas locales, tokens ni contraseñas.
- El repo es publico.
- Formato pitfall: Sintoma / Causa / Fix.
- Formato snippet: Cuando / Codigo minimo.
