# Target-Detail Resolver-Modul kompakter aufgebaut

## Ziel
Resolver-Daten auf der Target-Detailseite sollten auf Mobile weniger breit und dichter dargestellt werden.

## Umsetzung
- Target-Detailseite um ein eigenes Resolver-Modul unterhalb der Session-Liste ergänzt
- Resolverdaten direkt aus den einzelnen Resolver-Tabellen geladen
- target_final bleibt bewusst ausgeschlossen
- Feldraster adaptiv aufgebaut: kurze Werte können drei pro Zeile stehen, mittlere zwei pro Zeile, lange Werte laufen vollbreit
- Werte auf maximal drei Zeilen begrenzt
- technische Rohspalten `id`, `target_id` und `raw_payload` werden nicht angezeigt

## Betroffene Dateien
- `code/web/functions/targets.py`
- `code/web/templates/pages/_target_detail.html`
- `code/web/templates/pages/target_detail/_resolver_sections.html`
- `code/web/templates/pages/target_detail/_resolver_section.html`
- `code/web/static/css/app.css`

## Nicht enthalten
- keine DB-Änderung
- kein Final-Merge
- keine Änderungen an Resolver-Runnern
