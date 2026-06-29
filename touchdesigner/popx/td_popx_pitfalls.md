# POPX — Pitfalls

---

## Generators

**Convert no calcula orientación local**  
Síntoma: instancias sin eje local correcto, Transform Modifier en Local Space no funciona bien.  
Fix: añadir **Reorient** después de Convert.

**Explode vs Convert**  
- Explode: para fragmentar meshes por cara. Calcula normal/up automáticamente.  
- Convert: para convertir por conectividad o piece attribute. No calcula orientación.

**Instancer: Copy to Points vs GPU Instancing**  
- Copy to Points: geometría realizada, puede ser modificada por Modifiers. Más lento.  
- GPU Instancing: muy rápido, pero los Modifiers no pueden deformar la geometría per-instancia.

---

## Falloffs

**Múltiples falloffs afectando al mismo Modifier**  
Síntoma: solo uno de los falloffs tiene efecto.  
Fix: cambiar `Output Falloff Attribute` en cada Falloff op para que tengan nombres distintos (`falloff_noise`, `falloff_shape`...). Seleccionar el correcto en `Falloff Attribute` del Modifier.

**Infection Falloff que no propaga**  
Síntoma: el falloff aparece estático.  
Fix: necesita `Play` activado o pulsar `Start`. Funciona como una simulación.

---

## Modifiers

**Transform Modifier en Local Space no mueve en la dirección esperada**  
Síntoma: las instancias se mueven en world space aunque Local Space esté ON.  
Causa: las instancias no tienen orientación local definida.  
Fix: usar Explode (calcula normal/up) o Reorient antes del Transform Modifier.

**Spring Modifier no reactivo**  
Síntoma: las instancias no rebotan.  
Fix: el Spring Modifier necesita que la geometría de entrada cambie frame a frame (un Falloff animado, un LFO...). Sin input dinámico no hay efecto.

---

## Simulaciones (reglas generales)

**Sim con comportamiento extraño o explosión**  
Fix: siempre `Initialize → Start → Play` en ese orden. Si explota: bajar Time Scale o subir Substeps/Iterations.

**Physarum que no evoluciona**  
Causa: falta configurar el feedback loop.  
Fix: `Target Particles Update POP` + `Target Trail Update TOP` deben apuntar al nodo aguas abajo que vuelve a alimentar el Physarum.

**Flow modo Advect sin movimiento**  
Misma causa que Physarum: falta `Target Particles Update POP`.

**POPX Particle sin física visible**  
Causa: POPX Particle en modo Simple necesita un Particle POP nativo externo para la integración.  
El POPX Particle solo resuelve la física — no emite ni integra por sí solo.

---

## Soft Body

**Mesh que colapsa inmediatamente**  
Causa: falta el POP de constraints en Input 1 del Soft Body.  
Fix: generar constraints con el op Constraints y conectar en Input 1.

**Simulación inestable / explosión**  
Fix: bajar Compliance, subir Substeps (empezar con 4-8) y/o subir Iterations.

**Struts demasiado lentos**  
Causa: si el mesh es muy denso, el número de struts se dispara.  
Fix: reducir densidad del mesh antes de generar struts, o reducir Max Strut Length.

**SBPP sin efecto visual**  
Causa: SBPP necesita recibir Output 0 (geo) **y** Output 1 (constraints) del Soft Body.  
Si solo recibe Output 0, no puede calcular stretch stress.

---

## Tools

**Path Tracer no traza las instancias**  
Causa: las instancias POPX son packed — el Path Tracer no puede trazarlas directamente.  
Fix: añadir **Unpack** antes del Path Tracer.

**Geo op sin materiales visibles**  
Causa: el slot de material está vacío o el índice no coincide con el de la geometría.  
Fix: verificar que el índice de instancia (`popxIndex`) corresponde al slot de Material en Geo.

**Voxelize sin output en el Path Tracer**  
Fix: conectar la textura 3D de Voxelize al **Input 2** del Path Tracer, no al Input 0.  
Activar `Voxel Tracing` en Path Tracer y seleccionar Render Mode correcto (Isosurface o Volume).

---

## Rendering

**DLG no crece**  
Causa: DLG necesita **line strips** como input, no puntos sueltos.  
Fix: usar Circle POP o Line POP (con primitivas de tipo line strip).

**Mesh Fill no llena el volumen**  
Causa: el mesh no está cerrado o los seeds no están dentro.  
Fix: verificar que el mesh es watertight. Usar Sprinkle POP para distribuir seeds sobre la superficie.
