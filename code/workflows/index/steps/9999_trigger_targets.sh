#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause

step_run() {
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    log "index step 9999: skip target trigger in dry-run"
    return 0
  fi

  if [[ "${sessions_indexed:-0}" -le 0 ]]; then
    log "index step 9999: skip target trigger because sessions_indexed=0"
    return 0
  fi

  log "index step 9999: trigger targets resolve because sessions_indexed=${sessions_indexed}"
  "$ROOT/workflows/targets/resolve.sh" >>"$LOG" 2>&1
  log "index step 9999: targets resolve finished"
}
