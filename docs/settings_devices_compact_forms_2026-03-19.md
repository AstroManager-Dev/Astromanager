# Settings Geräte kompakter aufgebaut

## Ziel
Geräte-Settings auf Mobile deutlich kompakter und übersichtlicher machen.

## Umgesetzt
- Neue Geräteinstanz standardmäßig eingeklappt
- Öffnen nur über Button `Neue Instanz hinzufügen`
- Source-Templates bleiben als kompakte Collapsible-Infos
- Bestehende Geräteinstanzen bleiben kompakt
- Bearbeitungsformular pro Instanz erst nach Klick auf `Instanz bearbeiten` sichtbar
- `instance_key` wird bei Neuanlage automatisch aus dem Anzeigenamen erzeugt
- Bei Kollision wird automatisch ein Suffix ergänzt
- `/settings` Route und `settings` Hash-Tab im Web-Stand ergänzt

## Dry-Run
- Python-Syntax für `app.py` und `settings_devices.py` geprüft
- Templates/CSS ohne neue externen Abhängigkeiten umgesetzt
