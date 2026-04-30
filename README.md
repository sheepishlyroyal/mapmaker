# mapmaker

A terminal text-adventure engine with a live minimap overlay.  
Define your rooms and dialogue — the engine handles movement, rendering, and the map.

```
  +-- SHRINE OF THE NAMELESS  (1x1)           +-------+--+--+--+--+
  |   A stone idol squats in the centre,      |  . .  |  |  |  |  |
  |   ringed with offerings of bone.          +--#----+  |  |  |  |
  |                                           |       .  .  .  |  |
  |   The idol's hollow eyes track you.       +--+--+--+--+----+--+
  +-- 3 exits  [N E S]                        |  |@ |  |  |       |
                                              +--+--+--+--+-------+
  @ Shrine of the Nameless  |  exits: [N E S]  |  WASD/arrows = move  |  Q = quit
```

## Install

```bash
pip install mapmaker
```

Or directly from GitHub:

```bash
pip install git+https://github.com/sheepishlyroyal/mapmaker.git
```

## Quick start

```python
from mapmaker import Room, Dungeon

rooms = [
    Room(
        room_id     = "entrance",
        name        = "Cave Entrance",
        description = "Damp stone walls glisten in the torchlight.",
    ),
    Room(
        room_id     = "hall",
        name        = "Great Hall",
        description = "Pillars rise into darkness above a cracked mosaic floor.",
        width  = 2,
        height = 2,
    ),
]

Dungeon(rooms, start_room_id="entrance").run()
```

Controls: **WASD** or **arrow keys** to move. **Q** or **Esc** to quit.

---

## Room parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `room_id` | `str` | required | Unique identifier used for `start_room_id` and `exits` |
| `name` | `str` | required | Display name shown in narrative and status bar |
| `description` | `str` | required | Atmospheric text shown on room entry |
| `width` | `int` | `1` | Grid cells wide (1–4) |
| `height` | `int` | `1` | Grid cells tall (1–3) |
| `events` | `list[str]` | `[]` | Random atmospheric lines; falls back to engine defaults if empty |
| `on_enter` | `callable` | `None` | `on_enter(dungeon)` called every time the player enters |
| `entry_message` | `str` | `None` | Override the random "you step through…" line for this room |
| `exits` | `list[str]` | `None` | Explicit list of `room_id`s this room connects to. Auto-connects by grid adjacency if `None` |

## Dungeon parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rooms` | `list[Room]` | required | All rooms in the dungeon |
| `start_room_id` | `str` | random | `room_id` of the starting room |
| `entry_lines` | `list[str]` | built-in | Override the "you step through…" lines |
| `event_lines` | `list[str]` | built-in | Override global atmospheric events |
| `event_chance` | `float` | `0.55` | Probability an atmospheric event fires on entry |

## Custom logic with `on_enter`

```python
def treasury_entered(dungeon):
    if dungeon.get_room("shrine")._visited:
        dungeon.print("The chest glows faintly — the idol's blessing.")
    else:
        dungeon.print("The chest is cold and empty.")

Room(
    room_id     = "treasury",
    name        = "Treasury",
    description = "Iron chests line the walls.",
    on_enter    = treasury_entered,
)
```

`dungeon.print(text)` appends a line to the narrative from inside a callback.

## Minimap legend

| Symbol | Meaning |
|--------|---------|
| `@`    | Your current position |
| `.`    | Visited room floor |
| `#`    | Open door (both rooms visited) |
| `?`    | Passage hint (one side visited) |
| ` `    | Unexplored (fog of war) |

## Publishing your own dungeon

See `example/example_game.py` for a full working demo.

## Requirements

- Python 3.9+
- `pynput` (installed automatically)
- A proper terminal (not an IDE's embedded console)
- macOS/Linux: no extra setup. Windows: pynput works natively.

## License

MIT
