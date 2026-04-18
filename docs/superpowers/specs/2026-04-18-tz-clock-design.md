# tz-clock — Terminal Timezone Dashboard

## Overview

A live-updating terminal dashboard that displays the current time, day progress, and weather across 6 timezones. Runs as a single command (`tz-clock`) from `~/.local/bin/`, built as a single Python file with no external dependencies.

## Timezones & Cities

| Label       | Timezone            | Weather City | Notes        |
|-------------|---------------------|--------------|--------------|
| HAWAII      | Pacific/Honolulu    | Hilo         |              |
| WEST COAST  | America/Los_Angeles | Los Angeles  |              |
| MOUNTAIN    | America/Denver      | Denver       |              |
| CENTRAL     | America/Chicago     | Austin       | Home zone ►  |
| EASTERN     | America/New_York    | New York     |              |
| UTC         | UTC                 | London       |              |

## Display Layout

```
╔════════════════════════════════════════════════════════╗
║       TIMEZONE DASHBOARD         Friday, Apr 18       ║
╠════════════════════════════════════════════════════════╣
║  HAWAII       1:45  ░░░░░░░░░░░░░░  ☀️  79°F Sunny   ║
║  WEST COAST   4:45  ▓▓▓▓▓░░░░░░░░░  ⛅ 68°F Cloudy   ║
║  MOUNTAIN     5:45  ▓▓▓▓▓▓░░░░░░░░  🌤️  72°F Clear   ║
║ ►CENTRAL      6:45  ▓▓▓▓▓▓▓░░░░░░░  🌧️  65°F Rain    ║
║  EASTERN      7:45  ▓▓▓▓▓▓▓▓░░░░░░  ☁️  61°F Cloudy  ║
║  UTC         12:45  ▓▓▓▓▓▓▓▓▓▓▓░░░  🌙 52°F Clear    ║
╠════════════════════════════════════════════════════════╣
║  r: refresh weather   q: quit   weather updated 2m ago║
╚════════════════════════════════════════════════════════╝
```

### Layout Details

- **Frame**: Unicode box-drawing characters (`╔ ═ ╗ ║ ╚ ╝ ╠ ╣`), blue color
- **Header**: Title + day of week and date, based on the home timezone (Central)
- **Zone rows**: Label, time (no AM/PM — progress bar conveys this), 24h progress bar, emoji weather icon, temperature (°F), short condition text
- **Home zone**: Marked with `►`, entire row in green. All other zones in orange/amber
- **Progress bar**: `▓` for elapsed, `░` for remaining. Width: 14 characters. Calculated as `(hours * 60 + minutes) / 1440 * bar_width`
- **Footer**: Keybind hints and weather freshness timestamp
- **Right wall alignment**: Every row padded to exact terminal width before drawing the right `║`

## Color Scheme

| Element          | Color          | Curses Constant     |
|------------------|----------------|---------------------|
| Frame            | Blue           | COLOR_BLUE          |
| Title            | White/bold     | COLOR_WHITE + BOLD  |
| Date             | Gray           | Dim white           |
| Home zone row    | Green          | COLOR_GREEN         |
| Other zone rows  | Orange/amber   | COLOR_YELLOW        |
| Footer text      | Gray           | Dim white           |

Note: Terminal "yellow" typically renders as orange/amber, which matches the desired look.

## Weather

### Data Source

[wttr.in](https://wttr.in) — free, no API key, curl-friendly.

**Request format:**
```
curl -s "wttr.in/Austin?format=%c+%t+%C"
```

Returns: `☀️ +79°F Sunny`

### Weather Behavior

- **On launch**: Fetch weather for all 6 cities in parallel (threaded)
- **Auto-refresh**: Every 30 minutes (configurable via `--refresh N`)
- **Manual refresh**: Press `r` to force refresh all cities
- **Freshness indicator**: Footer shows "weather updated Xm ago"
- **Failure handling**: If a city's weather fetch fails, show `--` in place of weather data. Don't crash or block the clock.

## Refresh & Input

### Clock Refresh
- Redraws every **60 seconds**
- Uses `curses.halfdelay()` or `timeout()` to allow non-blocking key detection between redraws

### Keybinds
| Key | Action                          |
|-----|---------------------------------|
| `r` | Force refresh weather for all zones |
| `q` | Quit                            |

## Configuration

Three layers, lowest to highest priority:

### 1. Built-in Defaults
The 6 zones listed above, baked into the script.

### 2. Config File
Location: `~/.config/tz-clock/config.json`

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

### 3. CLI Flags
```
tz-clock                        # run with defaults or config file
tz-clock --config PATH          # alternate config file location
tz-clock --no-weather           # disable weather fetching entirely
tz-clock --refresh 15           # weather auto-refresh every 15 minutes
```

Flags override config file values, which override defaults.

## Technical Details

### Language & Dependencies
- **Python 3.9+** (for `zoneinfo` module)
- **stdlib only**: `curses`, `urllib.request`, `json`, `argparse`, `datetime`, `zoneinfo`, `threading`, `time`
- No pip installs required

### File Structure
```
tz-clock              # single executable Python script in ~/.local/bin/
```

The script uses a `#!/usr/bin/env python3` shebang and is `chmod +x`.

### Threading Model
- **Main thread**: curses event loop — redraws clock, handles key input
- **Weather thread(s)**: background fetches via `threading.Thread`, results written to a shared dict with a lock. Main thread reads on next redraw cycle.

### Terminal Handling
- `curses.wrapper()` for clean init/teardown
- `curses.curs_set(0)` to hide cursor
- `stdscr.timeout(1000)` for 1-second input polling (redraws only when minute changes)
- Adapts to terminal width — if terminal is too narrow, truncate weather condition text first, then temperature

### Error Handling
- **Weather fetch failure**: Show `--` for that zone's weather, log nothing, retry on next cycle
- **Terminal too small**: Show a "resize terminal" message instead of crashing
- **Invalid config**: Fall back to defaults, print warning on stderr before entering curses mode
- **No internet**: Weather shows `--` for all zones, clock continues to function

## Distribution

- **Local install**: Copy script to `~/.local/bin/tz-clock`, ensure `~/.local/bin` is in PATH
- **GitHub**: Repository with README, the script, and an example config file
- **Install instructions**: `curl` one-liner or `git clone` + copy
