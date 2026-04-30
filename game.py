#!/usr/bin/env python3
"""
DUNGEON CRAWLER — powered by coolmapmaker
WASD / arrow keys to move  |  Q to quit
"""

import random
from coolmapmaker import Room, Dungeon

ROOM_FLAVOUR = [
    ("Torch-Lit Corridor",  "Flickering torches cast long shadows. Dust motes drift through stale air."),
    ("Collapsed Vault",     "The ceiling has partially caved in. Something glints beneath the rubble."),
    ("Ossuary",             "Skulls line alcoves in the rock. A faint smell of incense — someone was here recently."),
    ("Flooded Chamber",     "Ankle-deep black water covers the floor. Slow dripping echoes from above."),
    ("Armoury",             "Rusted weapon racks line the walls. One short blade still holds an edge."),
    ("Library Alcove",      "Rotting shelves sag under water-damaged tomes. One lies open, its script unreadable."),
    ("Shrine",              "A stone idol daubed with old pigment. Offerings of bone surround its base."),
    ("Guard Post",          "Overturned table, dried food, a guttered candle. They left in a hurry."),
    ("Crypt",               "Stone sarcophagi line the walls. Every lid slid aside — from the inside."),
    ("Chasm Bridge",        "A narrow bridge spans a yawning drop. You cannot see the bottom."),
    ("Conjuring Circle",    "Chalk sigils cover every surface. The air tastes of copper. Still faintly warm."),
    ("Feast Hall",          "A long table set for guests who never arrived. Candles melted to cold puddles."),
    ("Prison Cells",        "Iron doors hang open on rusted hinges. Scratched tallies mark every wall."),
    ("Cistern",             "A great stone tank, bone-dry. An echo hints at tunnels below the waterline."),
    ("War Room",            "Maps pinned to the walls show territories completely unfamiliar to you."),
    ("Grand Antechamber",   "Whatever held court beyond this room has not been seen in a very long time."),
    ("Fungal Grotto",       "Pale mushrooms the size of stools crowd every corner, emitting a faint glow."),
    ("Charnel Pit",         "A grated hole drops into blackness. The smell tells you enough."),
    ("Observatory Shaft",   "A tunnel bored straight up. Far above, a circle of sky — impossibly distant."),
    ("Alchemist's Nook",    "Shattered glass vessels. A residue of vivid green clings to the workbench."),
]

EVENT_LINES = [
    "Something skitters in the darkness, then goes silent.",
    "A torch flares briefly, then steadies.",
    "Claw marks on the doorframe — fresh.",
    "A faint sound, like breathing, just beyond hearing.",
    "The air here is noticeably colder.",
    "Water drips in perfect, metronomic rhythm.",
    "A flash of reflected light — something moved.",
    "The shadows seem to lean toward you.",
    "A low moan echoes through the stone. Probably the wind.",
    "A copper coin pressed into a crack in the floor.",
    "The mortar between the stones here has been recently disturbed.",
    "A faint smell of smoke — recent, not ancient.",
]

ENTRY_LINES = [
    "You step through the doorway.",
    "You press carefully forward.",
    "The passage opens into—",
    "You duck under a low arch.",
    "A cold draught pulls you onward.",
    "The floor groans under your boots.",
    "You cross the threshold.",
    "Torchlight gives way to shadow.",
]


LARGE_SIZES = [(3, 2), (2, 3), (4, 2), (2, 2), (3, 2), (2, 2),
               (2, 2), (3, 2), (2, 3), (2, 2), (3, 2), (4, 2)]


def build_rooms():
    flavour = random.sample(ROOM_FLAVOUR, len(LARGE_SIZES))
    rooms = []
    for i, (w, h) in enumerate(LARGE_SIZES):
        name, desc = flavour[i]
        rooms.append(Room(
            room_id=f"room_{i}",
            name=name,
            description=desc,
            width=w,
            height=h,
            events=random.sample(EVENT_LINES, 3),
        ))
    return rooms


Dungeon(
    build_rooms(),
    entry_lines=ENTRY_LINES,
    event_chance=0.55,
).run()
