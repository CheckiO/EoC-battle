__all__ = ["sentry_tower", "machine_gun_tower", "rocket_tower"]

from .tools import create_building

SENTRY_TOWER_BASIS = {
    'alias': 'sniper',
    'type': 'sentryGun',
    'firing_range': 12,
    'rate_of_fire': 0.7,
    'role': 'tower',
    'status': 'idle',
    'size': 3,
    'level': None,
    'tile_position': None,
    'player_id': None,
    'code': None,
}

SENTRY_TOWERS = {
    1: dict(damage_per_shot=56, hit_points=1000, **SENTRY_TOWER_BASIS),
    2: dict(damage_per_shot=65, hit_points=1200, **SENTRY_TOWER_BASIS),
    3: dict(damage_per_shot=75, hit_points=1400, **SENTRY_TOWER_BASIS),
    4: dict(damage_per_shot=87, hit_points=1700, **SENTRY_TOWER_BASIS),
    5: dict(damage_per_shot=100, hit_points=2100, **SENTRY_TOWER_BASIS),
}

MACHINE_GUN_TOWER_BASIS = {
    'alias': 'machine_gun',
    'type': 'machineGun',
    'firing_range': 5,
    'rate_of_fire': 10,
    'role': 'tower',
    'status': 'idle',
    'size': 2,
    'level': None,
    'tile_position': None,
    'player_id': None,
    'code': None,
}

MACHINE_GUN_TOWERS = {
    1: dict(damage_per_shot=10, hit_points=1600, **MACHINE_GUN_TOWER_BASIS),
    2: dict(damage_per_shot=15, hit_points=1750, **MACHINE_GUN_TOWER_BASIS),
    3: dict(damage_per_shot=20, hit_points=2000, **MACHINE_GUN_TOWER_BASIS),
}

ROCKET_TOWER_BASIS = {
    'alias': 'machine_gun',
    'type': 'machineGun',
    'firing_range': 10,
    'rate_of_fire': 0.3,
    'role': 'tower',
    'status': 'idle',
    'size': 2,
    'level': None,
    'tile_position': None,
    'player_id': None,
    'code': None,
}

ROCKET_TOWERS = {
    1: dict(damage_per_shot=150, hit_points=2000, **ROCKET_TOWER_BASIS),
    2: dict(damage_per_shot=200, hit_points=2180, **ROCKET_TOWER_BASIS),
    3: dict(damage_per_shot=300, hit_points=2370, **ROCKET_TOWER_BASIS),
    4: dict(damage_per_shot=420, hit_points=2600, **ROCKET_TOWER_BASIS),
}


def sentry_tower(level: int, tile_position: [int, int], player_id: int, code_id: int) -> dict:
    return create_building(SENTRY_TOWERS, level, tile_position, player_id, code_id)


def machine_gun_tower(level: int, tile_position: [int, int], player_id: int, code_id: int) -> dict:
    return create_building(SENTRY_TOWERS, level, tile_position, player_id, code_id)


def rocket_tower(level: int, tile_position: [int, int], player_id: int, code_id: int) -> dict:
    return create_building(SENTRY_TOWERS, level, tile_position, player_id, code_id)
