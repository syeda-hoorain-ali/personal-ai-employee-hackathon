# API Contract for File System Watcher Functionality

## Overview
This document describes the API contract for the file system watcher functionality in the Personal AI Employee system. The file system watcher monitors specific directories for changes and triggers appropriate actions based on detected changes.

## Components

### BaseWatcher (Abstract Base Class)
The `BaseWatcher` serves as the foundation for all watcher implementations.

#### Methods
- `__init__(vault_path: str, check_interval: int = 60)`
  - Initializes the watcher with the vault path and check interval
  - Validates that the vault path exists
  - Creates the `Needs_Action` directory if it doesn't exist
  - Validates that the check interval is positive
  - Sets up logging for the watcher

- `check_for_updates() -> list`
  - Abstract method to check for updates in the monitored location
  - Must be implemented by subclasses
  - Returns a list of detected items that need processing

- `create_action_file(item) -> Path`
  - Abstract method to create an action file in the `Needs_Action` directory
  - Must be implemented by subclasses
  - Returns the path to the created action file

- `run()`
  - Starts the watcher in an infinite loop
  - Calls `check_for_updates()` at regular intervals
  - For each returned item, calls `create_action_file()`
  - Includes error handling and logging
  - Sleeps for `check_interval` seconds between checks

#### Properties
- `vault_path`: Path to the Obsidian vault
- `Needs_Action`: Path to the `/Needs_Action` directory within the vault
- `check_interval`: Interval (in seconds) between checks
- `logger`: Logger instance for the watcher

### FileSystemWatcher
The `FileSystemWatcher` monitors file system changes, particularly in the `/Needs_Action` directory.

#### Methods
- `__init__(vault_path: str, watch_path: str = None)`
  - Initializes the file system watcher
  - If `watch_path` is not specified, defaults to `vault_path/Needs_Action`
  - Creates the watch path if it doesn't exist
  - Sets up the observer and event handler

- `start_monitoring()`
  - Begins monitoring the specified directory for file changes
  - Uses the watchdog library to monitor for file creation, modification, and deletion
  - Logs when monitoring starts

- `stop_monitoring()`
  - Stops monitoring the directory
  - Properly shuts down the observer

- `check_for_updates() -> list`
  - Implemented for compatibility with base class (returns empty list for event-driven watcher)

- `create_action_file(item) -> Path`
  - Implemented for compatibility with base class

#### Event Handlers
- `on_created(event)`
  - Triggered when a file is created in the monitored directory
  - Checks if the file has a `.md` extension
  - Copies the file to the `Needs_Action` directory with a `FILE_` prefix
  - Creates a metadata file with file information

- `on_modified(event)`
  - Triggered when a file is modified in the monitored directory
  - Logs the modification event

- `on_deleted(event)`
  - Triggered when a file is deleted in the monitored directory
  - Logs the deletion event

### DropFolderHandler
Handles file system events for the `FileSystemWatcher`.

#### Methods
- `__init__(vault_path: str)`
  - Initializes the handler with the vault path
  - Sets up the `Needs_Action` directory path
  - Sets up logging

- `on_created(event)`
  - Handles file creation events
  - Filters for `.md` files
  - Copies files to `Needs_Action` directory
  - Creates metadata files
  - Includes error handling

- `on_modified(event)`
  - Handles file modification events
  - Logs modification events
  - Includes error handling

- `on_deleted(event)`
  - Handles file deletion events
  - Logs deletion events
  - Includes error handling

- `create_metadata(source: Path, dest: Path)`
  - Creates a metadata file for the copied file
  - Includes file information like original name, size, and detection time
  - Includes error handling

## Configuration Parameters

### BaseWatcher Configuration
- `vault_path` (str): Path to the Obsidian vault directory
  - Required: Yes
  - Format: Absolute or relative path
  - Validation: Must exist and be accessible

- `check_interval` (int): Interval between checks in seconds
  - Required: No (defaults to 60)
  - Range: Positive integers only
  - Validation: Must be greater than 0

### FileSystemWatcher Configuration
- `watch_path` (str): Path to monitor for file changes
  - Required: No (defaults to `vault_path/Needs_Action`)
  - Format: Absolute or relative path
  - Validation: Directory will be created if it doesn't exist

## File Operations

### Input Files
- Monitored extensions: `.md` (Markdown files)
- Source locations: Configured watch path
- Processing trigger: File creation in monitored directory

### Output Files
- Action files: Copied to `Needs_Action` directory with `FILE_` prefix
- Metadata files: Created in `Needs_Action` directory with `_meta.md` suffix
- Metadata content includes:
  - `type`: Always set to "file_drop"
  - `original_name`: Original filename
  - `size`: File size in bytes
  - `detected_at`: Timestamp of detection
  - Basic description of the file drop

## Error Handling

### BaseWatcher Error Handling
- Invalid vault path: Raises `ValueError`
- Invalid check interval: Raises `ValueError`
- Runtime errors: Logged and handled gracefully
- Individual item processing errors: Caught and logged separately

### FileSystemWatcher Error Handling
- Missing credentials: Logged as error
- API connection issues: Handled with retry mechanism
- File system access issues: Logged and skipped
- Individual file processing errors: Caught and logged separately

## Logging

### Log Levels
- `INFO`: Starting/stopping watchers, successful operations
- `WARNING`: Skipped files, recoverable issues
- `ERROR`: Failed operations, configuration issues

### Log Content
- Timestamp
- Component name
- Log level
- Descriptive message

## Integration Points

### With Orchestrator
- Watchers register with the orchestrator via `add_watcher()`
- Orchestrator manages watcher lifecycle
- Watchers run in separate threads managed by orchestrator

### With File Processor
- Watchers create files in `Needs_Action` directory
- File processor monitors `Needs_Action` directory for new files
- Processed files are moved to appropriate destinations (`Done`, `Pending_Approval`, etc.)

### With Vault Reader/Writer
- Watchers may use vault writer to create action files
- Created files follow vault structure conventions
- Metadata files follow standardized format

## Security Considerations

- Only processes `.md` files to prevent arbitrary file processing
- Validates file paths to prevent directory traversal
- Logs all file operations for audit purposes
- Respects file system permissions