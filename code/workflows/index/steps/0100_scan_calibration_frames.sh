#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local base="${RAW_ROOT%/}/Astronomy/CALI_FRAME"
  local state_root="${STATE_DIR_ARG%/}/index_sessions/cali_frame"

  asset_signature() {
    local dir="$1"
    find "$dir" -type f -name '*.fits' -printf '%P|%s|%T@\n' | LC_ALL=C sort | sha1sum | awk '{print $1}'
  }

  asset_state_file() {
    local dir="$1"
    local digest
    digest="$(printf '%s' "$dir" | sha1sum | awk '{print $1}')"
    printf '%s/%s.state\n' "$state_root" "$digest"
  }

  asset_should_skip() {
    local sig="$1"
    local state_file="$2"
    local old_sig=""

    [[ "${FULL_SCAN:-0}" -eq 1 ]] && return 1
    [[ "${DRY_RUN:-0}" -eq 1 ]] && return 1
    [[ -f "$state_file" ]] || return 1

    old_sig="$(sed -n '1p' "$state_file" 2>/dev/null || true)"
    [[ -n "$old_sig" && "$old_sig" == "$sig" ]]
  }

  asset_write_state() {
    local state_file="$1"
    local sig="$2"
    local dir="$3"
    local ts
    ts="$(date +'%F %T')"
    mkdir -p "$(dirname "$state_file")"
    {
      printf '%s\n' "$sig"
      printf '%s\n' "$ts"
      printf '%s\n' "$dir"
    } > "$state_file"
  }

  [[ -d "$base" ]] || { log "scan cali_frame: missing: $base"; return 0; }

  mkdir -p "$state_root"
  log "scan cali_frame: $base"

  while IFS= read -r -d '' asset_dir; do
    local dir_sig="" state_file=""

    dir_sig="$(asset_signature "$asset_dir")"
    state_file="$(asset_state_file "$asset_dir")"

    if asset_should_skip "$dir_sig" "$state_file"; then
      sessions_skipped_unchanged=$((sessions_skipped_unchanged + 1))
      log "scan cali_frame: skip unchanged: $asset_dir"
      continue
    fi

    while IFS= read -r -d '' f; do
      local rel parent_dir file_name size_bytes mtime_epoch sha256
      local asset_type="" camera="" exp="" gain="" binning="" temp_c="" stack_count="" ir_index=""
      local meta_source

      rel="${f#${RAW_ROOT%/}/}"
      parent_dir="$(dirname "$f")"
      file_name="$(basename "$f")"

      case "$rel" in
        Astronomy/CALI_FRAME/dark/*) asset_type="dark" ;;
        Astronomy/CALI_FRAME/bias/*) asset_type="bias" ;;
        Astronomy/CALI_FRAME/flat/*) asset_type="flat" ;;
        *) asset_type="unknown" ;;
      esac

      case "$rel" in
        */cam_0/*) camera="cam_0" ;;
        */cam_1/*) camera="cam_1" ;;
        *) camera="" ;;
      esac

      if [[ "$file_name" =~ ^dark_exp_([0-9.]+)_gain_([0-9]+)_bin_([0-9]+)_([0-9]+)C_stack_([0-9]+)\.fits$ ]]; then
        exp="${BASH_REMATCH[1]}"
        gain="${BASH_REMATCH[2]}"
        binning="${BASH_REMATCH[3]}"
        temp_c="${BASH_REMATCH[4]}"
        stack_count="${BASH_REMATCH[5]}"
      elif [[ "$file_name" =~ ^bias_gain_([0-9]+)_bin_([0-9]+)\.fits$ ]]; then
        gain="${BASH_REMATCH[1]}"
        binning="${BASH_REMATCH[2]}"
      elif [[ "$file_name" =~ ^flat_gain_([0-9]+)_bin_([0-9]+)(_ir_([0-9]+))?\.fits$ ]]; then
        gain="${BASH_REMATCH[1]}"
        binning="${BASH_REMATCH[2]}"
        [[ -n "${BASH_REMATCH[4]:-}" ]] && ir_index="${BASH_REMATCH[4]}"
      fi

      IFS='|' read -r meta_source size_bytes mtime_epoch sha256 _ _ _ _ _ _ _ _ _ _ _ _ _ _ <<< "$(get_file_meta "$f" "$parent_dir" "$file_name" "unknown")"

      if [[ "$meta_source" == "cached" ]]; then
        files_reused=$((files_reused + 1))
      else
        files_hashed=$((files_hashed + 1))
      fi

      upsert_calibration_asset \
        "$asset_type" \
        "dwarf_cali_frame" \
        "$camera" \
        "$f" \
        "$rel" \
        "$size_bytes" \
        "$mtime_epoch" \
        "$sha256" \
        "$exp" \
        "$gain" \
        "$binning" \
        "$temp_c" \
        "$stack_count" \
        "$ir_index"

      upsert_raw_file \
        "cali_frame" \
        "$asset_type" \
        "$f" \
        "$rel" \
        "$parent_dir" \
        "$file_name" \
        "$size_bytes" \
        "$mtime_epoch" \
        "$sha256" \
        "" \
        "unknown" \
        "ok" \
        "" \
        "" \
        0 \
        0 \
        "" \
        "" \
        "" \
        "" \
        "" \
        "" \
        "" \
        "" \
        "" \
        "" \
        0 \
        0 \
        "$exp" \
        "$gain" \
        "$temp_c" \
        "$binning" \
        "$camera"

      files_indexed=$((files_indexed + 1))
      cal_assets_indexed=$((cal_assets_indexed + 1))
      progress_maybe_log
    done < <(find "$asset_dir" -type f -name '*.fits' -print0 | sort -z)

    asset_write_state "$state_file" "$dir_sig" "$asset_dir"
  done < <(find "$base" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
}
