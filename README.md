# tz-clock

A terminal timezone dashboard that displays the current time across multiple timezones with live weather data, built with Python curses.

```
┌──────────────────────────────────────────────────────┐
│  Friday, Apr 18                                      │
├──────────────────────────────────────────────────────┤
│  HAWAII        4:32  ######--------  ☀️  82°F/28°C  │
│  WEST COAST    7:32  #########-----  ⛅  65°F/18°C  │
│  MOUNTAIN      8:32  ##########----  ☁️  58°F/14°C  │
│ ►CENTRAL       9:32  ###########---  ☀️  79°F/26°C  │
│  EASTERN      10:32  ############--  🌦️  61°F/16°C  │
│  UTC          14:32  ##############  ☁️  55°F/13°C  │
├──────────────────────────────────────────────────────┤
│  r: refresh weather   q: quit        weather 2m ago  │
└──────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.9+ (uses `zoneinfo`)
- No external dependencies

## Install

```sh
git clone https://github.com/jwilli97/ascii-clock.git
cd ascii-clock
chmod +x tz-clock
```

## Usage

```sh
./tz-clock
```

### Options

| Flag | Description |
|------|-------------|
| `--config PATH` | Path to config file (default: `~/.config/tz-clock/config.json`) |
| `--no-weather` | Disable weather fetching |
| `--refresh N` | Weather refresh interval in minutes (default: 30) |

### Keybindings

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh weather |

## Configuration

Create a config file at `~/.config/tz-clock/config.json` (or pass `--config`):

```json
{
  "zones": [
    {"name": "HAWAII", "tz": "Pacific/Honolulu", "city": "Hilo"},
    {"name": "WEST COAST", "tz": "America/Los_Angeles", "city": "Los Angeles"},
    {"name": "MOUNTAIN", "tz": "America/Denver", "city": "Denver"},
    {"name": "CENTRAL", "tz": "America/Chicago", "city": "Austin", "home": true},
    {"name": "EASTERN", "tz": "America/New_York", "city": "New York"},
    {"name": "UTC", "tz": "UTC", "city": "London"}
  ],
  "refresh_minutes": 30
}
```

| Field | Description |
|-------|-------------|
| `name` | Display label for the timezone |
| `tz` | IANA timezone identifier |
| `city` | City name for weather lookup (via [wttr.in](https://wttr.in)) |
| `home` | Set `true` to mark as home zone (shown with `►` marker) |
| `refresh_minutes` | How often to auto-refresh weather data |

Without a config file, built-in defaults are used (Hawaii through UTC, home = Central).
