"""
example_game.py
---------------
A short demo dungeon using the dungeoncrawler library.

Shows how to:
  - Define rooms with custom descriptions and events
  - Use on_enter callbacks for custom logic
  - Override entry messages per room
  - Set explicit exit connections between rooms
  - Use dungeon.print() inside a callback

Run with:
    python example_game.py
"""

from coolmapmaker import Room, Dungeon

# =============================================================================
# DEFINE YOUR ROOMS
# Each Room needs at minimum: room_id, name, description.
# =============================================================================

rooms = [

    Room(
        room_id     = "entrance",
        name        = "Cave Entrance",
        description = "Damp stone walls glisten in the torchlight. Cold air rises from below.",
        width       = 1,
        height      = 1,
        entry_message = "You descend into the cave.",  # shown every time you re-enter
        events = [
            "Bats chitter somewhere in the dark above you.",
            "A distant rumble shakes loose a trickle of dust from the ceiling.",
            "The torches at the entrance gutter in an unseen draught.",
        ],
    ),

    Room(
        room_id     = "great_hall",
        name        = "Great Hall",
        description = "Vast pillars rise into darkness. A cracked mosaic covers the floor.",
        width       = 3,
        height      = 2,   # large room — occupies a 3x2 block on the grid
        events = [
            "Your footsteps echo back from impossible directions.",
            "One of the pillars bears a handprint in dried crimson.",
        ],
    ),

    Room(
        room_id     = "library",
        name        = "Ruined Library",
        description = "Shelves sag under rotting tomes. Most are illegible. One falls open as you enter.",
        width       = 2,
        height      = 1,
        events = [
            "The page the book fell open to shows a map. The map shows this room.",
        ],
    ),

    Room(
        room_id     = "shrine",
        name        = "Shrine of the Nameless",
        description = "A stone idol squats in the centre of the room, ringed with offerings of bone.",
        entry_message = "Something pulls you forward.",
        events = [
            "The idol's shadow points in a direction the torchlight cannot explain.",
            "A low hum vibrates in your back teeth.",
        ],
        on_enter = lambda dungeon: dungeon.print(
            "You feel watched. The idol's hollow eyes seem to track you."
        ),
    ),

    Room(
        room_id     = "treasury",
        name        = "Treasury",
        description = "Empty iron chests line the walls. Whatever was here is long gone.",
        events = [
            "A single gold coin sits in the corner, heads-up.",
            "The lock on one chest has been forced from the inside.",
        ],
    ),

    Room(
        room_id     = "cistern",
        name        = "Cistern",
        description = "A vast stone tank, bone-dry. The echo suggests tunnels far below.",
        width       = 2,
        height      = 2,
    ),

    Room(
        room_id     = "guard_post",
        name        = "Guard Post",
        description = "An overturned table. Dried food. A guttered candle. They left in a hurry.",
        events = [
            "The chair is still warm.",
        ],
    ),

    Room(
        room_id     = "deep_passage",
        name        = "Deep Passage",
        description = "The ceiling lowers until you must stoop. The air is very still.",
        events = [
            "The walls here are perfectly smooth — not carved, but melted.",
        ],
    ),

    Room(
        room_id     = "throne_room",
        name        = "Throne Room",
        description = "A single throne of black stone sits at the far end. The seat is worn smooth with use.",
        width       = 2,
        height      = 2,
        entry_message = "The door swings open on its own.",
        on_enter = lambda dungeon: dungeon.print(
            "You are the first living thing to stand here in a very long time."
            " The throne waits."
        ),
    ),

]

# =============================================================================
# OPTIONAL: Override the atmospheric lines used between rooms
# (remove these kwargs to use the built-in defaults)
# =============================================================================

MY_ENTRY_LINES = [
    "You move deeper.",
    "The passage leads you onward.",
    "You step through.",
    "Shadows retreat as you enter.",
    "You cross the threshold.",
]

# =============================================================================
# RUN THE DUNGEON
# =============================================================================

dungeon = Dungeon(
    rooms          = rooms,
    start_room_id  = "entrance",
    entry_lines    = MY_ENTRY_LINES,
    event_chance   = 0.6,
)

dungeon.run()
