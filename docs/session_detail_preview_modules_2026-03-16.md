# Session-Detail Preview-Module – 2026-03-16

Basis: echter Backup-Stand 0.4.016.

Umgesetzt:
- Session-Detail auf einzelne Modul-Blöcke umgestellt
- Header bleibt textbasiert; kein Bild im Headerbereich
- Hauptbild zeigt zuerst vorhandenes PNG/Preview
- FITS als vorbereitetes Dummy-Modul mit eigenem Switch
- Klick auf Bild öffnet Vollbildansicht
- Teleskop- und AstroManager-Bereich als getrennte Modulpanels
- RAW-Zugriff und einzelne Lights unter dem Teleskop-Bereich
- Session-Qualitätsübersicht mit Lights / Failed / Bad FITS, aber nur datenbasiert

Datenlogik:
- Preview-Priorität: img_reference.png -> img_stacked_counter.png -> stacked.png -> stacked.jpg -> stacked_thumbnail.jpg -> sonstige Preview-Bilder
- Einzelne Lights basieren auf raw_files.source_subtype = light_raw_frame
- failed / bad_fits werden nur aus quality_flag gezählt, wenn dort Werte vorhanden sind
- FITS-Viewer ist nur vorbereitet; keine feste Viewer-Software eingebaut
