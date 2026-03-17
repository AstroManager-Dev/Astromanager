Reparatur-Patch für den 500-Fehler auf /targets/<id>.

Ursache:
- pages/target_detail/_resolver_sections.html wurde von _target_detail.html eingebunden,
  war aber im zuletzt gelieferten Patch-ZIP nicht enthalten.

Enthalten:
- code/web/templates/pages/target_detail/_resolver_sections.html
- code/web/templates/pages/target_detail/_resolver_section.html

Keine DB- oder Workflow-Änderung.
Nur Web-Template-Reparatur.
