"""
sesion_tools_module - Memoria de sesion GIVAH, 100% nativa.

Reemplaza toda la dependencia de /project1 (form_server, session_loader,
session_info_table, memoria_sesion, sesion_actual_brief, td_givah). Todo
vive dentro de /givah_tool/sesion_tools:

  session_info    (tableDAT: campo,valor) — datos del grupo
  participantes   (tableDAT) — una fila por participante
  memoria         (tableDAT) — acuerdos/restricciones/vetos/objetivos/pendientes
  brief           (textDAT) — texto cacheado que devuelve sesion_contexto
  form_server     (webserverDAT) — formulario iPad
  form_html       (textDAT) — HTML del formulario
  form_callbacks  (textDAT) — rutas GET/POST del formulario

El session_id activo vive en /givah_tool/session_id (Text DAT compartido
por todo el kit — no en agent_GIVAH).

El brief se regenera al vuelo cuando cambia session_info/participantes/
memoria, y solo llega al agente si este llama a sesion_contexto — no se
inyecta en cada mensaje.
"""

import json
import os
import re
import datetime as _dt
import unicodedata as _uni

name = "sesion"
description = "Memoria de sesion: formulario iPad, acuerdos, informe HTML"
category = "tool"

params = [
    {"name": "Screenstate", "type": "str", "page": "Config", "label": "Screen State DAT",
     "default": "/givah_tool/pantalla_tools/screen_state",
     "help": "Tabla compartida donde se publican eventos de pantalla."},
    {"name": "Pantallasesion", "type": "str", "page": "Config", "label": "Pantalla sesion/acuerdos",
     "default": "centro",
     "help": "Pantalla donde se muestran participantes y acuerdos."},
    {"name": "Sessioniddat", "type": "str", "page": "Config", "label": "Session ID DAT",
     "default": "/givah_tool/session_id",
     "help": "Text DAT que guarda el session_id activo del kit."},
    {"name": "Sessioninfo", "type": "str", "page": "Config", "label": "Session Info Table",
     "default": "session_info",
     "help": "Table DAT interna con los campos del grupo. Relativo al modulo."},
    {"name": "Memtable", "type": "str", "page": "Config", "label": "Memoria Table",
     "default": "memoria",
     "help": "Table DAT interna con acuerdos. Relativo al modulo."},
    {"name": "Partstable", "type": "str", "page": "Config", "label": "Participantes Table",
     "default": "participantes",
     "help": "Table DAT interna con los participantes. Relativo al modulo."},
    {"name": "Briefdat", "type": "str", "page": "Config", "label": "Brief DAT",
     "default": "brief",
     "help": "Text DAT donde se cachea el brief. Relativo al modulo."},
    {"name": "Formport", "type": "int", "page": "Config", "label": "Puerto del formulario",
     "default": 9981, "min": 1024, "max": 65535,
     "help": "Puerto del webserverDAT que sirve el formulario iPad."},
    {"name": "Sessionsdir", "type": "str", "page": "Config", "label": "Sessions folder",
     "default": "sessions",
     "help": "Carpeta donde se guardan los JSON de sesiones y los informes. Relativo al proyecto o absoluto."},
    {"name": "Catalogofolder", "type": "str", "page": "Config", "label": "Catalogo folder DAT",
     "default": "/givah_tool/catalogo_local_todo",
     "help": "Folder DAT usado para poblar la lista de empresas del formulario."},
    {"name": "Autopublicar", "type": "bool", "page": "Config", "label": "Auto-publicar en pantalla",
     "default": True,
     "help": "Si esta activo, publica en screen_state al iniciar sesion o registrar un acuerdo."},
]

_TIPOS = ("acuerdo", "restriccion", "veto", "objetivo", "pendiente")


# ─── UTILIDADES ──────────────────────────────────────────────────────────────

def _me():
    return me.parent()

def _resolve(par_name, default_local=None):
    """Devuelve el operador referido por par_name. Si el valor es
    relativo, lo busca dentro del módulo; si es absoluto, en el proyecto."""
    val = (getattr(_me().par, par_name).eval() or "").strip()
    if not val:
        val = default_local or ""
    o = op(val) or _me().op(val)
    return o

def _sid_dat():
    return _resolve("Sessioniddat")

def _session_id():
    src = _sid_dat()
    if src is None:
        return ""
    if hasattr(src.par, "Sessionid"):
        return src.par.Sessionid.eval() or ""
    return (src.text or "").strip()

def _set_session_id(sid):
    src = _sid_dat()
    if src is None:
        return False
    if hasattr(src.par, "Sessionid"):
        src.par.Sessionid = sid
    else:
        src.text = sid
    return True

def _info_tbl():
    return _resolve("Sessioninfo", "session_info")

def _mem_tbl():
    return _resolve("Memtable", "memoria")

def _parts_tbl():
    return _resolve("Partstable", "participantes")

def _brief_dat():
    return _resolve("Briefdat", "brief")

def _screen_state():
    return _resolve("Screenstate")

def _pantalla_sesion():
    return (_me().par.Pantallasesion.eval() or "centro").strip()

def _sessions_dir():
    val = (_me().par.Sessionsdir.eval() or "sessions").strip()
    if not os.path.isabs(val):
        val = os.path.join(project.folder, val)
    os.makedirs(val, exist_ok=True)
    return val

def _args(tool_call):
    raw = tool_call.function.arguments
    try:
        return json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        return {}

def _slugify(s):
    s = _uni.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").upper()
    return s or "SESION"

def _norm(s):
    s = _uni.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return s.lower().strip()


# ─── EMPRESAS DEL CATALOGO ───────────────────────────────────────────────────

def _empresas_disponibles():
    """Devuelve la lista de empresas base del catalogo local. Solo mira
    la primera capa de subcarpetas de Catalogo_local/. Nombre mostrado
    en mayusculas (LUXES, VERUM...)."""
    fd = _resolve("Catalogofolder")
    if fd is None:
        return []
    empresas = set()
    hdr = [fd[0, c].val for c in range(fd.numCols)]
    try:
        col_folder = hdr.index("folder")
    except ValueError:
        return []
    for r in range(1, fd.numRows):
        rel = str(fd[r, col_folder].val).replace("\\", "/").strip("/")
        if not rel:
            continue
        first = rel.split("/", 1)[0]
        if first and not first.startswith("."):
            empresas.add(first)
    return sorted(e.upper() for e in empresas)


# ─── PUBLICACION EN PANTALLA ─────────────────────────────────────────────────

def _publicar_sesion_en_pantalla():
    """Publica el bloque de sesion (nombre grupo, participantes, director)
    en la pantalla configurada."""
    ss = _screen_state()
    if ss is None or not _me().par.Autopublicar.eval():
        return
    info = _info_tbl()
    parts = _parts_tbl()
    if info is None or parts is None:
        return

    campos = {}
    for r in range(1, info.numRows):
        campos[str(info[r, "campo"].val)] = str(info[r, "valor"].val)

    sid = _session_id()
    nombre = campos.get("nombre_grupo") or campos.get("empresa") or sid
    contexto = campos.get("contexto", "").strip()
    titulo = contexto if contexto else nombre

    participantes_lista = []
    director = ""
    for r in range(1, parts.numRows):
        if str(parts[r, "session_id"].val) != sid:
            continue
        nom = str(parts[r, "nombre"].val)
        area = str(parts[r, "area"].val)
        veto = str(parts[r, "autoridad_veto"].val).lower() in ("1", "true", "yes")
        if not nom:
            continue
        disp = f"{nom} ({area})" if area else nom
        participantes_lista.append(disp)
        if veto and not director:
            director = disp

    pantalla = _pantalla_sesion()
    ss.appendRow([pantalla, "session", json.dumps({
        "head": "Sesion",
        "nombre": titulo,
        "participantes": participantes_lista,
        "director": director,
    })])
    _publicar_acuerdos_en_pantalla()

def _publicar_acuerdos_en_pantalla():
    """Publica los acuerdos/restricciones registrados hasta ahora en la
    pantalla configurada."""
    ss = _screen_state()
    if ss is None or not _me().par.Autopublicar.eval():
        return
    info = _info_tbl()
    mem = _mem_tbl()
    if mem is None:
        return
    sid = _session_id()
    items = []
    if info is not None:
        for r in range(1, info.numRows):
            if str(info[r, "campo"].val) == "restricciones":
                v = str(info[r, "valor"].val).strip()
                if v and _norm(v) not in ("ninguna", "-", "n/a"):
                    for linea in v.splitlines():
                        linea = linea.strip()
                        if linea:
                            items.append({"tipo": "restriccion", "contenido": linea})
                break
    for r in range(1, mem.numRows):
        if str(mem[r, "session_id"].val) != sid:
            continue
        items.append({"tipo": str(mem[r, "tipo"].val),
                      "contenido": str(mem[r, "contenido"].val)})

    pantalla = _pantalla_sesion()
    ss.appendRow([pantalla, "entries", json.dumps({"items": items})])


# ─── BRIEF PARA EL AGENTE ────────────────────────────────────────────────────

def _construir_brief():
    """Regenera el brief cacheado en el text DAT. El agente lo consulta
    via la tool sesion_contexto una sola vez al inicio."""
    br = _brief_dat()
    info = _info_tbl()
    parts = _parts_tbl()
    if br is None or info is None or parts is None:
        return

    campos = {}
    for r in range(1, info.numRows):
        campos[str(info[r, "campo"].val)] = str(info[r, "valor"].val)

    sid = _session_id()
    lineas = []
    lineas.append(f"Sesion: {sid}  ({campos.get('fecha','')})")
    if campos.get("empresa"):
        lineas.append(f"Empresa: {campos['empresa']}")
    if campos.get("contexto"):
        lineas.append(f"Contexto: {campos['contexto']}")
    if campos.get("objetivos"):
        lineas.append(f"Objetivos: {campos['objetivos']}")
    restr = campos.get("restricciones", "").strip()
    if restr and _norm(restr) not in ("ninguna", "-", "n/a"):
        lineas.append(f"Restricciones no negociables: {restr}")

    lineas.append("")
    lineas.append("Participantes:")
    for r in range(1, parts.numRows):
        if str(parts[r, "session_id"].val) != sid:
            continue
        nom = str(parts[r, "nombre"].val)
        if not nom:
            continue
        area = str(parts[r, "area"].val)
        rol = str(parts[r, "rol"].val) or "participante"
        veto = str(parts[r, "autoridad_veto"].val).lower() in ("1", "true", "yes")
        prefs = str(parts[r, "preferencias"].val).strip()
        detalles = []
        if area:
            detalles.append(area)
        if rol and rol != "participante":
            detalles.append(rol)
        if veto:
            detalles.append("director (autoridad VETO)")
        if prefs:
            detalles.append(f"prefs: {prefs}")
        linea = f"- {nom}"
        if detalles:
            linea += f" ({', '.join(detalles)})"
        lineas.append(linea)

    br.text = "\n".join(lineas)


# ─── ENTRY POINT DEL FORMULARIO ──────────────────────────────────────────────

def iniciar_sesion_desde_formulario(payload):
    """Recibe el JSON del formulario iPad, guarda todo en tablas + disco,
    publica en pantalla y regenera el brief. Devuelve (session_id, path)."""
    grupo = payload.get("grupo", {}) or {}
    participantes = payload.get("participantes", []) or []

    empresa = (grupo.get("empresa") or "").strip()
    if not empresa:
        raise ValueError("Falta la empresa")
    parts_validos = [p for p in participantes if (p.get("nombre") or "").strip()]
    if not parts_validos:
        raise ValueError("Falta al menos un participante")

    override = (grupo.get("session_id_override") or "").strip()
    sessions_dir = _sessions_dir()
    if override:
        session_id = override
    else:
        today = _dt.date.today().isoformat()
        base = f"GIVAH-{today}-{_slugify(empresa)}"
        n = 1
        session_id = f"{base}-01"
        while os.path.exists(os.path.join(sessions_dir, f"{session_id}.json")):
            n += 1
            session_id = f"{base}-{n:02d}"

    fecha = _dt.date.today().isoformat()
    nombre_grupo = (grupo.get("nombre") or session_id).strip()

    session = {
        "session_id": session_id,
        "fecha": fecha,
        "grupo": {
            "nombre": nombre_grupo,
            "empresa": empresa,
            "contexto": grupo.get("contexto", ""),
            "restricciones": grupo.get("restricciones", "") or "",
            "objetivos": grupo.get("objetivos", ""),
        },
        "participantes": [
            {
                "nombre": p.get("nombre", "").strip(),
                "area": p.get("area", "").strip(),
                "rol": p.get("rol", "participante").strip() or "participante",
                "autoridad_veto": bool(p.get("autoridad_veto", False)),
                "preferencias": p.get("preferencias", "").strip(),
            }
            for p in parts_validos
        ],
    }

    path = os.path.join(sessions_dir, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    _set_session_id(session_id)

    info = _info_tbl()
    info.clear()
    info.appendRow(["campo", "valor"])
    info.appendRow(["session_id", session_id])
    info.appendRow(["fecha", fecha])
    info.appendRow(["empresa", empresa])
    info.appendRow(["nombre_grupo", nombre_grupo])
    info.appendRow(["contexto", session["grupo"]["contexto"]])
    info.appendRow(["objetivos", session["grupo"]["objetivos"]])
    info.appendRow(["restricciones", session["grupo"]["restricciones"] or "Ninguna"])

    parts = _parts_tbl()
    for r in range(parts.numRows - 1, 0, -1):
        if str(parts[r, "session_id"].val) == session_id:
            parts.deleteRow(r)
    for p in session["participantes"]:
        parts.appendRow([
            session_id, p["nombre"], p["area"], p["rol"],
            "1" if p["autoridad_veto"] else "0", p["preferencias"],
        ])

    _construir_brief()
    _publicar_sesion_en_pantalla()

    return session_id, path


# ─── TOOLS EXPUESTAS AL AGENTE ───────────────────────────────────────────────

def get_tools(ext):
    tools = [
        {
            "name": "sesion_registrar_acuerdo",
            "description":
                "Registra un acuerdo, restriccion, veto, objetivo o pendiente en la "
                "memoria de la sesion activa. Se muestra automaticamente en pantalla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string",
                             "description": "acuerdo | restriccion | veto | objetivo | pendiente"},
                    "contenido": {"type": "string", "description": "Texto del acuerdo."}
                },
                "required": ["tipo", "contenido"]
            }
        },
        {
            "name": "sesion_leer_memoria",
            "description": "Lee los acuerdos, restricciones y vetos registrados en la sesion activa.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "sesion_contexto",
            "description":
                "Devuelve el brief de la sesion activa (empresa, participantes con sus roles y "
                "preferencias, objetivos, restricciones). LLAMA A ESTA TOOL EN TU PRIMER TURNO "
                "para saber a quien saludar por nombre.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "sesion_generar_informe",
            "description":
                "Genera el informe HTML de la sesion activa (participantes, acuerdos, timeline "
                "de imagenes y splats) y devuelve la URL local. Llamar al cierre de la sesion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string",
                                   "description": "Vacio = sesion activa.", "default": ""}
                }
            }
        },
    ]
    return tools


def handle_sesion_registrar_acuerdo(ext, tool_call):
    a = _args(tool_call)
    tipo = (a.get("tipo", "") or "").strip().lower()
    contenido = (a.get("contenido", "") or "").strip()
    if not tipo or not contenido:
        return {"ok": False, "error": "tipo y contenido requeridos"}
    if tipo not in _TIPOS:
        return {"ok": False, "error": f"tipo '{tipo}' no valido. Usa: {', '.join(_TIPOS)}"}
    sid = _session_id()
    if not sid:
        return {"ok": False, "error": "no hay session_id activo — inicia una sesion desde el formulario"}
    mem = _mem_tbl()
    if mem is None:
        return {"ok": False, "error": "memoria table no resuelve — revisa Config"}
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    mem.appendRow([sid, tipo, contenido, ts])
    _publicar_acuerdos_en_pantalla()
    return {"ok": True, "session_id": sid, "tipo": tipo,
            "mensaje": "Registrado en la memoria y publicado en pantalla."}


def handle_sesion_leer_memoria(ext, tool_call):
    sid = _session_id()
    if not sid:
        return {"ok": False, "error": "no hay session_id activo"}
    mem = _mem_tbl()
    if mem is None:
        return {"ok": False, "error": "memoria table no resuelve"}
    items = []
    for r in range(1, mem.numRows):
        if str(mem[r, "session_id"].val) == sid:
            items.append({"tipo": str(mem[r, "tipo"].val),
                          "contenido": str(mem[r, "contenido"].val),
                          "ts": str(mem[r, "ts"].val)})
    return {"ok": True, "session_id": sid, "total": len(items), "items": items}


def handle_sesion_contexto(ext, tool_call):
    sid = _session_id()
    br = _brief_dat()
    if br is None:
        return {"ok": False, "error": "brief DAT no resuelve"}
    texto = br.text or ""
    if not texto.strip():
        return {"ok": False, "error": "brief vacio — no se ha iniciado sesion todavia"}
    return {"ok": True, "session_id": sid, "brief": texto}


def handle_sesion_generar_informe(ext, tool_call):
    a = _args(tool_call)
    sid = (a.get("session_id", "") or "").strip() or _session_id()
    if not sid:
        return {"ok": False, "error": "no hay session_id"}
    try:
        html_path = _generar_informe_html(sid)
        return {"ok": True, "session_id": sid, "informe_path": html_path,
                "mensaje": f"Informe generado en {html_path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── INFORME HTML (nativo, sin td_givah) ─────────────────────────────────────

def _generar_informe_html(sid):
    """Genera un HTML sencillo del informe de sesion. Escribe en
    sessions/<sid>_informe.html y devuelve la ruta."""
    sessions_dir = _sessions_dir()

    session = {}
    session_path = os.path.join(sessions_dir, f"{sid}.json")
    if os.path.exists(session_path):
        with open(session_path, "r", encoding="utf-8") as f:
            session = json.load(f)
    grupo = session.get("grupo", {})
    participantes = session.get("participantes", [])

    mem = _mem_tbl()
    acuerdos = []
    if mem is not None:
        for r in range(1, mem.numRows):
            if str(mem[r, "session_id"].val) == sid:
                acuerdos.append({
                    "tipo": str(mem[r, "tipo"].val),
                    "contenido": str(mem[r, "contenido"].val),
                    "ts": str(mem[r, "ts"].val) if mem.numCols > 3 else "",
                })

    imagenes = []
    for path in ["/givah_tool/comfy_tools/generated_images_table",
                 "/project1/generated_images_table"]:
        t = op(path)
        if t is None or t.numRows < 2:
            continue
        hdr = [t[0, c].val for c in range(t.numCols)]
        for r in range(1, t.numRows):
            row = {hdr[c]: str(t[r, c].val) for c in range(t.numCols)}
            if row.get("session_id") == sid:
                imagenes.append(row)
        if imagenes:
            break

    splats = []
    for path in ["/project1/gaussian_jobs", "/givah_tool/splat_tools/gaussian_jobs"]:
        t = op(path)
        if t is None or t.numRows < 2:
            continue
        hdr = [t[0, c].val for c in range(t.numCols)]
        for r in range(1, t.numRows):
            row = {hdr[c]: str(t[r, c].val) for c in range(t.numCols)}
            if row.get("session_id") == sid and row.get("status") == "ready":
                splats.append(row)
        if splats:
            break

    def esc(s):
        return (str(s or "")
                .replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    parts_html = ""
    for p in participantes:
        nom = esc(p.get("nombre", ""))
        area = esc(p.get("area", ""))
        rol = esc(p.get("rol", ""))
        veto = " · director" if p.get("autoridad_veto") else ""
        prefs = esc(p.get("preferencias", ""))
        line_area = " — " + area if area else ""
        line_rol = " · " + rol if rol and rol != "participante" else ""
        line_prefs = '<div class="prefs">' + prefs + '</div>' if prefs else ''
        parts_html += ('<li><strong>' + nom + '</strong>'
                       + line_area + line_rol + veto + line_prefs + '</li>')

    color_tipo = {
        "acuerdo": "#43aa54", "restriccion": "#d4a849",
        "veto": "#e06c75", "objetivo": "#7aa2f7", "pendiente": "#c678dd",
    }
    acu_html = ""
    for a in acuerdos:
        c = color_tipo.get(a["tipo"], "#8b93a3")
        ts = esc(a["ts"])
        ts_html = '<span class="ts">' + ts + '</span>' if ts else ''
        acu_html += ('<div class="acuerdo">'
                     + '<span class="tag" style="background:' + c + '">' + esc(a["tipo"]) + '</span>'
                     + '<span class="txt">' + esc(a["contenido"]) + '</span>'
                     + ts_html + '</div>')

    img_html = "".join(
        '<div class="img"><div class="cap">' + esc(i.get("nombre") or i.get("url","")) + '</div></div>'
        for i in imagenes
    )
    splat_html = "".join(
        '<div class="splat">Splat: ' + esc(s.get("slug","")) + ' — ' + esc(s.get("source_nombre","")) + '</div>'
        for s in splats
    )

    splats_section = ('<section><h2>Splats generados</h2>' + splat_html + '</section>') if splats else ''
    img_section = ('<section><h2>Imagenes generadas</h2>' + img_html + '</section>') if imagenes else ''

    html = ('<!DOCTYPE html>\n'
            '<html lang="es"><head><meta charset="UTF-8">\n'
            '<title>Informe ' + esc(sid) + '</title>\n'
            '<style>\n'
            ':root{--bg:#0f1115;--card:#181b22;--line:#2a2f3a;--text:#e8eaf0;--muted:#8b93a3;--accent:#d4a849;}\n'
            '*{box-sizing:border-box}\n'
            'body{margin:0;padding:32px;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.5}\n'
            '.wrap{max-width:900px;margin:0 auto}\n'
            'header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:24px}\n'
            'h1{margin:0;font-size:28px;font-weight:600}\n'
            'h1 span{color:var(--accent)}\n'
            '.sub{color:var(--muted);font-size:14px;margin-top:8px}\n'
            'section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px;margin-bottom:18px}\n'
            'h2{margin:0 0 14px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1.4px;color:var(--accent)}\n'
            'ul{list-style:none;padding:0;margin:0}\n'
            'li{padding:10px 0;border-bottom:1px solid #24272f}\n'
            'li:last-child{border-bottom:none}\n'
            '.prefs{color:var(--muted);font-size:13px;margin-top:4px}\n'
            '.acuerdo{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #24272f}\n'
            '.acuerdo:last-child{border-bottom:none}\n'
            '.tag{color:#1a1408;font-size:11px;text-transform:uppercase;letter-spacing:1px;padding:3px 8px;border-radius:4px;font-weight:600;min-width:88px;text-align:center}\n'
            '.txt{flex:1}\n'
            '.ts{color:var(--muted);font-size:12px}\n'
            '.stats{display:flex;gap:20px;color:var(--muted);font-size:14px}\n'
            '</style></head>\n'
            '<body><div class="wrap">\n'
            '<header>\n'
            '  <h1>GIVAH <span>· informe de sesion</span></h1>\n'
            '  <div class="sub">' + esc(sid) + ' — ' + esc(session.get("fecha","")) + ' — ' + esc(grupo.get("empresa","")) + '</div>\n'
            '  <div class="stats" style="margin-top:12px">\n'
            '    <span>' + str(len(participantes)) + ' participantes</span>\n'
            '    <span>' + str(len(acuerdos)) + ' registros</span>\n'
            '    <span>' + str(len(imagenes)) + ' imagenes</span>\n'
            '    <span>' + str(len(splats)) + ' splats</span>\n'
            '  </div>\n'
            '</header>\n'
            '<section><h2>Contexto</h2><div>' + esc(grupo.get("contexto") or "(sin contexto)") + '</div></section>\n'
            '<section><h2>Objetivos</h2><div>' + esc(grupo.get("objetivos") or "(sin especificar)") + '</div></section>\n'
            '<section><h2>Participantes</h2><ul>' + (parts_html or "<li>(sin participantes)</li>") + '</ul></section>\n'
            '<section><h2>Acuerdos y restricciones</h2>' + (acu_html or "<div style=\"color:var(--muted)\">(sin registros)</div>") + '</section>\n'
            + splats_section + img_section +
            '</div></body></html>')

    path = os.path.join(sessions_dir, f"{sid}_informe.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ─── LOAD DE UNA SESION EXISTENTE ────────────────────────────────────────────

def cargar_sesion_por_id(sid):
    """Carga una sesion existente desde disco y repuebla tablas + pantallas."""
    sessions_dir = _sessions_dir()
    path = os.path.join(sessions_dir, f"{sid}.json")
    if not os.path.exists(path):
        return {"ok": False, "error": f"no existe {path}"}
    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)
    payload = {
        "grupo": {
            **session.get("grupo", {}),
            "session_id_override": session["session_id"],
        },
        "participantes": session.get("participantes", []),
    }
    session_id, path2 = iniciar_sesion_desde_formulario(payload)
    return {"ok": True, "session_id": session_id}
