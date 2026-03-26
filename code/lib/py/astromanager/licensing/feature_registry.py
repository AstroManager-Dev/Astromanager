from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class FeatureDef:
    code: str
    label: str
    area: str
    summary: str


FEATURES: Final[dict[str, FeatureDef]] = {
    "core.import": FeatureDef(
        code="core.import",
        label="Import und Quellenzugriff",
        area="core",
        summary="Grundlegender Import, Datenquellenzugriff und Dateierkennung.",
    ),
    "core.viewer": FeatureDef(
        code="core.viewer",
        label="Viewer",
        area="core",
        summary="RAW-, FITS- und Session-Viewer ohne produktive Verarbeitung.",
    ),
    "core.targets": FeatureDef(
        code="core.targets",
        label="Targets",
        area="core",
        summary="Target-Listen, Target-Detail und Resolver-Ergebnisse anzeigen.",
    ),
    "core.sessions": FeatureDef(
        code="core.sessions",
        label="Sessions",
        area="core",
        summary="Session-Listen, Session-Detail und RAW-Zuordnung anzeigen.",
    ),
    "core.atlas_basic": FeatureDef(
        code="core.atlas_basic",
        label="Atlas Basis",
        area="atlas",
        summary="Grundatlas ohne Planungs- oder Bilddaten-Layer.",
    ),
    "core.stacking": FeatureDef(
        code="core.stacking",
        label="Siril-Stacking",
        area="processing",
        summary="Produktive Siril-Stacking- und Restack-Workflows.",
    ),
    "plus.progress": FeatureDef(
        code="plus.progress",
        label="Target-Fortschritt",
        area="planning",
        summary="Soll-/Ist-Belichtungszeit, Restzeit und Status pro Target.",
    ),
    "plus.planning": FeatureDef(
        code="plus.planning",
        label="Planungskalender",
        area="planning",
        summary="Planung der nächsten Nächte, Slots und Session-Vorschläge.",
    ),
    "plus.visibility": FeatureDef(
        code="plus.visibility",
        label="Sichtbarkeiten",
        area="planning",
        summary="Mindesthöhe, Mindestdauer, Mondabstand und Nachtfenster.",
    ),
    "plus.recommendations": FeatureDef(
        code="plus.recommendations",
        label="Empfehlungen",
        area="planning",
        summary="Empfehlungslogik für nächste Sessions und beste nächste Aktion.",
    ),
    "plus.weather_basic": FeatureDef(
        code="plus.weather_basic",
        label="Wetter Basis",
        area="weather",
        summary="Basis-Wetterdaten und einfache Nachtbewertung.",
    ),
    "plus.atlas_filters": FeatureDef(
        code="plus.atlas_filters",
        label="Atlas Planungsfilter",
        area="atlas",
        summary="Atlas-Filter für Sichtbarkeit, Fortschritt und Planungsstatus.",
    ),
    "pro.atlas_imagery": FeatureDef(
        code="pro.atlas_imagery",
        label="Atlas Bilddaten",
        area="atlas",
        summary="Eigene Bilddaten, Overlays und zuschaltbare Bildlayer im Atlas.",
    ),
    "pro.footprints": FeatureDef(
        code="pro.footprints",
        label="Session-Footprints",
        area="atlas",
        summary="Session-Footprints mit Zentrum, Rotation, FOV und Verlinkung.",
    ),
    "pro.coverage": FeatureDef(
        code="pro.coverage",
        label="Coverage und Mosaikabdeckung",
        area="atlas",
        summary="Abdeckungs- und Coverage-Layer inklusive Mosaik-Panels.",
    ),
    "pro.forecast_advanced": FeatureDef(
        code="pro.forecast_advanced",
        label="Astro-Forecast erweitert",
        area="weather",
        summary="Erweiterter Astro-Forecast inklusive Nachtqualitätslogik.",
    ),
    "pro.mosaic_progress": FeatureDef(
        code="pro.mosaic_progress",
        label="Mosaik- und Kanalfortschritt",
        area="planning",
        summary="Panel-, Filter- und Kanalfortschritt über mehrere Sessions.",
    ),
    "pro.ai_tools": FeatureDef(
        code="pro.ai_tools",
        label="KI-Analyse und Postproduktion",
        area="ai",
        summary="Spätere KI-gestützte Analyse-, Bewertungs- und Postproduktionswerkzeuge.",
    ),
}


FEATURE_ORDER: Final[tuple[str, ...]] = tuple(FEATURES.keys())
