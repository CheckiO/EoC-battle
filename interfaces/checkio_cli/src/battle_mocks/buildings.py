__all__ = ["command_center", "crystalite_farm", "adamantite_mine", "crystalite_silo",
           "adamantite_storage", "vault", "laboratory", "craft_pad"]

from .tools import create_building

COMMAND_CENTER_BASIS = {
    'alias': 'commandCenter-main',
    'role': 'center',
    'type': 'commandCenter',
    'size': 4,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

COMMAND_CENTERS = {
    1: dict(hit_points=2500, **COMMAND_CENTER_BASIS),
    2: dict(hit_points=3000, **COMMAND_CENTER_BASIS),
    3: dict(hit_points=3500, **COMMAND_CENTER_BASIS),
    4: dict(hit_points=4000, **COMMAND_CENTER_BASIS),
    5: dict(hit_points=6000, **COMMAND_CENTER_BASIS)
}

CRYSTALITE_FARM_BASIS = {
    'alias': 'crystalite-farm',
    'role': 'building',
    'type': 'crystaliteFarm',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

CRYSTALITE_FARMS = {
    1: dict(hit_points=1000, **CRYSTALITE_FARM_BASIS),
    2: dict(hit_points=1200, **CRYSTALITE_FARM_BASIS),
    3: dict(hit_points=1400, **CRYSTALITE_FARM_BASIS),
    4: dict(hit_points=1700, **CRYSTALITE_FARM_BASIS),
    5: dict(hit_points=2000, **CRYSTALITE_FARM_BASIS)
}

ADAMANTITE_MINE_BASIS = {
    'alias': 'adamantite-mine',
    'role': 'building',
    'type': 'adamantiteMine',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

ADAMANTITE_MINES = {
    1: dict(hit_points=1500, **ADAMANTITE_MINE_BASIS),
    2: dict(hit_points=1800, **ADAMANTITE_MINE_BASIS),
    3: dict(hit_points=2200, **ADAMANTITE_MINE_BASIS),
    4: dict(hit_points=2600, **ADAMANTITE_MINE_BASIS),
    5: dict(hit_points=3100, **ADAMANTITE_MINE_BASIS)
}

CRYSTALITE_SILO_BASIS = {
    'alias': 'crystalite-silo',
    'role': 'building',
    'type': 'crystaliteSilo',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}
CRYSTALITE_SILOS = {
    1: dict(hit_points=1000, **CRYSTALITE_SILO_BASIS),
    2: dict(hit_points=1200, **CRYSTALITE_SILO_BASIS),
    3: dict(hit_points=1400, **CRYSTALITE_SILO_BASIS),
    4: dict(hit_points=1700, **CRYSTALITE_SILO_BASIS),
}

ADAMANTITE_STORAGE_BASIS = {
    'alias': 'adamantite_storage',
    'role': 'building',
    'type': 'adamantiteStorage',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

ADAMANTITE_STORAGES = {
    1: dict(hit_points=1000, **ADAMANTITE_STORAGE_BASIS),
    2: dict(hit_points=1200, **ADAMANTITE_STORAGE_BASIS),
    3: dict(hit_points=1400, **ADAMANTITE_STORAGE_BASIS),
    4: dict(hit_points=1700, **ADAMANTITE_STORAGE_BASIS),
}

VAULT_BASIS = {
    'alias': 'vault',
    'role': 'building',
    'type': 'vault',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

VAULTS = {
    1: dict(hit_points=1000, **VAULT_BASIS),
    2: dict(hit_points=1100, **VAULT_BASIS),
    3: dict(hit_points=1200, **VAULT_BASIS),
    4: dict(hit_points=1300, **VAULT_BASIS),
}

LABORATORY_BASIS = {
    'alias': 'lab',
    'role': 'building',
    'type': 'laboratory',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

LABORATORIES = {
    1: dict(hit_points=1200, **LABORATORY_BASIS),
    2: dict(hit_points=1300, **LABORATORY_BASIS),
}

CRAFT_PAD_BASIS = {
    'alias': 'craft-pad',
    'role': 'building',
    'type': 'craftPad',
    'size': 3,
    'status': 'idle',
    'tile_position': None,
    'level': None,
    'player_id': None,
}

CRAFT_PADS = {
    1: dict(hit_points=1000, **CRAFT_PAD_BASIS),
    2: dict(hit_points=1200, **CRAFT_PAD_BASIS),
    3: dict(hit_points=1400, **CRAFT_PAD_BASIS),
    4: dict(hit_points=1700, **CRAFT_PAD_BASIS),
    5: dict(hit_points=2000, **CRAFT_PAD_BASIS),
}


def command_center(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(COMMAND_CENTERS, level, tile_position, player_id)


def crystalite_farm(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(CRYSTALITE_FARMS, level, tile_position, player_id)


def adamantite_mine(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(ADAMANTITE_MINES, level, tile_position, player_id)


def crystalite_silo(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(CRYSTALITE_SILOS, level, tile_position, player_id)


def adamantite_storage(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(ADAMANTITE_STORAGES, level, tile_position, player_id)


def vault(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(VAULTS, level, tile_position, player_id)


def laboratory(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(LABORATORIES, level, tile_position, player_id)


def craft_pad(level: int, tile_position: [int, int], player_id: int) -> dict:
    return create_building(CRAFT_PADS, level, tile_position, player_id)
