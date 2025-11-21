# Descargador SoundCloud → MP3 320 kbps

Aplicación de escritorio (Python + PyQt6) centrada en descargar pistas y playlists públicas de SoundCloud directamente en MP3 a 320 kbps CBR utilizando `yt-dlp` y FFmpeg para el postprocesado.

## ¿Por qué este stack?
- **Python + PyQt6**: ofrece una UI nativa multiplataforma sencilla de construir y distribuir.
- **FFmpeg + yt-dlp**: garantiza MP3 320 kbps CBR incluso cuando la fuente es AAC/Opus.

## Requisitos
- Python 3.10+
- FFmpeg disponible en el `PATH` (para conversiones y post-procesado de descargas).
- Dependencias de Python: `PyQt6`, `yt-dlp`.
- Si no detecta FFmpeg, la aplicación descargará una build estática en `~/.conversor_audio/bin` la primera vez que inicias la interfaz.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Ejecución en desarrollo
```bash
conversor-audio
```

La configuración se guarda en `~/.conversor_audio/config.json` y los logs en `~/.conversor_audio/app.log`.

## Uso
- **Introduce el enlace** de pista o playlist pública de SoundCloud.
- **Elige la carpeta de destino** (por defecto `~/Downloads`).
- Pulsa **"Descargar en MP3 320 kbps"** y espera a que termine. Las playlists se guardan en una carpeta con el nombre de la lista y los elementos numerados.

## Empaquetado
Puedes generar un ejecutable con PyInstaller:
```bash
pip install pyinstaller
pyinstaller -F -w src/conversor_rekordbox/ui/app.py --name conversor-audio
```
El ejecutable resultante estará en `dist/`.

## Comentarios clave del código
- Descarga SoundCloud: `src/conversor_rekordbox/api/soundcloud.py` configura `yt-dlp` para playlists y pistas en MP3 320 kbps.
- Interfaz: `src/conversor_rekordbox/ui/main_window.py` valida enlaces de SoundCloud, permite elegir la carpeta destino y muestra el progreso.
- Configuración y logging: `src/conversor_rekordbox/utils/config.py` y `src/conversor_rekordbox/utils/logger.py`.

## Pruebas
```bash
pytest
```
