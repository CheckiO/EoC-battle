__all__ = ["ROLE", "PARTY"]


class PARTY():
    REQUEST_NAME = 'parties'
    MY = 'my'
    ENEMY = 'enemy'
    ALL = (MY, ENEMY)


class ROLE():
    REQUEST_NAME = 'roles'
    CENTER = 'center'
    TOWER = 'tower'
    UNIT = 'unit'
    BUILDING = 'building'
    OBSTACLE = 'obstacle'
    ALL = (CENTER, TOWER, UNIT, BUILDING, OBSTACLE)
