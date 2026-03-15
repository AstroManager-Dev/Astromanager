#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
# shellcheck source=/dev/null
source "$ROOT/lib/pipeline_env.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

LOG="${LOG_ROOT}/master/siril_group_dummy.log"
mkdir -p "$(dirname "$LOG")"

log "DUMMY siril group stack started"
log "WORK_ROOT=$WORK_ROOT"
log "CATALOG_ROOT=$CATALOG_ROOT"
log "No real siril group stack executed"
log "DUMMY siril group stack finished"
