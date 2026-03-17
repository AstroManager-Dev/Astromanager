# RAW file viewer context signature fix

## Problem
The raw file detail page and FITS preview endpoint called `enrich_raw_file_viewer_context()` with the newer viewer parameters `stretch`, `black`, `white`, and `gamma`, while the function still accepted only `view` and `debayer`.

## Fix
- make the additional viewer arguments optional
- preserve compatibility with older callers
- generate FITS detail URLs with the active stretch/black/white/gamma values
- keep thumbnail URLs lightweight

## Dry run
- open `/raw-files/<id>?view=fits&debayer=auto&stretch=auto&black=0.500&white=99.500&gamma=1.000`
- verify the page no longer raises `unexpected keyword argument 'stretch'`
