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


from datetime import datetime
from zoneinfo import ZoneInfo


def test_get_zone_time():
    zone = Zone("CENTRAL", "America/Chicago", "Austin", True)
    result = tz_clock.get_zone_time(zone)
    assert "hour" in result
    assert "minute" in result
    assert "time_str" in result
    assert "date_str" in result
    assert "day_str" in result
    assert 0 <= result["hour"] <= 23
    assert 0 <= result["minute"] <= 59


def test_get_zone_time_format():
    zone = Zone("UTC", "UTC", "London", False)
    result = tz_clock.get_zone_time(zone)
    # time_str should be like "1:45" or "12:05" — no AM/PM
    assert ":" in result["time_str"]
    assert "AM" not in result["time_str"]
    assert "PM" not in result["time_str"]


def test_make_progress_bar_midnight():
    bar = tz_clock.make_progress_bar(0, 0, width=14)
    assert bar == "░" * 14


def test_make_progress_bar_noon():
    bar = tz_clock.make_progress_bar(12, 0, width=14)
    assert bar == "▓" * 7 + "░" * 7


def test_make_progress_bar_end_of_day():
    bar = tz_clock.make_progress_bar(23, 59, width=14)
    filled = round(((23 * 60 + 59) / 1440) * 14)
    assert bar == "▓" * filled + "░" * (14 - filled)


def test_make_progress_bar_custom_width():
    bar = tz_clock.make_progress_bar(6, 0, width=24)
    filled = round(((6 * 60) / 1440) * 24)
    assert len(bar) == 24
    assert bar == "▓" * filled + "░" * (24 - filled)


import threading


def test_parse_weather_response_success():
    sample_json = json.dumps({
        "current_condition": [{
            "temp_F": "79",
            "temp_C": "26",
            "weatherDesc": [{"value": "Sunny"}],
            "weatherCode": "113",
        }]
    })
    result = tz_clock.parse_weather(sample_json)
    assert result["temp_f"] == "79"
    assert result["temp_c"] == "26"
    assert result["condition"] == "Sunny"
    assert result["emoji"] is not None


def test_parse_weather_response_unknown_code():
    sample_json = json.dumps({
        "current_condition": [{
            "temp_F": "50",
            "temp_C": "10",
            "weatherDesc": [{"value": "Weird"}],
            "weatherCode": "99999",
        }]
    })
    result = tz_clock.parse_weather(sample_json)
    assert result["temp_f"] == "50"
    assert result["condition"] == "Weird"
    assert result["emoji"] == "?"


def test_parse_weather_bad_json():
    result = tz_clock.parse_weather("not json")
    assert result is None


def test_weather_emoji_mapping():
    # Sunny
    assert tz_clock.WEATHER_EMOJI.get("113") == "☀️"
    # Cloudy
    assert tz_clock.WEATHER_EMOJI.get("119") == "☁️"
    # Rain
    assert tz_clock.WEATHER_EMOJI.get("296") == "🌧️"


def test_format_weather_string():
    weather = {"temp_f": "79", "temp_c": "26", "condition": "Sunny", "emoji": "☀️"}
    result = tz_clock.format_weather(weather)
    assert "79°F" in result
    assert "26°C" in result
    assert "☀️" in result
    assert "Sunny" in result


def test_format_weather_none():
    result = tz_clock.format_weather(None)
    assert result == "--"


def test_pad_row():
    result = tz_clock.pad_row("hello", 20)
    assert len(result) == 20
    assert result == "hello" + " " * 15


def test_pad_row_truncate():
    result = tz_clock.pad_row("a" * 30, 20)
    assert len(result) == 20


def test_format_zone_row_home():
    zone = Zone("CENTRAL", "America/Chicago", "Austin", True)
    time_info = {"time_str": "6:45", "hour": 18, "minute": 45}
    weather = {"emoji": "☀️", "temp_f": "79", "temp_c": "26", "condition": "Sunny"}
    row = tz_clock.format_zone_row(zone, time_info, weather, inner_width=54)
    assert "►" in row
    assert "CENTRAL" in row
    assert "6:45" in row
    assert "▓" in row
    assert "79°F/26°C" in row
    assert len(row) == 54


def test_format_zone_row_non_home():
    zone = Zone("UTC", "UTC", "London", False)
    time_info = {"time_str": "12:45", "hour": 0, "minute": 45}
    weather = None
    row = tz_clock.format_zone_row(zone, time_info, weather, inner_width=54)
    assert "►" not in row
    assert "UTC" in row
    assert "--" in row
    assert len(row) == 54


def test_format_header():
    header = tz_clock.format_header("Friday", "Apr 18", inner_width=54)
    assert "TIMEZONE DASHBOARD" in header
    assert "Friday" in header
    assert "Apr 18" in header
    assert len(header) == 54


def test_format_footer():
    footer = tz_clock.format_footer(120, inner_width=54)
    assert "r: refresh" in footer
    assert "q: quit" in footer
    assert "2m ago" in footer
    assert len(footer) == 54


def test_format_footer_never_updated():
    footer = tz_clock.format_footer(None, inner_width=54)
    assert "loading" in footer.lower() or "--" in footer
    assert len(footer) == 54
