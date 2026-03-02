#!/usr/bin/env python3
"""
Validates YAML configs for:
- Types and required keys (via Pydantic models)
- Simple business rules (e.g., price >= 0, HH:MM format, allowed roles)
- Cross-file integrity (e.g., referenced hours key exists)

Usage:
  python tools/validate.py
"""

import re
import sys
from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"

TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")  # HH:MM 24h

# ----- Models -----

class InventoryItem(BaseModel):
    sku: str
    name: str
    price: float = Field(ge=0)
    reorder_threshold: int = Field(ge=0)

class StaffMember(BaseModel):
    id: int
    name: str
    role: Literal["cashier", "stocker", "manager"]
    active: bool
    preferred_days: List[Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
    phone: Optional[str] = None

class HoursBlock(BaseModel):
    open: str
    close: str

    @field_validator("open", "close")
    @classmethod
    def hhmm(cls, v: str) -> str:
        if not TIME_RE.match(v):
            raise ValueError("must match HH:MM (24h), e.g., 09:00")
        return v

class HoursConfig(BaseModel):
    weekday: HoursBlock
    weekend: HoursBlock

class BaseConfig(BaseModel):
    store_name: str
    timezone: str
    tax_rate: float = Field(ge=0, le=1)  # e.g., 0.14 for 14%

class ProfileConfig(BaseModel):
    profile: Literal["weekday", "weekend"]
    staffing_multiplier: float = Field(gt=0)
    promotions_active: bool
    # Path-like pointer resolved by the app/validator (keep YAML simple)
    active_hours_from: Literal["hours.weekday", "hours.weekend"]

# ----- Loaders -----

def load_yaml(path: Path):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise SystemExit(f"YAML parse error in {path}:\n{e}")

def assert_file(path: Path):
    if not path.exists():
        raise SystemExit(f"Missing expected file: {path}")

# ----- Validation Orchestration -----

def validate_all() -> int:
    errors: List[str] = []

    # 1) Required files exist
    required = [
        CONFIG_DIR / "base.yaml",
        CONFIG_DIR / "data" / "inventory.yaml",
        CONFIG_DIR / "data" / "staff.yaml",
        CONFIG_DIR / "data" / "hours.yaml",
        CONFIG_DIR / "profiles" / "weekday.yaml",
        CONFIG_DIR / "profiles" / "weekend.yaml",
    ]
    for f in required:
        try:
            assert_file(f)
        except SystemExit as e:
            errors.append(str(e))

    if errors:
        print_section("Missing files", errors)
        return 1

    # 2) Load files
    base = load_yaml(required[0])
    inventory = load_yaml(required[1])
    staff = load_yaml(required[2])
    hours = load_yaml(required[3])
    weekday = load_yaml(required[4])
    weekend = load_yaml(required[5])

    # 3) Schema validations
    try:
        BaseConfig(**base)
    except ValidationError as e:
        errors.append(format_pydantic_error("base.yaml", e))

    # inventory.yaml expects a top-level `inventory: [...]`
    inv_items = inventory.get("inventory")
    if not isinstance(inv_items, list):
        errors.append("inventory.yaml: `inventory` must be a list of items")
    else:
        for i, item in enumerate(inv_items):
            try:
                InventoryItem(**item)
            except ValidationError as e:
                errors.append(format_pydantic_error(f"inventory.yaml [index {i}]", e))

    # staff.yaml expects `staff: [...]`
    staff_items = staff.get("staff")
    if not isinstance(staff_items, list):
        errors.append("staff.yaml: `staff` must be a list of staff members")
    else:
        for i, member in enumerate(staff_items):
            try:
                StaffMember(**member)
            except ValidationError as e:
                errors.append(format_pydantic_error(f"staff.yaml [index {i}]", e))

    # hours.yaml expects `hours: { weekday: {open,close}, weekend: {open,close} }`
    hours_obj = hours.get("hours")
    if not isinstance(hours_obj, dict):
        errors.append("hours.yaml: `hours` must be a map")
    else:
        try:
            HoursConfig(**hours_obj)
        except ValidationError as e:
            errors.append(format_pydantic_error("hours.yaml", e))

    # profiles
    for name, data in [("weekday.yaml", weekday), ("weekend.yaml", weekend)]:
        try:
            ProfileConfig(**data)
        except ValidationError as e:
            errors.append(format_pydantic_error(name, e))

    # 4) Cross-file checks
    errors.extend(cross_checks(base, inventory, staff, hours, weekday, weekend))

    # Report
    if errors:
        print_section("Validation FAILED", errors)
        return 1
    print("Validation PASSED ✓")
    return 0

def cross_checks(base, inventory, staff, hours, weekday, weekend) -> List[str]:
    errs = []

    # Example: ensure all prices are >= reorder_threshold * 0 (already via schema for >=0)
    # Example: ensure active_hours_from pointers resolve
    hours_map = hours.get("hours", {})
    for prof_name, prof in [("weekday.yaml", weekday), ("weekend.yaml", weekend)]:
        ptr = prof.get("active_hours_from")
        if ptr == "hours.weekday" and "weekday" not in hours_map:
            errs.append(f"{prof_name}: active_hours_from points to missing hours.weekday")
        if ptr == "hours.weekend" and "weekend" not in hours_map:
            errs.append(f"{prof_name}: active_hours_from points to missing hours.weekend")

    # Example: ensure at least one manager is active
    staff_list = staff.get("staff", [])
    if not any(s.get("role") == "manager" and s.get("active") for s in staff_list):
        errs.append("staff.yaml: At least one active manager is required")

    return errs

def print_section(title: str, lines: List[str]):
    bar = "=" * len(title)
    print(f"\n{title}\n{bar}")
    for line in lines:
        print(f"- {line}")

def format_pydantic_error(fname: str, e: ValidationError) -> str:
    msgs = []
    for err in e.errors():
        loc = ".".join(str(p) for p in err.get("loc", []))
        msgs.append(f"{fname}: {loc} -> {err.get('msg')}")
    return "\n".join(msgs)

if __name__ == "__main__":
    sys.exit(validate_all())