"""
coolmapmaker
========
A terminal text-adventure engine with a live minimap overlay.

Quick start
-----------
    from coolmapmaker import Room, Dungeon

    rooms = [
        Room("cave_entrance", "Cave Entrance", "Damp stone walls glisten in the torchlight."),
        Room("great_hall",    "Great Hall",    "A vast chamber, pillars stretching into darkness.", width=2, height=2),
    ]

    dungeon = Dungeon(rooms)
    dungeon.run()
"""

from .engine import Dungeon, Room

__all__ = ["Dungeon", "Room"]
__version__ = "0.1.2"
