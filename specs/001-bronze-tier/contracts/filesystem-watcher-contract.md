# File System Watcher Contract

## Purpose
Defines the interface for the file system watcher that monitors the Obsidian vault for new tasks in the /Needs_Action directory.

## Endpoints

### POST /watch/start
Start monitoring the specified directory for file changes.

**Request**:
```json
{
  "directory_path": "/path/to/vault/Needs_Action",
  "file_extensions": [".md"],
  "polling_interval": 30
}
```

**Response**:
```json
{
  "watcher_id": "unique-watcher-identifier",
  "status": "active",
  "directory_monitored": "/path/to/vault/Needs_Action",
  "started_at": "2026-01-14T10:00:00Z"
}
```

### GET /watch/{watcher_id}/status
Get the current status of the file system watcher.

**Response**:
```json
{
  "watcher_id": "unique-watcher-identifier",
  "status": "active",
  "directory_monitored": "/path/to/vault/Needs_Action",
  "last_change_detected": "2026-01-14T10:05:23Z",
  "files_processed_count": 5
}
```

### POST /watch/event
Triggered when a file system event occurs (used internally by the watcher).

**Request**:
```json
{
  "event_type": "created|modified|deleted",
  "file_path": "/path/to/vault/Needs_Action/new_task.md",
  "timestamp": "2026-01-14T10:05:23Z"
}
```

**Response**:
```json
{
  "event_id": "unique-event-identifier",
  "processed": true,
  "triggered_claude_processing": true,
  "processing_job_id": "claude-job-12345"
}
```