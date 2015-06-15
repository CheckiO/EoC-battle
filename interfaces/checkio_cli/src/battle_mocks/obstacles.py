__all__ = ["obstacle"]

from .tools import check_tile_position


def obstacle(tile_position, size):
    """
    Create obstacle dictionary with the given position and size
    """
    check_tile_position(tile_position)
    return {'alias': 'rock',
            'hit_points': 9000000,
            'level': 1,
            'role': 'obstacle',
            'size': size,
            'tile_position': tile_position,
            'type': 'rock'}