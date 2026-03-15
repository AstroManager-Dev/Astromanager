# Bottom-Navigation auf Target-Unterseiten repariert

## Problem
Auf `/targets/<id>` wurden die Buttons der Bottom-Navigation und des Menüs nicht mehr sinnvoll behandelt.
Die globale Tab-JavaScript-Logik erwartete `.tab-panel`-Elemente der Startseite und führte auf Unterseiten nur Hash-Wechsel auf derselben URL aus.

## Umsetzung
- Wenn keine `.tab-panel`-Elemente vorhanden sind, behandelt `app.js` Navigationseinträge mit `data-tab` als echte Rücknavigation zur Startseite.
- Ziel ist dann `/#<tab>`, zum Beispiel:
  - `/#gallery`
  - `/#atlas`
  - `/#targets`
  - `/#overview`
- Die automatische Tab-Aktivierung läuft nur noch auf Seiten mit echten Tab-Panels.
