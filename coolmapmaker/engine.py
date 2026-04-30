"""
coolmapmaker.engine
===============
Core engine: Room data class, dungeon generator, minimap renderer, game loop.
"""

import sys
import os
import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional
from pynput import keyboard


# =============================================================================
# TERMINAL UTILITIES  (no `re` — ANSI stripped with a simple state machine)
# =============================================================================

def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def _hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def _show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def _move_cursor(row: int, col: int) -> str:
    return f"\033[{row};{col}H"

def _erase_to_end() -> str:
    return "\033[K"

def _strip_ansi(text: str) -> str:
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\033" and i + 1 < len(text) and text[i + 1] == "[":
            i += 2
            while i < len(text) and text[i] != "m":
                i += 1
            i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)

def _get_terminal_size() -> tuple:
    try:
        s = os.get_terminal_size()
        return s.columns, s.lines
    except Exception:
        return 120, 40

# ANSI colour helpers
RESET = "\033[0m"
BOLD  = "\033[1m"

def _fg(n: int) -> str:
    return f"\033[38;5;{n}m"

def _bg(n: int) -> str:
    return f"\033[48;5;{n}m"

# Colour palette
_C_WALL         = _fg(238) + _bg(234)
_C_FLOOR        = _fg(59)  + _bg(234)
_C_PLAYER       = BOLD + _fg(226) + _bg(22)
_C_CURRENT_BG   = _fg(46)  + _bg(22)
_C_UNEXPLORED   = _fg(235) + _bg(233)
_C_DOOR_OPEN    = BOLD + _fg(214) + _bg(52)
_C_DOOR_HINT    = _fg(130) + _bg(234)
_C_STATUS       = _bg(232) + _fg(240)

# Minimap cell size (fixed)
_CELL_W = 4
_CELL_H = 2


# =============================================================================
# PUBLIC: Room
# =============================================================================

@dataclass(eq=False)
class Room:
    """
    A single room (or multi-cell area) in your dungeon.

    Parameters
    ----------
    room_id : str
        Unique identifier, e.g. ``"cave_entrance"``.
    name : str
        Display name shown in the narrative and status bar.
    description : str
        One or two sentences of atmospheric text shown on entry.
    width : int
        How many grid cells wide this room is (default 1, max 4).
    height : int
        How many grid cells tall  this room is (default 1, max 3).
    events : list[str], optional
        Extra lines that may randomly appear when entering.
        Falls back to the engine's built-in atmospheric events if empty.
    on_enter : callable, optional
        ``on_enter(dungeon)`` called every time the player enters.
    entry_message : str, optional
        Override the random "you step through…" line for this room.
    exits : list[str], optional
        Explicit list of room_ids this room connects to.
        If None the engine auto-connects rooms that share a grid edge.
    """

    room_id:       str
    name:          str
    description:   str
    width:         int              = 1
    height:        int              = 1
    events:        list             = field(default_factory=list)
    on_enter:      Optional[object] = field(default=None, repr=False)
    entry_message: Optional[str]   = None
    exits:         Optional[list]  = None

    _uid:         int  = field(default=0,     init=False, repr=False)
    _grid_x:      int  = field(default=0,     init=False, repr=False)
    _grid_y:      int  = field(default=0,     init=False, repr=False)
    _cells:       set  = field(default_factory=set, init=False, repr=False)
    _connections: set  = field(default_factory=set, init=False, repr=False)
    _visited:     bool = field(default=False, init=False, repr=False)

    def _init_engine(self, uid: int, gx: int, gy: int):
        self._uid    = uid
        self._grid_x = gx
        self._grid_y = gy
        self._cells  = set()
        for dy in range(self.height):
            for dx in range(self.width):
                self._cells.add((gx + dx, gy + dy))

    def _center(self) -> tuple:
        return self._grid_x + self.width // 2, self._grid_y + self.height // 2

    def size_label(self) -> str:
        return f"{self.width}x{self.height}"


# =============================================================================
# DEFAULT FALLBACK FLAVOUR TEXT
# =============================================================================

_DEFAULT_ENTRIES = [
    "You step through the doorway.",
    "You press carefully forward.",
    "The passage opens into—",
    "You duck under a low arch.",
    "A cold draught pulls you onward.",
    "The floor groans under your boots.",
    "You cross the threshold.",
    "Torchlight gives way to shadow.",
]

_DEFAULT_EVENTS = [
    "Something skitters in the darkness, then goes silent.",
    "A torch flares briefly, then steadies.",
    "Claw marks on the doorframe — fresh.",
    "A faint sound, like breathing, just beyond hearing.",
    "The air here is noticeably colder.",
    "Water drips in perfect, metronomic rhythm.",
    "A flash of reflected light — something moved.",
    "The shadows seem to lean toward you.",
    "A low moan echoes through the stone. Probably the wind.",
]


# =============================================================================
# GRID SIZE CALCULATION
# =============================================================================

def _compute_grid_size(rooms: list) -> int:
    """
    Pick a grid size so rooms fill roughly 75% of the grid area.
    Clamped to [5, 15].
    """
    total_cells = sum(r.width * r.height for r in rooms)
    size = math.ceil(math.sqrt(total_cells / 0.75))
    return max(5, min(15, size))


# =============================================================================
# DUNGEON PLACEMENT
# =============================================================================

def _place_rooms(rooms: list, grid_size: int) -> tuple:
    grid:     dict = {}
    occupied: set  = set()
    id_map:   dict = {}
    uid_counter    = [0]

    def try_place(room: Room, x: int, y: int) -> bool:
        cells = [(x + dx, y + dy) for dy in range(room.height) for dx in range(room.width)]
        for cx, cy in cells:
            if (cx, cy) in occupied:        return False
            if cx < 0 or cx >= grid_size:   return False
            if cy < 0 or cy >= grid_size:   return False
        uid_counter[0] += 1
        room._init_engine(uid_counter[0], x, y)
        for cell in cells:
            occupied.add(cell)
            grid[cell] = room
        id_map[room.room_id] = room
        return True

    sorted_rooms = sorted(rooms, key=lambda r: r.width * r.height, reverse=True)

    for room in sorted_rooms:
        placed = False
        attempts = 0
        while not placed and attempts < 2000:
            attempts += 1
            x = random.randint(0, grid_size - room.width)
            y = random.randint(0, grid_size - room.height)
            placed = try_place(room, x, y)
        if not placed:
            raise RuntimeError(
                f"Could not place room '{room.room_id}' ({room.width}x{room.height}) "
                f"after 2000 attempts. Too many large rooms for the grid?"
            )

    # Auto-connect rooms that share a grid edge
    for (gx, gy), room in grid.items():
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nb = grid.get((gx + dx, gy + dy))
            if nb is not None and nb is not room:
                room._connections.add(nb)
                nb._connections.add(room)

    # Connect any isolated rooms to their nearest neighbour
    placed_rooms = list(id_map.values())
    for room in placed_rooms:
        if len(room._connections) == 0 and len(placed_rooms) > 1:
            cx = room._grid_x + room.width  // 2
            cy = room._grid_y + room.height // 2
            nearest = min(
                (r for r in placed_rooms if r is not room),
                key=lambda r: abs((r._grid_x + r.width  // 2) - cx)
                            + abs((r._grid_y + r.height // 2) - cy)
            )
            room._connections.add(nearest)
            nearest._connections.add(room)

    # Override with explicit exits if provided
    for room in rooms:
        if room.exits is not None:
            room._connections.clear()
            for target_id in room.exits:
                if target_id in id_map:
                    target = id_map[target_id]
                    room._connections.add(target)
                    target._connections.add(room)

    return grid, id_map


# =============================================================================
# MINIMAP
# =============================================================================

def _build_minimap(current_room: Room, grid: dict, grid_size: int) -> list:
    map_w = grid_size * _CELL_W + 1
    map_h = grid_size * _CELL_H + 1

    char_buf  = [[" "] * map_w for _ in range(map_h)]
    color_buf = [[_C_UNEXPLORED] * map_w for _ in range(map_h)]

    for (gx, gy), room in grid.items():
        px = gx * _CELL_W
        py = gy * _CELL_H
        is_cur = room is current_room
        is_vis = room._visited

        for row in range(_CELL_H + 1):
            for col in range(_CELL_W + 1):
                bx = px + col
                by = py + row
                if bx >= map_w or by >= map_h:
                    continue

                on_t = row == 0
                on_b = row == _CELL_H
                on_l = col == 0
                on_r = col == _CELL_W
                is_edge = on_t or on_b or on_l or on_r

                if on_t and gy > 0             and grid.get((gx,     gy - 1)) is room: continue
                if on_b and gy < grid_size - 1 and grid.get((gx,     gy + 1)) is room: continue
                if on_l and gx > 0             and grid.get((gx - 1, gy))     is room: continue
                if on_r and gx < grid_size - 1 and grid.get((gx + 1, gy))     is room: continue

                if is_edge:
                    nb = None
                    if on_t and gy > 0:               nb = grid.get((gx,     gy - 1))
                    elif on_b and gy < grid_size - 1: nb = grid.get((gx,     gy + 1))
                    elif on_l and gx > 0:             nb = grid.get((gx - 1, gy))
                    elif on_r and gx < grid_size - 1: nb = grid.get((gx + 1, gy))

                    if nb is not None and nb is not room and nb in room._connections:
                        is_mid = (col == _CELL_W // 2) if (on_t or on_b) else (row == _CELL_H // 2)
                        if is_mid:
                            if is_vis and nb._visited:
                                char_buf[by][bx]  = "#"
                                color_buf[by][bx] = _C_DOOR_OPEN
                            elif is_vis or nb._visited:
                                char_buf[by][bx]  = "?"
                                color_buf[by][bx] = _C_DOOR_HINT
                        else:
                            if is_vis:
                                ch = "-" if (on_t or on_b) else "|"
                                char_buf[by][bx]  = ch
                                color_buf[by][bx] = _C_CURRENT_BG if is_cur else _C_WALL
                    else:
                        if is_vis:
                            if   on_t and on_l: ch = "+"
                            elif on_t and on_r: ch = "+"
                            elif on_b and on_l: ch = "+"
                            elif on_b and on_r: ch = "+"
                            elif on_t or on_b:  ch = "-"
                            else:               ch = "|"
                            char_buf[by][bx]  = ch
                            color_buf[by][bx] = _C_CURRENT_BG if is_cur else _C_WALL
                else:
                    if is_vis:
                        if is_cur and col == _CELL_W // 2 and row == _CELL_H // 2:
                            char_buf[by][bx]  = "@"
                            color_buf[by][bx] = _C_PLAYER
                        elif is_cur:
                            char_buf[by][bx]  = " "
                            color_buf[by][bx] = _C_CURRENT_BG
                        else:
                            char_buf[by][bx]  = "."
                            color_buf[by][bx] = _C_FLOOR

    lines = []
    for row in range(map_h):
        line = ""
        for col in range(map_w):
            line += color_buf[row][col] + char_buf[row][col] + RESET
        lines.append(line)
    return lines


# =============================================================================
# SCREEN RENDERER
# =============================================================================

def _render(log: list, current_room: Room, grid: dict, grid_size: int):
    term_w, term_h = _get_terminal_size()

    map_lines  = _build_minimap(current_room, grid, grid_size)
    map_h      = len(map_lines)
    map_vis_w  = grid_size * _CELL_W + 1

    sep_col    = term_w - map_vis_w - 3
    text_w     = max(20, sep_col - 2)
    map_top    = term_h - map_h - 1

    wrapped = []
    for raw in log:
        plain = _strip_ansi(raw)
        if not plain:
            wrapped.append("")
            continue
        while len(plain) > text_w:
            cut = plain[:text_w].rfind(" ")
            if cut < 4:
                cut = text_w
            wrapped.append(plain[:cut])
            plain = plain[cut:].lstrip()
        wrapped.append(plain)

    max_vis = term_h - 2
    visible = wrapped[-max_vis:] if len(wrapped) > max_vis else wrapped

    out = ["\033[H"]

    for row in range(1, term_h):
        ridx = row - 1

        ti = ridx - (max_vis - len(visible))
        if 0 <= ti < len(visible):
            t   = visible[ti]
            pad = max(0, text_w - len(_strip_ansi(t)))
            text_part = "  " + t + " " * pad
        else:
            text_part = " " * (text_w + 2)

        in_map = map_top <= ridx < map_top + map_h
        sep    = f" {_fg(240)}|{RESET} " if in_map else "   "

        mi       = ridx - map_top
        map_part = map_lines[mi] if 0 <= mi < map_h else ""

        out.append(f"{_move_cursor(row, 1)}{text_part}{sep}{map_part}{_erase_to_end()}")

    hints = _exit_hints(current_room)
    sbar  = (
        f"{_C_STATUS}  @ {BOLD}{_fg(220)}{current_room.name}{RESET}"
        f"{_C_STATUS}  |  exits: {_fg(172)}{hints}{_fg(240)}"
        f"  |  WASD / arrows = move  |  # = door  |  Q = quit {RESET}"
    )
    out.append(f"{_move_cursor(term_h, 1)}{sbar}{_erase_to_end()}")

    sys.stdout.write("".join(out))
    sys.stdout.flush()


# =============================================================================
# MOVEMENT HELPERS
# =============================================================================

def _exit_hints(room: Room) -> str:
    cx, cy = room._center()
    dirs = []
    for nb in room._connections:
        nx, ny = nb._center()
        dx = nx - cx
        dy = ny - cy
        if abs(dx) >= abs(dy):
            dirs.append("E" if dx > 0 else "W")
        else:
            dirs.append("S" if dy > 0 else "N")
    order = ["N", "E", "S", "W"]
    unique = sorted(set(dirs), key=lambda d: order.index(d))
    return "[" + " ".join(unique) + "]" if unique else "[-]"


def _best_neighbour(current: Room, dx: int, dy: int) -> Optional[Room]:
    cx, cy = current._center()
    candidates = []
    for nb in current._connections:
        nx, ny = nb._center()
        score  = (nx - cx) * dx + (ny - cy) * dy
        if score > 0:
            candidates.append((score, nb._uid, nb))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][2]


# =============================================================================
# PUBLIC: Dungeon
# =============================================================================

class Dungeon:
    """
    The main game engine.

    Parameters
    ----------
    rooms : list[Room]
        All Room objects that make up the dungeon.
        The engine places them on a grid automatically sized to fit.
    start_room_id : str, optional
        ``room_id`` of the starting room. Defaults to a random room.
    entry_lines : list[str], optional
        Override the default "you step through…" lines.
    event_lines : list[str], optional
        Override the default atmospheric event lines.
    event_chance : float
        Probability (0–1) that an event fires on room entry. Default 0.55.
    """

    def __init__(
        self,
        rooms:          list,
        start_room_id:  Optional[str] = None,
        entry_lines:    Optional[list] = None,
        event_lines:    Optional[list] = None,
        event_chance:   float = 0.55,
    ):
        if not rooms:
            raise ValueError("You must provide at least one Room.")

        self._rooms        = rooms
        self._entry_lines  = entry_lines or _DEFAULT_ENTRIES
        self._event_lines  = event_lines or _DEFAULT_EVENTS
        self._event_chance = event_chance
        self._grid_size    = _compute_grid_size(rooms)

        self._grid, self._id_map = _place_rooms(rooms, self._grid_size)

        if start_room_id is not None:
            if start_room_id not in self._id_map:
                raise ValueError(f"start_room_id '{start_room_id}' not found in rooms list.")
            self._current = self._id_map[start_room_id]
        else:
            self._current = random.choice(rooms)

        self._log:          list = []
        self._needs_redraw: bool = True
        self._key_queue:    list = []

        self._enter(self._current, first=True)

    @property
    def current_room(self) -> Room:
        return self._current

    @property
    def visited_rooms(self) -> list:
        return [r for r in self._rooms if r._visited]

    def get_room(self, room_id: str) -> Optional[Room]:
        return self._id_map.get(room_id)

    def print(self, text: str):
        self._log.append(f"  {text}")
        self._needs_redraw = True

    def _enter(self, room: Room, first: bool = False):
        room._visited = True

        if not first:
            msg = room.entry_message or random.choice(self._entry_lines)
            self._log.append("")
            self._log.append(f"  {msg}")
            self._log.append("")

        self._log.append(f"  +-- {room.name.upper()}  ({room.size_label()})")
        self._log.append(f"  |   {room.description}")

        pool = room.events if room.events else self._event_lines
        if pool and random.random() < self._event_chance:
            self._log.append("  |")
            self._log.append("  |   " + random.choice(pool))

        count = len(room._connections)
        hints = _exit_hints(room)
        self._log.append(f"  +-- {count} exit{'s' if count != 1 else ''}  {hints}")

        self._needs_redraw = True

        if room.on_enter is not None:
            room.on_enter(self)

    def _message(self, text: str):
        self._log.append(f"  {text}")
        self._needs_redraw = True

    def _move(self, dx: int, dy: int):
        nb = _best_neighbour(self._current, dx, dy)
        if nb is None:
            self._message("[No passage that way.]")
            return
        self._current = nb
        self._enter(nb)

    def _push_key(self, key):
        self._key_queue.append(key)

    def _process_keys(self) -> bool:
        while self._key_queue:
            key = self._key_queue.pop(0)

            char = None
            try:
                if hasattr(key, "char") and key.char is not None:
                    char = key.char.lower()
            except Exception:
                pass

            if char == "q" or key == keyboard.Key.esc:
                return False
            if char == "w" or key == keyboard.Key.up:      self._move( 0, -1)
            elif char == "s" or key == keyboard.Key.down:  self._move( 0,  1)
            elif char == "a" or key == keyboard.Key.left:  self._move(-1,  0)
            elif char == "d" or key == keyboard.Key.right: self._move( 1,  0)

        return True

    def run(self):
        _clear_screen()
        _hide_cursor()

        listener = keyboard.Listener(on_press=self._push_key)
        listener.start()

        running = True
        try:
            while running:
                running = self._process_keys()
                if self._needs_redraw:
                    _render(self._log, self._current, self._grid, self._grid_size)
                    self._needs_redraw = False
                time.sleep(0.03)
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
            _show_cursor()
            _clear_screen()
            print(f"\n{BOLD}You escaped the dungeon.{RESET}\n")
