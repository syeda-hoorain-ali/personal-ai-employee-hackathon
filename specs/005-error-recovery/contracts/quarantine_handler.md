# Quarantine Handler Interface

**Purpose**: Isolate corrupted or invalid data files for manual review

## Interface Definition

### `QuarantineHandler(vault_path: str)`

Handler for quarantining corrupted files.

**Parameters**:
- `vault_path` (str): Path to AI_Employee_Vault

**Methods**:

#### `quarantine_file(file_path: str, error_reason: str, parsing_error: str, component: str) -> str`

Move a corrupted file to quarantine.

**Parameters**:
- `file_path` (str): Absolute path to the corrupted file
- `error_reason` (str): Brief reason (e.g., "Invalid YAML frontmatter")
- `parsing_error` (str): Detailed error message
- `component` (str): Component that detected the error

**Returns**:
- `quarantine_id` (str): UUID of the quarantined file

**Behavior**:
1. Calculate file hash (SHA-256)
2. Create quarantine directory for today if not exists
3. Move file to quarantine directory
4. Create metadata file (.meta.json) with QuarantinedFile data
5. Log quarantine event
6. Update dashboard with quarantine count
7. Return quarantine_id

**Example Usage**:
```python
from error_recovery import QuarantineHandler

handler = QuarantineHandler("AI_Employee_Vault")

try:
    data = parse_markdown_file("Needs_Action/EMAIL_12345.md")
except yaml.YAMLError as e:
    quarantine_id = handler.quarantine_file(
        file_path="Needs_Action/EMAIL_12345.md",
        error_reason="Invalid YAML frontmatter",
        parsing_error=str(e),
        component="file_processor"
    )
    logger.info(f"File quarantined: {quarantine_id}")
```

---

#### `restore_file(quarantine_id: str, destination: str) -> bool`

Restore a quarantined file to a specified location.

**Parameters**:
- `quarantine_id` (str): UUID of the quarantined file
- `destination` (str): Where to restore the file

**Returns**:
- `success` (bool): Whether restoration succeeded

**Behavior**:
1. Find quarantined file by ID
2. Copy file to destination
3. Update metadata (reviewed=True, action_taken=RESTORED)
4. Log restoration event
5. Keep original in quarantine for audit trail

---

#### `delete_quarantined_file(quarantine_id: str) -> bool`

Permanently delete a quarantined file.

**Parameters**:
- `quarantine_id` (str): UUID of the quarantined file

**Returns**:
- `success` (bool): Whether deletion succeeded

**Behavior**:
1. Find quarantined file by ID
2. Delete file and metadata
3. Log deletion event

---

#### `list_quarantined_files(reviewed: Optional[bool] = None) -> List[QuarantinedFile]`

List all quarantined files.

**Parameters**:
- `reviewed` (Optional[bool]): Filter by review status (None = all)

**Returns**:
- List of QuarantinedFile objects

---

#### `get_quarantine_stats() -> dict`

Get quarantine statistics.

**Returns**:
- Dictionary with counts:
  - `total`: Total quarantined files
  - `unreviewed`: Files not yet reviewed
  - `by_date`: Count per date
  - `by_component`: Count per component

---

## Configuration

```python
class QuarantineConfig:
    vault_path: str = "AI_Employee_Vault"
    quarantine_dir: str = "Quarantine"
    auto_cleanup_after_days: int = 90
    max_file_size_mb: int = 10  # Don't quarantine files larger than this
```
