#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError

from astromanager.targets.wikidata_match_utils import norm, row_search_terms

TIMEOUT = float(os.environ.get("WIKIDATA_TIMEOUT", "20"))
USER_AGENT = os.environ.get("WIKIDATA_UA", "AstroManager/1.0")
SEARCH_LIMIT = int(os.environ.get("WIKIDATA_SEARCH_LIMIT", "10"))
WIKIDATA_RETRIES = int(os.environ.get("WIKIDATA_RETRIES", "4"))
WIKIDATA_RETRY_SLEEP = float(os.environ.get("WIKIDATA_RETRY_SLEEP", "1.5"))

SEARCH_URL = (
    "https://www.wikidata.org/w/api.php"
    "?action=wbsearchentities&format=json&language=en&type=item&limit={limit}&search="
)
GET_URL = (
    "https://www.wikidata.org/w/api.php"
    "?action=wbgetentities&format=json&languages=de|en&sitefilter=dewiki|enwiki"
    "&props=labels|aliases|sitelinks|claims&ids="
)
SPARQL_URL = os.environ.get("WIKIDATA_SPARQL_URL", "https://query.wikidata.org/sparql")

_JSON_CACHE = {}


def http_json(url: str, method: str = "GET", data: bytes | None = None):
    cache_key = (method, url, data.decode("utf-8", "replace") if data else "")
    if cache_key in _JSON_CACHE:
        return _JSON_CACHE[cache_key]

    last_error = None
    for attempt in range(WIKIDATA_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
            _JSON_CACHE[cache_key] = payload
            return payload
        except HTTPError as e:
            last_error = e
            if e.code == 429 and attempt < WIKIDATA_RETRIES:
                time.sleep(WIKIDATA_RETRY_SLEEP * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_error = e
            if attempt < WIKIDATA_RETRIES:
                time.sleep(WIKIDATA_RETRY_SLEEP * (attempt + 1))
                continue
            raise

    raise last_error


def sparql_json(query: str):
    data = urllib.parse.urlencode({"query": query}).encode("utf-8")
    cache_key = ("POST", SPARQL_URL, query)
    if cache_key in _JSON_CACHE:
        return _JSON_CACHE[cache_key]

    last_error = None
    for attempt in range(WIKIDATA_RETRIES + 1):
        try:
            req = urllib.request.Request(
                SPARQL_URL,
                data=data,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/sparql-results+json, application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
            _JSON_CACHE[cache_key] = payload
            return payload
        except HTTPError as e:
            last_error = e
            if e.code == 429 and attempt < WIKIDATA_RETRIES:
                time.sleep(WIKIDATA_RETRY_SLEEP * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_error = e
            if attempt < WIKIDATA_RETRIES:
                time.sleep(WIKIDATA_RETRY_SLEEP * (attempt + 1))
                continue
            raise

    raise last_error


def search_entities(term: str) -> list[dict]:
    term = norm(term)
    if not term:
        return []
    data = http_json(SEARCH_URL.format(limit=SEARCH_LIMIT) + urllib.parse.quote(term))
    return data.get("search", [])


def get_entity(qid: str) -> dict:
    qid = norm(qid)
    if not qid:
        return {}
    data = http_json(GET_URL + urllib.parse.quote(qid))
    return data.get("entities", {}).get(qid, {})


def exact_catalog_qids(term: str) -> list[str]:
    term = norm(term)
    if not term:
        return []

    term_escaped = term.replace("\\", "\\\\").replace('"', '\\"')

    query = f"""
SELECT DISTINCT ?item WHERE {{
  {{
    ?item wdt:P528 "{term_escaped}" .
  }}
  UNION
  {{
    ?item wdt:P373 "{term_escaped}" .
  }}
}}
LIMIT 25
""".strip()

    data = sparql_json(query)
    qids = []
    for row in data.get("results", {}).get("bindings", []):
        uri = row.get("item", {}).get("value", "")
        if not uri:
            continue
        qid = norm(uri.rsplit("/", 1)[-1])
        if qid and qid not in qids:
            qids.append(qid)
    return qids


def collect_candidates(row) -> dict:
    aggregated = {}

    for term in row_search_terms(row):
        exact_qids = exact_catalog_qids(term)
        for qid in exact_qids:
            entry = aggregated.setdefault(
                qid,
                {
                    "hit": {
                        "id": qid,
                        "label": "",
                        "match": {"text": term},
                        "description": "exact catalog identifier lookup",
                    },
                    "terms": [],
                    "sources": [],
                },
            )
            if term not in entry["terms"]:
                entry["terms"].append(term)
            if "catalog_exact" not in entry["sources"]:
                entry["sources"].append("catalog_exact")

        for hit in search_entities(term):
            qid = norm(hit.get("id", ""))
            if not qid:
                continue

            entry = aggregated.setdefault(
                qid,
                {
                    "hit": hit,
                    "terms": [],
                    "sources": [],
                },
            )
            if term not in entry["terms"]:
                entry["terms"].append(term)
            if "wbsearch" not in entry["sources"]:
                entry["sources"].append("wbsearch")

    return aggregated
