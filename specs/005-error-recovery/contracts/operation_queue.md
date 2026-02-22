# Operation Queue Interface

**Purpose**: Queue operations when external services are unavailable

## Interface Definition

### `OperationQueue(service_name: str, vault_path: str)`

Queue manager for a specific service.

**Parameters**:
- `service_name` (str): Name of the service (e.g., "gmail_api", "linkedin_api")
- `vault_path` (str): Path to AI_Employee_Vault

**Methods**:

#### `enqueue(operation_type: str, payload: dict, priority: int = 5) -> str`

Add an operation to the queue.

**Parameters**:
- `operation_type` (str): Type of operation (e.g., "send_email", "post_linkedin")
- `payload` (dict): Operation-specific data
- `priority` (int): Priority level (1=highest, 10=lowest)

**Returns**:
- `operation_id` (str): UUID of the queued operation

**Behavior**:
1. Create QueuedOperation object
2. Validate payload (no sensitive data in plain text)
3. Write to pending queue directory
4. Log queue event
5. Return operation_id

**Example Usage**:
```python
from error_recovery import OperationQueue

queue = OperationQueue("gmail_api", "AI_Employee_Vault")

operation_id = queue.enqueue(
    operation_type="send_email",
    payload={
        "to": "client@example.com",
        "subject": "Invoice #1234",
        "body": "Please find attached...",
        "attachment_path": "/vault/Invoices/2026-01_Client_A.pdf"
    },
    priority=5
)
```

---

#### `process_queue() -> List[str]`

Process all pending operations in the queue.

**Returns**:
- List of operation_ids that were processed (successfully or failed)

**Behavior**:
1. List all files in pending directory
2. Sort by timestamp (oldest first), then by priority
3. For each operation:
   - Load operation from file
   - Attempt execution
   - If succeeds: Move to completed directory
   - If fails: Increment retry_count
   - If retry_count < max_retries: Update scheduled_for, keep in pending
   - If retry_count >= max_retries: Move to failed directory
4. Return list of processed operation_ids

---

#### `get_queue_size() -> int`

Get number of pending operations.

**Returns**:
- Count of operations in pending directory

---

#### `get_pending_operations() -> List[QueuedOperation]`

Get all pending operations.

**Returns**:
- List of QueuedOperation objects

---

#### `cancel_operation(operation_id: str) -> bool`

Cancel a pending operation.

**Parameters**:
- `operation_id` (str): UUID of operation to cancel

**Returns**:
- `success` (bool): Whether cancellation succeeded

**Behavior**:
1. Find operation file in pending directory
2. Delete file
3. Log cancellation event

---

## Queue Processing Strategy

**Automatic Processing**:
- Watchdog triggers queue processing every 5 minutes
- Each component checks queue before attempting new operations

**Priority Handling**:
- Operations sorted by priority (1=highest)
- Within same priority, FIFO (oldest first)

**Retry Strategy**:
- Failed operations retry with exponential backoff
- Max 3 retries per operation
- After max retries, move to failed directory

---

## Configuration

```python
class OperationQueueConfig:
    vault_path: str = "AI_Employee_Vault"
    max_retries: int = 3
    base_retry_delay: int = 300  # 5 minutes
    max_queue_size: int = 100
    processing_interval: int = 300  # 5 minutes
    cleanup_completed_after_days: int = 7
    cleanup_failed_after_days: int = 30
```
