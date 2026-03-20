# JS9 lokaler Viewer im bestehenden FITS-Webmodul

## Ziel
Den bestehenden FITS-Viewer nicht in `app.py` neu verkabeln, sondern im vorhandenen Web-UI-Modul fuer RAW/FITS-Detail erweitern.

## Umsetzung
- `functions/fits_viewer.py` liefert zusaetzlich JS9-Kontextdaten fuer die RAW-Datei.
- `pages/raw_file_detail/_viewer_module.html` enthaelt jetzt zwei Ebenen:
  - nativer lokaler JS9-Viewer fuer FITS/WCS
  - bisherige serverseitige Debayer-/Stretch-Vorschau als Vergleichs- und OSC-Preview
- `raw_file_detail.html` laedt die JS9-Assets nur auf der RAW-Detailseite.
- `base.html` wurde um Head-/Script-Bloecke erweitert, damit Seitenskripte sauber modular eingebunden werden koennen.

## Lokale Asset-Strategie
JS9 wird nicht per CDN geladen.

Stattdessen:
- `image/Dockerfile.base` installiert benoetigte Pakete fuer spaetere JS9-Helper-Nutzung
- laedt die JS9-Quellen beim Base-Build lokal nach `/opt/vendor/js9`
- `image/Dockerfile` kopiert diese lokalen Assets in `/app/web/static/vendor/js9`

## Wichtiger Fachpunkt
JS9 zeigt das native FITS an. Bei Bayer-/OSC-FITS bleibt die bestehende serverseitige Debayer-/Stretch-Preview absichtlich erhalten, weil sie visuell oft besser als die reine native FITS-Darstellung ist.

## Dry-Run / Testlauf
Nach Build und Container-Neustart pruefen:

```bash
docker exec -it astromanager-web sh -lc '
python3 - <<"PY"
from pathlib import Path
base = Path("/app/web/static/vendor/js9")
required = [
    "js9.css",
    "js9support.css",
    "js9.min.js",
    "js9support.min.js",
    "js9plugins.js",
    "js9worker.js",
]
missing = [name for name in required if not (base / name).exists()]
print({"base": str(base), "missing": missing, "ok": not missing})
PY'
```

Danach im Browser:
- RAW-Detail einer FITS-Datei oeffnen
- FITS-Ansicht aufrufen
- pruefen, ob JS9-Display laedt
- pruefen, ob darunter die serverseitige Preview weiterhin funktioniert
