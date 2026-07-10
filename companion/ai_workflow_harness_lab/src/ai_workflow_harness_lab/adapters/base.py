from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import AdapterResult, SuiteTask


class Adapter(ABC):
    adapter_id: str
    adapter_version: str

    @abstractmethod
    def run(
        self,
        task: SuiteTask,
        condition: str,
        trial_index: int,
        workspace: Path,
        prompt_file: Path,
        output_dir: Path,
    ) -> AdapterResult:
        raise NotImplementedError
