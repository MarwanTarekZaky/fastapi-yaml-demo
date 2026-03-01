#!/usr/bin/env python3
"""Validates YAML configs for:
- Types and required keys (via Pydantic models)
- Simple business rules (e.g., price >= 0, HH:MM format, allowed roles)
- Cross file integrity (e.g., refrenced hours key exists)

Usage:
    python tools/validate.py
"""

