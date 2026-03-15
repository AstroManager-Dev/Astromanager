#!/usr/bin/env bash

: "${TARGET_RESOLVER_TIMEOUT:=20}"

: "${OPENNGC_CSV_URL:=https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/NGC.csv}"
: "${OPENNGC_CSV_LOCAL:=/app/catalog/_db/openngc.csv}"
: "${OPENNGC_MAX_AGE_DAYS:=30}"

: "${SIMBAD_BASE_URL:=https://simbad.cds.unistra.fr/simbad/sim-id}"
: "${NED_URL:=https://ned.ipac.caltech.edu/srs/ObjectLookup}"
: "${VIZIER_BASE_URL:=https://vizier.cds.unistra.fr/viz-bin/asu-tsv}"
: "${VIZIER_SOURCE:=VII/239}"
: "${VIZIER_RADIUS:=0.2}"

: "${WIKIDATA_SEARCH_URL:=https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=item&limit=10&search=}"
: "${WIKIDATA_GET_URL:=https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&languages=de|en&sitefilter=dewiki|enwiki&props=labels|aliases|sitelinks|claims&ids=}"

: "${NASA_IMAGE_SEARCH_URL:=https://images-api.nasa.gov/search}"
: "${SKYVIEW_BASE_URL:=https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl}"
: "${IRSA_FINDER_BASE_URL:=https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api}"
