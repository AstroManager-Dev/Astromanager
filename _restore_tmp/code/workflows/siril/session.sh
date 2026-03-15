#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
# shellcheck source=/dev/null
source "$ROOT/lib/pipeline_env.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

LOG="${LOG_ROOT}/master/siril_session_dummy.log"
mkdir -p "$(dirname "$LOG")"

log "DUMMY siril session started"
log "WORK_ROOT=$WORK_ROOT"
log "CATALOG_ROOT=$CATALOG_ROOT"
log "No real siril session processing executed"
log "DUMMY siril session finished"
