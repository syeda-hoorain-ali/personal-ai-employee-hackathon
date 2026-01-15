import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from ..logging_config import get_logger


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)

        # Validate vault path exists
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")

        # Ensure Needs-Action directory exists
        self.Needs-Action = self.vault_path / 'Needs-Action'
        self.Needs-Action.mkdir(parents=True, exist_ok=True)

        # Validate check interval
        if check_interval <= 0:
            raise ValueError(f"Check interval must be positive, got: {check_interval}")

        self.check_interval = check_interval
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def check_for_updates(self) -> list:
        '''Return list of new items to process'''
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        '''Create .md file in Needs-Action folder'''
        pass

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                if items:
                    self.logger.info(f"Found {len(items)} items to process")
                for item in items:
                    try:
                        result = self.create_action_file(item)
                        if result:
                            self.logger.info(f"Created action file: {result}")
                        else:
                            self.logger.warning(f"Failed to create action file for item: {item}")
                    except Exception as item_error:
                        self.logger.error(f"Error creating action file for item {item}: {item_error}")
            except Exception as e:
                self.logger.error(f'Error in {self.__class__.__name__}: {e}')
            time.sleep(self.check_interval)
