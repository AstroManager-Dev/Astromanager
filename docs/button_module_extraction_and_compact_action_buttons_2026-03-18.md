# Button-Modul und kleine Hauptaktionsbuttons

## Stand
Die wiederverwendbaren Button-Stile lagen bisher in `app.css`. Kleine Buttons (`Viewer öffnen`, `Details`, Pagination, Segment-Switches) sahen dadurch nicht wie verkleinerte Varianten der Hauptaktionsbuttons aus der Zentrale aus.

## Änderung
- Button-System aus `app.css` in neues Modul `code/web/static/css/modules/10_buttons.css` ausgelagert
- kleine Buttons und Segment-Switches auf dieselbe visuelle DNA wie die Hauptaktionsbuttons umgestellt
- Pagination in der RAW-Liste auf `astro-btn` umgestellt
- RAW-Zugangsbutton in der Session-Detailseite auf `astro-btn` umgestellt

## Effekt
- konsistentes Styling für große und kleine Aktionen
- modulare CSS-Struktur bleibt erhalten
- neue Button-Regeln können getrennt von `app.css` weiterentwickelt werden
