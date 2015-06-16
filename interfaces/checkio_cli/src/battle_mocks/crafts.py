__all__ = ["craft"]

from .tools import create_craft

CRAFT_BASIS = {
    'alias': 'craft',
    'role': 'craft',
    'type': 'craft',
    'unit': {},
    'code': None,
    'level': None,
    'player_id': None,
    'unit_quantity': None
}


def craft(level: int, unit: dict, unit_quantity: int, player_id: int, code_id: int) -> dict:
    return create_craft(CRAFT_BASIS, level, unit, unit_quantity, player_id, code_id)
