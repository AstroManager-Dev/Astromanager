# AstroManager – Device Sources, UI-Template, Schema-Erweiterungen und fehlende Tabellen
Stand: 2026-03-08

## Zweck dieses Dokuments

Dieses Dokument hält die aktuellen Architektur- und Datenmodell-Überlegungen für AstroManager fest, damit sie später jederzeit wieder eingelesen und systematisch umgesetzt werden können.

Fokus:
- UI-Template für Datenquellen / Teleskope
- verschlüsselte Speicherung von Zugangsdaten
- generische Modellierung für verschiedene Smart-Teleskop-Typen
- sinnvolle Erweiterung bestehender Tabellen
- fehlende Tabellen für Session-, Gruppen-, Kalibrations- und Produktlogik
- Trennung zwischen Quelle, Session, Stack, Kalibration und Endprodukt

Dieses Dokument ist bewusst kein fertiges SQL-Schema, sondern eine belastbare Planungs- und Zielstruktur.

---

## 1. Ausgangslage

AstroManager besitzt bereits ein brauchbares Grundschema mit folgenden Kern-Tabellen:

- job_runs
- app_state
- device_sources
- sessions
- raw_files
- calibration_assets
- targets
- capture_profiles

Das Fundament ist vorhanden. Es fehlen nicht wahllos Tabellen, sondern vor allem:
- eine saubere Modellierung von Datenquellen für das UI
- eine echte Verarbeitungsebene oberhalb von Sessions
- eine Beziehung zwischen Kalibration und konkreter Verwendung
- eine Produkt-/Ausgabeebene für finale Resultate
- eine generische Sicht auf unterschiedliche Smart-Teleskop-Datenmodelle

---

## 2. Zielbild für Datenquellen im UI

Eine Datenquelle ist zunächst kein Sync-Job, sondern ein konfigurierbarer Stammdatensatz, der im UI angelegt und bearbeitet werden kann.

Eine Datenquelle beschreibt:

- welches Gerät das ist
- wie es erreichbar ist
- wie dessen Daten organisiert sind
- wie AstroManager diese Quelle fachlich einordnet
- welche Standardstruktur AstroManager von dieser Quelle erwartet

Wichtig:
- IP, Benutzername und Passwort werden über die UI eingetragen
- das Passwort wird verschlüsselt in der DB gespeichert
- die Verschlüsselung muss reversibel sein
- das Modell darf nicht nur DWARF3 abdecken, sondern auch andere Smart-Teleskope

---

## 3. Was in den letzten Überlegungen zusätzlich klar wurde

Neben der reinen Quellenanlage wurden folgende Punkte als wichtig erkannt:

1. `device_sources` darf nicht nur Gerät + Protokoll + Root speichern, sondern muss das komplette UI-Template abbilden.
2. Passwortspeicherung darf nicht nur Hashing sein, sondern reversible Verschlüsselung.
3. Andere Smart-Teleskope haben unterschiedliche Datenmodelle:
   - dateisystem-/sessionbasiert
   - observationbasiert
   - bundle-/exportbasiert
   - hybride Gerät/App-Modelle
4. Die DB braucht zusätzliche Ebenen für:
   - Session-Ergebnisse
   - Gruppen-/Mega-Stacks
   - finale Produkte
   - Kalibrationszuordnung
5. Bestehende Tabellen sollen bevorzugt sinnvoll erweitert werden, statt unnötig viele neue Tabellen einzuführen.

---

## 4. Erkenntnisse aus anderen Smart-Teleskopen

### 4.1 DWARF 3
DWARF 3 ist stark dateisystem- und ordnerorientiert.

Typische relevante Bereiche:
- Astronomy
- Atlas
- CALI_FRAME
- DWARF_DARK
- DWARF_RAW
- Solving_Failed
- Restacked
- Panoramas
- Videos
- Burst
- Normal Photos

Eigenschaften:
- Sessions häufig direkt über Ordner- und Dateinamen identifizierbar
- Sonderkategorien wie Sun, Moon, Panorama, Restacked, Solving_Failed sind wichtig
- Rohdaten und derive Produkte liegen häufig parallel

### 4.2 Vaonis Vespera
Vaonis ist eher observation-basiert organisiert.

Eigenschaften:
- Daten pro Beobachtung
- innerhalb einer Beobachtung Unterbereiche wie initial framing und adjusted framing
- Metadaten und Expertenmodus spielen größere Rolle
- nicht nur simple Session-Ordner

### 4.3 Unistellar
Unistellar ist stärker export-/bundleorientiert.

Eigenschaften:
- Beobachtungen eher als auswählbare Einheiten
- Export über UI/Bundle-Konzept
- weniger klassischer offener Dateisystem-Sync

### 4.4 Seestar
Seestar zeigt eher ein Mischmodell.

Eigenschaften:
- Teile der Daten auf dem Gerät
- Teile eher im App-/Mobil-Kontext
- je nach Modus unterschiedliche Ablage und Sichtbarkeit

### Konsequenz
`device_sources` darf nicht nur FTP + Root-Ordner modellieren, sondern muss auch den Datenmodell-Typ und die Zugriffsart beschreiben.

---

## 5. Das UI-Template für eine Datenquelle

Das UI soll eine Datenquelle in fachlich klaren Blöcken erfassen.

### 5.1 Allgemein
- Name
- Quellschlüssel
- Beschreibung
- Gerätetyp
- Aktiv / deaktiviert

### 5.2 Verbindung
- Protokoll
- Zugriffsart
- Host / IP
- Port
- Benutzername
- Passwort
- Verbindungstimeout

### 5.3 Datenmodell
- Datenmodell-Typ
- Ordnerlayout
- Session-Erkennung
- Remote Root
- Astronomy Root
- Atlas Root
- Calibration Root
- lokaler Rohdaten-Präfix

### 5.4 Fachliche Zuordnung
- Kategorie-Modus
- Solar unterstützt
- Mond unterstützt
- Mosaik unterstützt
- Panorama unterstützt
- Startrails unterstützt
- Kalibration separat gespeichert
- Metadaten-Dateien vorhanden
- direkte Dateisystem-Navigation möglich
- Bundle-/Exportmodell vorhanden

### 5.5 Status / Notizen
- letzter Kontakt
- letzter Sync
- letzter Status
- letzter Fehler
- interne Notizen

---

## 6. Was das UI-Template fachlich können muss

Das Quellen-Template soll folgende Geräteklassen abbilden können:

- klassisches Dateisystem-Gerät
- observation-orientiertes Gerät
- export-/bundle-orientiertes Gerät
- hybrides Gerät mit App-/Mobil-Anteil
- generische FTP-/SFTP-/Import-Quelle

Das Template muss also nicht nur Verbindungsdaten aufnehmen, sondern die fachliche Struktur der Quelldaten.

---

## 7. Empfohlene Erweiterung von device_sources

Die Tabelle `device_sources` soll von einer groben Gerätebeschreibung zu einem vollständigen UI-/Quellenmodell ausgebaut werden.

### 7.1 Bereits vorhanden bzw. sinngemäß vorhanden
- id
- source_key
- vendor
- model
- family
- protocol
- root_pattern
- notes

### 7.2 Empfohlene zusätzliche Felder – Identität / UI
- name
- description
- device_type
- is_enabled

### 7.3 Empfohlene zusätzliche Felder – Zugriff / Verbindung
- access_mode
- host
- port
- username
- password_enc
- password_nonce
- password_alg
- connect_timeout_sec

### 7.4 Empfohlene zusätzliche Felder – Datenmodell / Struktur
- data_model_type
- folder_layout
- session_detection_mode
- remote_root
- astronomy_root
- atlas_root
- calibration_root
- local_raw_prefix

### 7.5 Empfohlene zusätzliche Felder – Fachliche Zuordnung
- category_mode
- supports_solar
- supports_moon
- supports_mosaic
- supports_panorama
- supports_startrails
- stores_calibration_separately
- stores_metadata_json
- supports_direct_fs_browsing
- supports_observation_bundle_export

### 7.6 Empfohlene zusätzliche Felder – Status / Diagnose
- last_seen_at
- last_sync_at
- last_sync_status
- last_error
- created_at
- updated_at

---

## 8. Warum das Passwort nicht gehasht werden darf

Das Passwort muss später für FTP, SFTP oder andere Zugriffe wieder verwendet werden können.

Deshalb gilt:
- Hashing ist ungeeignet
- es braucht reversible Verschlüsselung

### Empfohlenes Konzept
In der DB speichern:
- `password_enc`
- `password_nonce`
- `password_alg`

Nicht in der DB speichern:
- Klartextpasswort
- Schlüsselmaterial

Das Schlüsselmaterial soll außerhalb der Tabelle liegen, zum Beispiel:
- in einer App-Key-Datei unter `/config`
- oder als Container-/Runtime-Secret

### Technische Kernaussage
- UI nimmt Klartextpasswort entgegen
- Backend verschlüsselt
- DB speichert nur Ciphertext + Nonce + Algorithmus
- Backend entschlüsselt bei Bedarf zur Laufzeit

---

## 9. Empfohlene Enumerationen für device_sources

### 9.1 device_type
Beispiele:
- DWARF3
- DWARF2
- VESPERA
- UNISTELLAR
- SEESTAR
- GENERIC_FTP
- LOCAL_IMPORT

### 9.2 access_mode
Beispiele:
- ftp_fs
- sftp_fs
- usb_mass_storage
- http_data_ui
- smb
- manual_import

### 9.3 data_model_type
Beispiele:
- session_folders
- observation_folders
- bundle_export
- mixed_device_app

### 9.4 folder_layout
Beispiele:
- dwarf_standard
- observation_standard
- flat_remote_tree
- custom

### 9.5 session_detection_mode
Beispiele:
- folder_name
- fits_header
- hybrid

### 9.6 category_mode
Beispiele:
- auto
- astronomy_only
- atlas_only

---

## 10. Geräte-Presets, die später im UI vorbelegt werden können

### 10.1 Preset DWARF3
Empfohlene Defaults:
- protocol = ftp
- access_mode = ftp_fs
- data_model_type = session_folders
- folder_layout = dwarf_standard
- session_detection_mode = hybrid
- remote_root = /DWARF_Album
- astronomy_root = Astronomy
- atlas_root = Atlas

### 10.2 Preset VESPERA
Empfohlene Defaults:
- data_model_type = observation_folders
- folder_layout = observation_standard

### 10.3 Preset UNISTELLAR
Empfohlene Defaults:
- data_model_type = bundle_export
- access_mode = http_data_ui

### 10.4 Preset SEESTAR
Empfohlene Defaults:
- data_model_type = mixed_device_app

Diese Presets sind fachliche Startwerte, keine endgültige technische Implementierung.

---

## 11. Welche Tabellen im aktuellen Schema fehlen

Es fehlen nicht beliebig viele Tabellen, sondern gezielt die Verarbeitungs- und Ergebnis-Ebenen.

### 11.1 session_stacks
Zweck:
Ein konkretes Ergebnis einer einzelnen Session modellieren.

Empfohlene Felder:
- id
- session_id
- stack_version
- stack_role
- status
- stack_method
- input_frame_count
- used_frame_count
- rejected_frame_count
- integration_seconds
- masterdark_asset_id
- output_fits_path
- output_png_path
- output_jpg_path
- preview_path
- weighting_method
- qc_score
- note
- job_run_id
- created_at
- finished_at

### 11.2 group_stacks
Zweck:
Versionierte Gesamt- oder Gruppen-Stacks über mehrere Sessions desselben Targets mit identischem Capture-Profil.

Empfohlene Felder:
- id
- group_key
- target_id
- category
- filter_set
- exp
- gain
- binning
- group_scope
- version_no
- status
- session_count
- total_input_frames
- total_integration_seconds
- output_fits_path
- output_png_path
- output_jpg_path
- preview_path
- quality_score
- is_current
- job_run_id
- created_at
- finished_at

### 11.3 group_stack_members
Zweck:
Dokumentieren, welche Sessions bzw. Session-Stacks in einer bestimmten Gruppen-Version enthalten sind.

Empfohlene Felder:
- id
- group_stack_id
- session_id
- session_stack_id
- member_order
- created_at

### 11.4 final_products
Zweck:
Saubere Trennung zwischen technischen Zwischenprodukten und finalen, im UI oder extern relevanten Ergebnissen.

Empfohlene Felder:
- id
- target_id
- source_kind
- source_ref_id
- product_type
- variant_name
- abs_path
- rel_path
- file_size
- sha256
- width_px
- height_px
- is_published
- is_current
- rating
- note
- created_at

### 11.5 calibration_matches
Zweck:
Speichern, welche Kalibration konkret welchem Session- oder Stack-Ergebnis zugeordnet wurde.

Empfohlene Felder:
- id
- session_id
- session_stack_id
- calibration_asset_id
- match_type
- match_score
- match_reason
- created_at

---

## 12. Tabellen, die später zusätzlich sinnvoll sein können

Noch nicht sofort Pflicht, aber vorbereitet mitdenken:

### 12.1 mosaic_projects
Für Mosaik-Projekte als eigene Kategorie.

### 12.2 mosaic_tiles
Für die einzelnen Kacheln innerhalb eines Mosaiks.

### 12.3 Weitere spätere Sonderpfade
- panorama_projects
- startrail_projects
- lunar_products
- solar_products

Wichtig:
Sun und Moon bleiben trotzdem fachlich eigene Kategorien im Kernmodell und werden nicht als normaler DeepSky-Fall behandelt.

---

## 13. Welche bestehenden Tabellen sinnvoll erweitert werden sollten

### 13.1 sessions
Die Tabelle ist gut, aber noch nicht vollständig.

#### Solve / Identität
- solve_status
- solve_ra_deg
- solve_dec_deg
- solve_ref
- target_name_raw

#### Pipeline-Status
- index_status
- calibration_status
- registration_status
- stack_status
- preview_status

#### Klassifikation
- subtype
- session_family

#### Statistik
- light_frame_count
- badfit_frame_count
- defect_frame_count
- rejected_frame_count

#### Pfade
- work_dir
- products_dir

Begründung:
`sessions` soll nicht nur Indexeintrag sein, sondern echte Session-Zentrale.

---

### 13.2 raw_files
Die Tabelle ist bereits stark, aber bei Qualitäts- und Nutzungsdaten noch zu flach.

#### Qualitätsmetriken
- qc_score
- fwhm
- eccentricity
- snr_estimate
- background_level
- stars_detected

#### Verarbeitung
- registration_status
- calibration_status
- rejection_reason
- used_in_stack

#### Klassifikation
- object_category_guess
- target_guess
- capture_kind

Begründung:
Später braucht AstroManager Qualitätsfilter und Nutzungsnachweise je Rohdatei.

---

### 13.3 calibration_assets
Die Tabelle braucht mehr fachliche Kontextinformationen.

Sinnvolle Ergänzungen:
- profile_id
- quality_score
- valid_from
- valid_to
- is_master
- source_session_id
- asset_status
- note

Begründung:
Ein Kalibrations-Asset muss nicht nur existieren, sondern fachlich bewertbar und zeitlich einordenbar sein.

---

### 13.4 targets
`targets` ist schon weit, aber noch zu extern-resolverlastig.

Sinnvolle Ergänzungen:
- is_solar_system
- is_placeholder
- review_status
- preferred_image_product_id
- stack_count
- session_count
- total_integration_seconds
- last_session_at

Begründung:
Die Tabelle soll nicht nur Wissen über Zielobjekte enthalten, sondern auch den internen AstroManager-Kontext.

---

### 13.5 capture_profiles
Sinnvolle Ergänzungen:
- profile_kind
- temp_nominal
- filter_name_raw
- camera_mode
- notes

Begründung:
Damit wird die Tabelle auch für spätere Kalibrations- und Spezialfälle tragfähiger.

---

### 13.6 job_runs
Die Tabelle ist als Startpunkt okay, aber noch grob.

Sinnvolle Ergänzungen:
- entity_type
- entity_id
- action_name
- progress_percent
- result_json
- error_code

Begründung:
Jobs müssen später sauber einer Quelle, Session oder Stack-Version zugeordnet werden können.

---

## 14. Was bewusst noch nicht als eigene Tabelle nötig ist

Diese Dinge sollten vorerst nicht künstlich ausgelagert werden:

- kein extra session_previews
- kein extra target_aliases
- kein extra source_types

Begründung:
Die Komplexität soll schrittweise wachsen. Erst die Kernpfade modellieren.

---

## 15. Zusammenhang zur späteren Workflow-Logik

Auch wenn dieses Dokument noch kein Workflow-Dokument ist, muss das Modell später zu diesen Verarbeitungsstufen passen:

1. Quelle anlegen / pflegen
2. Quelle prüfen / inventarisieren
3. Rohdaten indexieren
4. Sessions bilden / klassifizieren
5. Kalibration zuordnen
6. Session-Stacks erzeugen
7. Gruppen-/Mega-Stacks erzeugen
8. finale Produkte verwalten

Das Datenmodell muss also sowohl UI-Stammdaten als auch spätere Pipeline-Verarbeitung tragen.

---

## 16. Priorisierung

### Sofort sinnvoll
1. `device_sources` fachlich auf UI-Niveau anheben
2. reversible Passwortverschlüsselung definieren
3. `session_stacks` anlegen
4. `group_stacks` anlegen
5. `group_stack_members` anlegen
6. `final_products` anlegen
7. `calibration_matches` anlegen

### Danach
8. `sessions` erweitern
9. `raw_files` erweitern
10. `calibration_assets` erweitern
11. `targets` ergänzen
12. `job_runs` verfeinern

### Später
13. `mosaic_projects`
14. `mosaic_tiles`
15. weitere Sonderpfade für Panorama und Startrails

---

## 17. Empfehlung für die Umsetzung

Die Umsetzung sollte in dieser Reihenfolge erfolgen:

### Schritt 1
`device_sources` finalisieren, weil dies die Grundlage für das UI-Quellenformular ist.

### Schritt 2
Passwortverschlüsselung definieren:
- UI nimmt Klartext entgegen
- Backend verschlüsselt
- DB speichert `password_enc`, `password_nonce`, `password_alg`
- Schlüsselmaterial liegt nicht in der Tabelle

### Schritt 3
`session_stacks` einführen, damit Session-Ergebnisse nicht nur indirekt über Pfade existieren.

### Schritt 4
`group_stacks` + `group_stack_members` einführen, damit versionierte Mega-/Gesamt-Stacks sauber modelliert werden.

### Schritt 5
`final_products` und `calibration_matches` ergänzen, damit Endprodukte und Kalibrationsverwendung nachvollziehbar werden.

---

## 18. Kernaussage

Es fehlen nicht einfach „mehr Tabellen“, sondern vor allem diese vier fachlichen Ebenen:

1. Datenquelle sauber als UI-/DB-Modell
2. Verbindungsdaten sicher und entschlüsselbar speichern
3. Verarbeitungsergebnisse pro Session und Gruppe modellieren
4. finale Produkte und Kalibrationszuordnung nachvollziehbar machen

Wenn diese Ebenen sauber stehen, kann AstroManager die bestehende Session-/Raw-/Target-Basis deutlich robuster und zukunftssicherer ausbauen.

