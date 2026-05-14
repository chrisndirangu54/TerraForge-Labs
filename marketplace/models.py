from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Plugin:
    name: str
    version: str
    author: str
    price_usd: float
    category: str


@dataclass
class Dataset:
    name: str
    region: str
    format: str
    licence: str
    price_usd: float


@dataclass
class Template:
    name: str
    standard: str
    language: str
    preview_pdf_url: str
