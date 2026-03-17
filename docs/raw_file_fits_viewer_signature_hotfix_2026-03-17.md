# RAW File FITS Viewer Signature Hotfix

- behebt 500er auf `/raw-files/<id>` und `/media/raw-file-fits-preview/<id>.png`
- Ursache: `enrich_raw_file_viewer_context()` wurde mit neuen Pflichtparametern verwendet, bestehende Aufrufer übergaben diese nicht
- Hotfix macht die zusätzlichen Viewer-Parameter optional und reicht sie in `app.py` sauber weiter
- keine DB-Änderungen
