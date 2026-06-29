# POPX — Simulaciones

Las simulaciones POPX son **independientes** del sistema Generator→Falloff→Modifier.
Tienen sus propios controles: `Initialize → Start → Play / Step`
Si una sim se comporta mal: siempre **Initialize primero**.

---

## Flow (Navier-Stokes)

Resuelve flujo incompresible en GPU. Grid volumétrico con velocidad y densidad como texturas 3D.  
Para humo, fuego, efectos atmosféricos.

**Modos:**
- `Simple` — el solver calcula velocidad/densidad. Un **Particle POP nativo** externo gestiona emisión e integración
- `Advect` — el solver advecta sus propias partículas. Requiere feedback loop via `Target Particles Update POP`

**Params clave:**

| Param | Para qué |
|---|---|
| Viscosity | Grosor del fluido (0 = aire) |
| Vorticity | Intensidad de turbulencia/espiral |
| Pressure Iterations | Precisión de incompressibilidad |
| Velocity Dissipation | Decaimiento del campo de velocidad |
| Substance Dissipation | Decaimiento de densidad (humo que desaparece) |
| Buoyancy | Flotación (humo que sube) |

**Workflow modo Simple (más común):**
```
Sphere POP (emisor) → Flow (Simple) ← Particle POP nativo (integra velocity field)
                                     → Trail POP → Render
```
El Particle POP nativo lee el velocity field del Flow y mueve las partículas.

**Workflow modo Advect:**
```
Point POP (seeds) → Flow (Advect) → [proc. opcional] → (feedback → input Flow)
```
`Target Particles Update POP` apunta al nodo de vuelta. Sin esto: no hay movimiento.

**Flow también puede advectar line strips** (no solo puntos):
```
Grid POP (plano de line strips) → Flow (Advect page: Target Particle Update ON)
→ LineSmooth → LineResample
```

---

## Particle (SPH / PBF / Grains)

**Arquitectura híbrida — clave:**
- `Particle POP nativo de TD` = emisión, edad, muerte, integración
- `POPX Particle` = física (densidad, presión, colisión)
- Los dos trabajan juntos, no se reemplazan

**Modos:**

| Modo | Para qué | Params clave |
|---|---|---|
| Fluids-SPH | Líquidos tipo agua | target density, pressure multiplier, near pressure |
| Fluids-PBF | Fluidos más estables | viscosity, cohesion, surface tension, adhesion |
| Grains | Arena, granulados | repulsion weight, attraction weight |

**Colisiones disponibles:** ground plane · bounding box · POP geometry · volumen container · textura 2D/3D

**Colisión interactiva con mouse (texture painting):**
```
Panel CHOP → Circle TOP → Feedback TOP → Threshold TOP → Collision TOP 2D del POPX Particle
```
El Feedback TOP acumula los círculos — sin él desaparecen cada frame.

---

## Soft Body + Constraints + SBPP

Sistema XPBD sobre mesh deformable. Las constraints definen el comportamiento estructural.

**Inputs del Soft Body:**
- Input 0: geometría a deformar
- Input 1: constraints (POP de primitivas generado por el op Constraints)
- Input 2: geometría de colisión (opcional)

**Tipos de constraint:**

| Tipo | Para qué |
|---|---|
| Distance (along edge) | Evita que el mesh se estire. Esencial para cloth |
| Bend (across triangles) | Resistencia al doblado |
| Pin to target | Ancla puntos a posiciones fijas o animadas |
| Attach to geometry | Ancla puntos a la superficie de otro POP |
| Cloth | Distance + Bend combinados para tela |
| Strut (volumetric) | Cruza el interior para mantener volumen |
| Pressure | Presión interna para inflado |

**Constraint Property** — define por tipo: Compliance (0=rígido) · Damping · Force Limit · Break Threshold

**Workflow cloth básico:**
```
Grid POP → Group POP (esquinas) → Constraints (pin-to-target, esquinas) ──┐
                                 → Constraints (cloth)                    ─┤→ Soft Body
                                                                           ─┘
```
Grabber interactivo: `Panel CHOP → Math → Grab Position del Soft Body`

**Workflow inflate:**
```
Mesh POP → Constraints (cloth) ──────────────────┐
         → Constraints (strut) ──────────────────┤→ Merge → Soft Body → SBPP
         → Infection Falloff → Noise Falloff ────┘
```

**SBPP (Soft Body Post Process):**  
Recibe outputs 0 y 1 del Soft Body. Smooth + Visualize Stretch Stress (azul=sin tensión, rojo=máximo) + Compute Normals.

**Variantes vistas en ejemplos:**
- `soft_body_cloth` — tela interactiva con Grabber + mouse
- `soft_body_inflate` — globo con struts + pressure
- `soft_body_self_collision` — múltiples cuerpos colisionando entre sí (Enable Self Collision)
- `soft_body_strings` — cuerdas sobre skeleton FBX animado via SkinDeform POP
- `soft_body_simple_collision` — colisión con esfera SDF interna al solver

---

## Physarum

Simula el moho Physarum polycephalum. Agentes siguen rastros de feromonas.  
Opera en 2D o 3D.

**Inputs:** POP (seeds) · TOP opcional (constraint volume)  
**Outputs:** Particles (POP) · Trail (TOP) · Deposit (TOP)

**Feedback obligatorio:** `Target Particles Update POP` + `Target Trail Update TOP` apuntando aguas abajo.

**Constraint Volume:** TOP blanco/negro. Blanco = zona permitida, negro = bloqueado.  
Setup mínimo 2D: `PointGen → Physarum + Circle TOP → PointSprite`

---

## DLA — Diffusion-Limited Aggregation

Partículas random walkers que se adhieren formando estructuras (coral, cristal, rayos).  
Input: POP de seeds. Outputs: Points · Lines · Random Walkers.  
Params: search distance · attach distance · attach strength.

## DLG — Differential Line Growth

Line strips que crecen subdividiendo y empujando puntos outward.  
**Input: line strips** (no puntos sueltos).  
Collision shape como boundary para limitar crecimiento.

## Mesh Fill

Seeds que generan trails orgánicos que llenan progresivamente el interior de un mesh.  
```
FileIn POP → Sprinkle POP (seeds) → Mesh Fill → LineSmooth
```

## SA — Strange Attractors

Sistemas caóticos: Lorenz, Thomas, Aizawa, custom equations.  
`MathMix POP` para escalar instancias según velocidad (vel. alta = instancia grande).

## Shortest Path

Calcula caminos mínimos entre puntos en una red de geometría.
