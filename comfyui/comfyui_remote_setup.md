# ComfyUI — Setup remoto

Cómo arrancar y usar ComfyUI desde el PC de casa via Tailscale + SSH.

**Última revisión:** junio 2026.

---

## Arquitectura

```
PC casa (vuski / 100.75.16.45)
    └── Claude Desktop con comfyui-mcp apuntando a 100.102.173.86:8188
            │
            │ Tailscale VPN
            ▼
PC ComfyUI (framemov / 100.102.173.86)
    └── ComfyUI corriendo en 0.0.0.0:8188
```

---

## IPs Tailscale

| PC | Usuario | IP Tailscale |
|---|---|---|
| PC ComfyUI (trabajo) | framemov | `100.102.173.86` |
| PC casa | vuski | `100.75.16.45` |

Ambos PCs deben tener Tailscale activo (icono verde en la bandeja).

---

## Config Claude Desktop — PC de casa

Archivo: `C:\Users\vuski\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "comfyui": {
      "command": "npx",
      "args": ["-y", "comfyui-mcp", "--comfyui-url", "http://100.102.173.86:8188"]
    }
  }
}
```

Reiniciar Claude Desktop tras cualquier cambio en este archivo.

---

## Arrancar ComfyUI remotamente via SSH

### Script en el PC de ComfyUI

Archivo: `C:\Users\framemov\Desktop\arrancar_comfyui.ps1`

```powershell
D:\pinokio\api\comfy.git\venv\Scripts\python.exe D:\pinokio\api\comfy.git\ComfyUI\main.py --listen 0.0.0.0 --port 8188 --database-url sqlite:///D:\pinokio\api\comfy.git\ComfyUI\user\comfyui_standalone.db
```

### Comando desde el PC de casa

```powershell
ssh -i "$env:USERPROFILE\.ssh\comfyui_key" framemov@100.102.173.86 "powershell -WindowStyle Hidden -File C:\Users\framemov\Desktop\arrancar_comfyui.ps1"
```

La ventana de PowerShell del PC de casa debe quedarse abierta mientras ComfyUI esté corriendo.

### Verificar que ComfyUI está respondiendo

```powershell
Invoke-WebRequest -Uri "http://100.102.173.86:8188/system_stats" -UseBasicParsing | Select-Object StatusCode
```

Debe devolver `StatusCode: 200`.

---

## Setup SSH (ya hecho, solo como referencia)

### En el PC de casa — generar clave
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\comfyui_key" -N '""'
```

La clave pública queda en `C:\Users\vuski\.ssh\comfyui_key.pub`.

### En el PC de ComfyUI — autorizar la clave
La clave pública debe estar en:
`C:\ProgramData\ssh\administrators_authorized_keys`

Con permisos:
```powershell
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:(R)" /grant "Administradores:(R)"
```

### Activar SSH server en el PC de ComfyUI (PowerShell como admin)
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

---

## Flujo de trabajo habitual

1. Encender el PC de ComfyUI (o que esté encendido)
2. Asegurarse de que Tailscale está activo en ambos PCs
3. Desde el PC de casa, ejecutar el comando SSH para arrancar ComfyUI
4. Esperar ~20 segundos a que arranque
5. Abrir Claude Desktop en el PC de casa y pedir generaciones normalmente

---

## Notas

- Si ComfyUI ya está corriendo (arrancado desde TD u otra vez), el comando SSH fallará por conflicto de puerto. Matar el proceso primero o ignorarlo si ya está corriendo.
- Las imágenes generadas se reciben como link o inline en el chat de Claude Desktop del PC de casa.
- Las skills de ComfyUI deben estar instaladas también en el PC de casa para que Claude las use desde allí.
