# Conversor Rekordbox

Herramienta de línea de comando para convertir bibliotecas musicales entre los
formatos de Rekordbox, Serato y Engine DJ.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Uso

```bash
python -m conversor_rekordbox.cli entrada.xml salida.m3u8
```

Opciones disponibles:

- `--input-format`: fuerza el formato de entrada (`rekordbox`, `serato`,
  `engine_dj`).
- `--output-format`: fuerza el formato de salida (`rekordbox`, `serato`,
  `engine_dj`).

Los formatos se deducen automáticamente a partir de la extensión si no se
especifican.

## Formatos soportados

- **Rekordbox**: archivos XML exportados con la colección.
- **Serato**: listas de reproducción en formato M3U/M3U8.
- **Engine DJ**: exportación simplificada en JSON con metadatos de pistas.

## Pruebas

```bash
pytest
```
