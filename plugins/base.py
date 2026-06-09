from __future__ import annotations

import importlib
from pathlib import Path
from typing import Protocol


class InstrumentPlugin(Protocol):
    name: str
    version: str
    supported_formats: list[str]

    def parse(self, filepath, **kwargs): ...

    def validate(self, df): ...


class ReportPlugin(Protocol):
    name: str
    standard: str

    def generate(self, data_context, metadata): ...


def discover_plugins(base_dir: str = 'plugins') -> list[str]:
    discovered: list[str] = []
    root = Path(base_dir)
    if not root.exists():
        return discovered
    for child in root.iterdir():
        if child.is_dir() and (child / '__init__.py').exists():
            mod_name = f'{base_dir}.{child.name}'.replace('/', '.')
            importlib.import_module(mod_name)
            discovered.append(mod_name)
    return discovered
