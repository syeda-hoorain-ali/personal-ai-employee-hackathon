# Watchdog Interface

**Purpose**: Monitor component health and automatically restart crashed processes

## Interface Definition

### `Watchdog(components: List[ComponentConfig])`

Process monitor that checks health and restarts crashed components.

**Parameters**:
- `components` (List[ComponentConfig]): List of components to monitor

**Methods**:

#### `start() -> None`

Start the watchdog monitoring loop.

**Behavior**:
1. Load component health status from disk
2. Enter monitoring loop (runs every 60 seconds)
3. For each component:
   - Check if process is running (via PID)
   - If crashed: Log event, attempt restart
   - If restart fails 3 times in 5 minutes: Pause component
4. Update component health status
5. Sleep for check_interval

**Example Usage**:
```python
from error_recovery import Watchdog, ComponentConfig

components = [
    ComponentConfig(
        name="gmail_watcher",
        command="python app/src/app/watchers/gmail_watcher.py",
        restart_policy="always"
    ),
    ComponentConfig(
        name="file_processor",
        command="python app/src/app/file_processor.py",
        restart_policy="on-failure"
    )
]

watchdog = Watchdog(components)
watchdog.start()  # Runs indefinitely
```

---

#### `restart_component(component_name: str) -> bool`

Manually restart a specific component.

**Parameters**:
- `component_name` (str): Name of component to restart

**Returns**:
- `success` (bool): Whether restart succeeded

**Behavior**:
1. Stop existing process (if running)
2. Start new process
3. Update PID in health status
4. Reset failure counter
5. Log restart event

---

#### `pause_component(component_name: str) -> None`

Manually pause a component (stop process, mark as PAUSED).

**Parameters**:
- `component_name` (str): Name of component to pause

---

#### `get_component_status(component_name: str) -> ComponentHealthStatus`

Get current health status of a component.

**Returns**:
- ComponentHealthStatus object

---

## Component Configuration

```python
class ComponentConfig:
    name: str
    command: str  # Command to start the component
    working_directory: str = "."
    restart_policy: str = "always"  # always | on-failure | never
    max_restarts_per_window: int = 3
    restart_window_seconds: int = 300  # 5 minutes
    environment: Dict[str, str] = {}
    health_check_interval: int = 60  # seconds
```

---

## Restart Policies

- **always**: Restart on any exit (crash or clean shutdown)
- **on-failure**: Restart only on non-zero exit code
- **never**: Don't restart automatically (manual only)

---

## Configuration

```python
class WatchdogConfig:
    check_interval: int = 60  # seconds
    max_restarts_per_window: int = 3
    restart_window_seconds: int = 300
    health_status_file: str = "AI_Employee_Vault/.system/health_status.json"
    log_file: str = "watchdog.log"
```
