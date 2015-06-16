__all__ = ["infantry_bot", "heavy_bot", "rocket_bot"]

from .tools import create_unit

INFANTRY_BOT_BASIS = {
    'c_size': 1,
    'firing_range': 4,
    'rate_of_fire': 1,
    'speed': 5,
    'type': 'infantryBot'
}

INFANTRY_BOTS = {
    1: dict(damage_per_shot=50, hit_points=120, **INFANTRY_BOT_BASIS),
    2: dict(damage_per_shot=60, hit_points=150, **INFANTRY_BOT_BASIS),
    3: dict(damage_per_shot=75, hit_points=200, **INFANTRY_BOT_BASIS),
}

HEAVY_BOT_BASIS = {
    'c_size': 4,
    'firing_range': 2.5,
    'rate_of_fire': 10,
    'speed': 3,
    'type': 'heavyBot'
}

HEAVY_BOTS = {
    1: dict(damage_per_shot=5, hit_points=1000, **HEAVY_BOT_BASIS),
    2: dict(damage_per_shot=7, hit_points=1200, **HEAVY_BOT_BASIS),
    3: dict(damage_per_shot=10, hit_points=1400, **HEAVY_BOT_BASIS),
}

ROCKET_BOT_BASIS = {
    'c_size': 2,
    'firing_range': 8,
    'rate_of_fire': 0.5,
    'speed': 4,
    'type': 'rocketBot'
}

ROCKET_BOTS = {
    1: dict(damage_per_shot=150, hit_points=50, **ROCKET_BOT_BASIS),
    2: dict(damage_per_shot=200, hit_points=60, **ROCKET_BOT_BASIS),
    3: dict(damage_per_shot=300, hit_points=80, **ROCKET_BOT_BASIS),
}


def infantry_bot(level: int) -> dict:
    return create_unit(INFANTRY_BOTS, level)


def heavy_bot(level: int) -> dict:
    return create_unit(HEAVY_BOTS, level)


def rocket_bot(level: int) -> dict:
    return create_unit(ROCKET_BOTS, level)
