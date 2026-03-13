from . import dev_tools, index_sessions, master_darks, raw_sync, siril_group, siril_session, status

ACTION_HANDLERS = {
    "raw_sync": raw_sync.handle,
    "index_sessions": index_sessions.handle,
    "masterdarks": master_darks.handle,
    "siril_session": siril_session.handle,
    "siril_group": siril_group.handle,
    "status": status.handle,
    "backup_create": dev_tools.backup_handle,
    "sql_dump": dev_tools.sql_dump_handle,
    "organizer_refresh": dev_tools.organizer_refresh_handle,
}
