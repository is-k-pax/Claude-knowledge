# Convenciones del repo

## Nombrado de archivos

- Minúsculas, guiones bajos: `lops_mcp_setup.md`
- Descriptivos y específicos: `glsl_feedback_loops.md` mejor que `glsl_tips.md`
- Sin fechas en el nombre (la fecha va en el header del documento)

## Estructura de cada documento

```markdown
# Título descriptivo

Descripción de una línea de qué cubre este doc.

**Origen:** de dónde viene este conocimiento  
**Última revisión:** mes año

---

## Secciones...
```

## Mensajes de commit

Formato: `[carpeta] acción breve`

Ejemplos:
- `[touchdesigner] añade sección sobre Tool VFS`
- `[shaders] nuevo doc glsl_feedback_loops`
- `[meta] actualiza índice README`

## Cuándo crear un doc nuevo vs añadir a uno existente

- **Añadir:** el conocimiento nuevo es una extensión natural del doc existente (nuevo pitfall, nuevo snippet)
- **Nuevo doc:** el tema es suficientemente distinto como para buscarlo por separado
