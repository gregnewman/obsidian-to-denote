"""
Obsidian to Denote Converter

A tool to convert Obsidian markdown files to Denote format.
"""

__version__ = "0.1.0"
__author__ = "Greg Newman"
__email__ = "greg@gregnewman.org"

from .converter import ObsidianToDenoteConverter, main

__all__ = ["ObsidianToDenoteConverter", "main"]
