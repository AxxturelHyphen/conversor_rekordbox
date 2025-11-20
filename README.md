# Conversor de audio 320 kbps / WAV

Aplicación de escritorio (Python + PyQt6) para convertir archivos locales a MP3 320 kbps CBR o WAV PCM, gestionar colas y descargar audio desde enlaces públicos de SoundCloud/YouTube/otros servicios compatibles con `yt-dlp`.

## ¿Por qué este stack?
- **Python + PyQt6**: ofrece una UI nativa multiplataforma sencilla de construir y distribuir.
- **FFmpeg**: motor robusto para conversiones garantizando MP3 320 kbps CBR y WAV PCM.
- **yt-dlp**: permite descargar audio de SoundCloud y otros servicios en MP3 320 kbps.

## Requisitos
- Python 3.10+
- FFmpeg disponible en el `PATH` (para conversiones y post-procesado de descargas).
- Dependencias de Python: `PyQt6`, `yt-dlp`.

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
- **Añadir archivos**: botón o arrastrar/soltar sobre la tabla.
- **Seleccionar formato**: MP3 320 kbps CBR o WAV PCM 16-bit/44.1 kHz.
- **Carpeta de salida**: usar carpeta de origen o elegir una personalizada.
- **Cola**: la tabla muestra nombre, ruta, destino y estado (Pendiente, Convirtiendo, Completado, Error).
- **Descarga de streaming**: pega una URL pública (SoundCloud, YouTube, etc.) y pulsa "Descargar a MP3 320". Usa `yt-dlp` y FFmpeg para entregar MP3 a 320 kbps.

## Empaquetado
Puedes generar un ejecutable con PyInstaller:
```bash
pip install pyinstaller
pyinstaller -F -w src/conversor_rekordbox/ui/app.py --name conversor-audio
```
El ejecutable resultante estará en `dist/`.

## Comentarios clave del código
- Conversión a MP3 320 kbps y WAV: `src/conversor_rekordbox/audio/conversion.py` define los comandos FFmpeg.
- Gestión de cola e interfaz: `src/conversor_rekordbox/ui/main_window.py` controla la tabla, drag & drop y ejecución en hilos.
- Descarga SoundCloud/streaming: `src/conversor_rekordbox/api/soundcloud.py` usa `yt-dlp` y admite credenciales para extensiones futuras.
- Configuración y logging: `src/conversor_rekordbox/utils/config.py` y `src/conversor_rekordbox/utils/logger.py`.

## Pruebas
```bash
pytest
```
