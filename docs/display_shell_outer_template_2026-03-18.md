# Display-Shell Außen-Template

- fester Außenrahmen als zentrale App-Hülle
- dynamische Höhe über `100dvh` statt starrem `100vh`
- responsive Breite: Desktop gerahmt, Mobile vollflächig
- Topbar bleibt innerhalb der Shell oben
- Bottom-Navigation richtet sich an der Shell-Breite aus
- Innen-Design bleibt weitgehend erhalten

## Ziel

AstroManager soll nicht wie eine normale Website wirken, sondern wie ein stabiles Geräte-Display mit festem Außenrahmen und zentralem Content-Fenster.

## Technische Eckpunkte

- neue Shell-Wrapper in `base.html`
- Rahmen-/Screen-Optik in `app.css`
- Höhe über `100dvh` und CSS-Variablen
- Desktop mit Maximalbreite, Mobile ohne harte Seitenränder
