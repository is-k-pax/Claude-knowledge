# POPX — Router

POPX es una familia de operadores GPU para TouchDesigner (extensión de POPs).
Doc oficial: https://popx.tools/docs
Instalación: arrastrar POPX.tox al proyecto. Requiere Patreon tier Advanced.

---

## Qué documento leer según la situación

| Situación | Lee |
|---|---|
| Qué operadores existen y para qué | td_popx_catalog.md |
| Construir una red POPX desde cero | td_popx_catalog.md → td_popx_workflows.md |
| Flow, Soft Body, Particle, Physarum, DLA/DLG | td_popx_simulations.md |
| Algo no funciona / comportamiento inesperado | td_popx_pitfalls.md |
| Patrones aprendidos de los ejemplos oficiales | td_popx_workflows.md |

---

## Concepto clave que toda instancia debe saber antes de empezar

POPX Geometry es geometría **packed**: cada punto lleva P + Rotación + Escala + Pivot.
Las transformaciones ocurren en GPU sin salir de la familia POP.
Cadena típica: `Generator → Falloff → Modifier → Tool (Geo/Material) → Render TOP`

Las **simulaciones** (Flow, Soft Body, Particle, Physarum, DLA, DLG, SA, Mesh Fill)
son independientes del resto del sistema y tienen sus propios controles
`Initialize → Start → Play / Step`.
