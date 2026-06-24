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
    └── Carpeta compartida: \\100.102.173.86\comfyui-output
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

## Flujo completo desde el PC de casa (con Claude)

### 1. Comprobar si ComfyUI está corriendo
```
get_system_stats → si responde, ComfyUI ya está activo, saltar al paso 3
```

### 2. Si no responde — arrancar ComfyUI via SSH
```powershell
ssh -i "$env:USERPROFILE\.ssh\comfyui_key" framemov@100.102.173.86 "powershell -File C:\Users\framemov\Desktop\arrancar_comfyui_bg.ps1"
```
Esperar 25 segundos y verificar con `get_system_stats` antes de continuar.

### 3. Generar
Cargar el workflow con `get_workflow`, ajustar parámetros y ejecutar con `enqueue_workflow`.

### 4. Entregar el resultado
- **Imágenes:** `get_history` → filename → `get_image` → inline en el chat. Siempre hacer este paso.
- **Vídeos:** se guardan solos en la carpeta compartida. Decirle al usuario que los busque en `\\100.102.173.86\comfyui-output\video\` desde el explorador de Windows (pide usuario `framemov` y contraseña de Windows).

---

## Carpeta compartida de outputs (vídeos)

La carpeta de output de ComfyUI está compartida en red:

```
\\100.102.173.86\comfyui-output
```

Acceder desde el explorador de Windows del PC de casa. Pide credenciales:
- **Usuario:** `framemov`
- **Contraseña:** contraseña de Windows del PC de ComfyUI

Solo funciona con Tailscale activo en ambos PCs.

Subcarpetas relevantes:
- `video\` — vídeos generados con Wan
- `Flux2-Klein_*.png` — imágenes generadas con Flux 2 Klein

---

## Scripts en el PC de ComfyUI

### arrancar_comfyui_bg.ps1 (recomendado — segundo plano)
`C:\Users\framemov\Desktop\arrancar_comfyui_bg.ps1`

```powershell
Start-Process -FilePath "D:\pinokio\api\comfy.git\venv\Scripts\python.exe" `
  -ArgumentList "D:\pinokio\api\comfy.git\ComfyUI\main.py --listen 0.0.0.0 --port 8188 --database-url sqlite:///D:\pinokio\api\comfy.git\ComfyUI\user\comfyui_standalone.db" `
  -WindowStyle Hidden
```

Arranca ComfyUI en segundo plano — libera la sesión SSH inmediatamente.

### arrancar_comfyui.ps1 (alternativo — con ventana)
`C:\Users\framemov\Desktop\arrancar_comfyui.ps1`

```powershell
D:\pinokio\api\comfy.git\venv\Scripts\python.exe D:\pinokio\api\comfy.git\ComfyUI\main.py --listen 0.0.0.0 --port 8188 --database-url sqlite:///D:\pinokio\api\comfy.git\ComfyUI\user\comfyui_standalone.db
```

Requiere que la ventana de PowerShell del PC de casa quede abierta.

---

## Setup SSH (referencia)

### En el PC de casa — generar clave
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\comfyui_key" -N '""'
```

### En el PC de ComfyUI — autorizar la clave
Archivo: `C:\ProgramData\ssh\administrators_authorized_keys`

```powershell
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:(R)" /grant "Administradores:(R)"
```

### Activar SSH server (PowerShell como admin)
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

---

## Notas

- Si ComfyUI ya está corriendo, el arranque via SSH fallará por conflicto de puerto — ignorar y continuar.
- La carpeta compartida solo funciona con Tailscale activo en ambos PCs.
- Las skills de ComfyUI deben estar instaladas en el PC de casa para que Claude las use desde allí.
