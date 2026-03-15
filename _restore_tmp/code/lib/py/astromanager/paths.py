#!/usr/bin/env python3
import os

APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY_ROOT = os.path.join(APP_ROOT, "lib", "py")

TARGETS_LIB_DIR = os.path.join(LIB_PY_ROOT, "astromanager", "targets")
TARGET_NAME_PARSER_MODULE = "astromanager.targets.name_parser"
TARGET_RESOLVER_TABLE_SYNC_MODULE = "astromanager.targets.resolver_table_sync"
TARGET_SYNC_RESOLVER_TABLES_COMMAND_MODULE = "astromanager.commands.targets.sync_resolver_tables"
TARGET_SESAME_RESOLVER_MODULE = "astromanager.targets.sesame_resolver"
TARGET_RESOLVE_SESAME_COMMAND_MODULE = "astromanager.commands.targets.resolve_sesame"
TARGET_WIKIDATA_NAME_RESOLVER_MODULE = "astromanager.targets.wikidata_name_resolver"
TARGET_RESOLVE_WIKIDATA_NAME_COMMAND_MODULE = "astromanager.commands.targets.resolve_wikidata_names"
TARGET_SIMBAD_RESOLVER_MODULE = "astromanager.targets.simbad_resolver"
TARGET_RESOLVE_SIMBAD_COMMAND_MODULE = "astromanager.commands.targets.resolve_simbad"
TARGET_NED_RESOLVER_MODULE = "astromanager.targets.ned_resolver"
TARGET_RESOLVE_NED_COMMAND_MODULE = "astromanager.commands.targets.resolve_ned"
