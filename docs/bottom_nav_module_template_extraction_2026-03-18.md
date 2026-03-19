# Bottom-Nav als eigenes Modul ausgelagert

## Ziel
Die Hauptnavigation unten wird nicht mehr direkt in `base.html` aufgebaut, sondern als eigenes Template-Modul eingebunden.

## Änderungen
- neues Include: `code/web/templates/includes/_bottom_nav.html`
- neues CSS-Modul mit eigenem Namespace: `code/web/static/css/modules/18_bottom_nav.css`
- `base.html` enthält nur noch den Include-Aufruf und lädt das Bottom-Nav-CSS-Modul direkt
- `app.js` unterstützt die neuen Modulklassen `am-bottom-nav__button` und bleibt dabei rückwärtskompatibel zu `bottom-nav-btn`

## Struktur
Die Bottom-Navigation nutzt jetzt einen eigenen Klassenraum:
- `am-bottom-nav`
- `am-bottom-nav__frame`
- `am-bottom-nav__grid`
- `am-bottom-nav__button`

Damit bleibt die Navigation unabhängig von generischen Altregeln in `app.css` und kann künftig getrennt weiterentwickelt werden.
