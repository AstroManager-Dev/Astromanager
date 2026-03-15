# NASA Resolver: JWST/Hubble Priorität und harte Match-Regeln

Stand: 2026-03-15

## Ziel
NASA-Bilder nur noch übernehmen, wenn der Treffer fachlich deutlich besser zum Target passt.

## Umgesetzt
- Resolver priorisiert NASA-Treffer jetzt nach Quelle:
  1. James Webb / JWST / Webb
  2. Hubble / HST
  3. sonstige NASA-Treffer
- Resolver akzeptiert Bilder nur noch bei ausreichendem Score.
- Exakte Alias- und Katalognamen-Treffer werden deutlich höher bewertet.
- Deutsche und englische Labels sowie Alias-Felder fließen in die Such- und Matchlogik ein.
- Problematische generische NASA-Treffer werden hart abgewertet, z. B.:
  - artist concept
  - illustration
  - simulation
  - poster
  - logo
  - patch
  - crew
  - launch
  - astronaut
  - rocket
- `nasa_source` wird bei JWST/Hubble als
  - `nasa-image-library:jwst`
  - `nasa-image-library:hubble`
  gespeichert.

## Dry-Run
Der Resolver unterstützt jetzt:

```bash
python3 /app/bin/resolve_target_nasa_image.py --dry-run --limit 20
```

Dabei werden geplante Treffer ausgegeben, ohne die DB zu ändern.

## Wichtig
Ein echter RA/DEC-Abgleich ist mit der NASA Image Library API im aktuellen Resolverpfad nicht belastbar nutzbar. Das Matching bleibt daher namens- und quellenbasiert.
