__all__ = ["ROLE", "PARTY", "ITEM_TYPE"]


class PARTY():
    REQUEST_NAME = 'parties'
    MY = "my"
    ENEMY = "enemy"
    ALL = (MY, ENEMY)


class ROLE():
    REQUEST_NAME = "roles"
    CENTER = "center"
    TOWER = "tower"
    UNIT = "unit"
    BUILDING = 'building'
    OBSTACLE = "obstacle"
    ALL = (CENTER, TOWER, UNIT, BUILDING, OBSTACLE)

class ITEM_TYPE():
    REQUEST_NAME = "types"
    ROCKETBOT = "rocketBot"
    INFANTRYBOT = "infantryBot"
    HEAVYBOT = "heavyBot"
    SENTRYGUN = "sentryGun"
    MACHINEGUN = "machineGun"
    ROCKETGUN = "rocketGun" #needs checking
    ALL = (ROCKETBOT, INFANTRYBOT, HEAVYBOT, SENTRYGUN, MACHINEGUN, ROCKETGUN)
