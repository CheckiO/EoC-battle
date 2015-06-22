from copy import deepcopy


class ATTRIBUTE():
    TILE_POSITION = 'tile_position'
    PLAYER_ID = 'player_id'
    CODE_ID = 'code'
    LEVEL = 'level'
    UNIT = 'unit'
    UNIT_QUANTITY = 'unit_quantity'
    CRAFT_ID = "craft_id"


def check_tile_position(tile_position: [int, int]):
    if (not isinstance(tile_position, (list, tuple)) or
            not all(isinstance(x, int) for x in tile_position)):
        raise TypeError('Tile position must be two integers list/tuple')


def check_level(group, level):
    if level not in group:
        raise AttributeError('Wrong level for item.')


def create_building(building_group: dict, level: int, tile_position: [int, int],
                    player_id: int, code_id: int=None) -> dict:
    check_level(building_group, level)
    check_tile_position(tile_position)
    building = deepcopy(building_group[level])
    building[ATTRIBUTE.TILE_POSITION] = tile_position[:]
    building[ATTRIBUTE.PLAYER_ID] = player_id
    building[ATTRIBUTE.LEVEL] = level
    if ATTRIBUTE.CODE_ID in building:
        building[ATTRIBUTE.CODE_ID] = code_id
    return building


def create_unit(unit_group: dict, level: int) -> dict:
    check_level(unit_group, level)
    unit = deepcopy(unit_group[level])
    unit[ATTRIBUTE.LEVEL] = level
    return unit


def create_craft(craft_basis: dict, level: int, unit: dict, unit_quantity: int,
                 player_id: int, code_id: int, craft_id: int) -> dict:
    craft = deepcopy(craft_basis)
    craft[ATTRIBUTE.LEVEL] = level
    craft[ATTRIBUTE.UNIT] = unit
    craft[ATTRIBUTE.UNIT_QUANTITY] = unit_quantity
    craft[ATTRIBUTE.PLAYER_ID] = player_id
    craft[ATTRIBUTE.CODE_ID] = code_id
    craft[ATTRIBUTE.CRAFT_ID] = craft_id
    return craft
