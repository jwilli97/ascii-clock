import json
import os
import sys
import tempfile

# Add parent dir to path so we can import tz-clock as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from tz-clock by loading it as a module
# spec_from_file_location returns None for extensionless files, so use SourceFileLoader directly
import importlib.util
import types
from importlib.machinery import SourceFileLoader
_tz_clock_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tz-clock")
_loader = SourceFileLoader("tz_clock", _tz_clock_path)
tz_clock = types.ModuleType("tz_clock")
_loader.exec_module(tz_clock)

Zone = tz_clock.Zone


def test_default_zones():
    zones = tz_clock.DEFAULT_ZONES
    assert len(zones) == 6
    assert zones[0].name == "HAWAII"
    assert zones[3].home is True
    assert zones[3].city == "Austin"
    home_zones = [z for z in zones if z.home]
    assert len(home_zones) == 1


def test_load_config():
    config = {
        "zones": [
            {"name": "TEST", "tz": "UTC", "city": "London", "home": True}
        ],
        "refresh_minutes": 15,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        path = f.name
    try:
        zones, refresh = tz_clock.load_config(path)
        assert len(zones) == 1
        assert zones[0].name == "TEST"
        assert zones[0].home is True
        assert refresh == 15
    finally:
        os.unlink(path)


def test_load_config_missing_file():
    try:
        tz_clock.load_config("/nonexistent/path.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_parse_args_defaults():
    args = tz_clock.parse_args([])
    assert args.config is None
    assert args.no_weather is False
    assert args.refresh is None


def test_parse_args_all_flags():
    args = tz_clock.parse_args(["--config", "/tmp/c.json", "--no-weather", "--refresh", "10"])
    assert args.config == "/tmp/c.json"
    assert args.no_weather is True
    assert args.refresh == 10


def test_resolve_config_defaults():
    args = tz_clock.parse_args([])
    zones, refresh, no_weather = tz_clock.resolve_config(args)
    assert len(zones) == 6
    assert refresh == 30
    assert no_weather is False


def test_resolve_config_file_override():
    config = {
        "zones": [
            {"name": "ONLY", "tz": "UTC", "city": "Nowhere"}
        ],
        "refresh_minutes": 5,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        path = f.name
    try:
        args = tz_clock.parse_args(["--config", path])
        zones, refresh, _ = tz_clock.resolve_config(args)
        assert len(zones) == 1
        assert zones[0].name == "ONLY"
        assert refresh == 5
    finally:
        os.unlink(path)


def test_resolve_config_cli_overrides_file():
    config = {"zones": [{"name": "X", "tz": "UTC", "city": "Y"}], "refresh_minutes": 5}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        path = f.name
    try:
        args = tz_clock.parse_args(["--config", path, "--refresh", "99"])
        _, refresh, _ = tz_clock.resolve_config(args)
        assert refresh == 99
    finally:
        os.unlink(path)
