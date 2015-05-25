__all__ = ['ROLE', 'PARTY', 'ATTRIBUTE', 'ACTION', 'STATUS',
           'INITIAL', 'PLAYER', 'DEFEAT_REASON', 'OUTPUT']


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
    CRAFT = 'craft'
    ALL = (CENTER, TOWER, UNIT, BUILDING, OBSTACLE)
    STATIC = (BUILDING, CENTER, OBSTACLE, TOWER)
    PLAYER_STATIC = (BUILDING, CENTER, TOWER)


class ATTRIBUTE():
    ID = 'id'
    PLAYER_ID = 'player_id'
    ALIAS = 'alias'
    COORDINATES = 'coordinates'
    LEVEL = 'level'
    TILE_POSITION = 'tile_position'
    SPEED = 'speed'
    RATE_OF_FIRE = 'rate_of_fire'
    FIRING_RANGE = 'firing_range'
    AREA_DAMAGE_PER_SHOT = 'area_damage_per_shot'
    DAMAGE_PER_SHOT = 'damage_per_shot'
    AREA_DAMAGE_RADIUS = 'area_damage_radius'
    ITEM_TYPE = 'type'
    ROLE = 'role'
    ITEM_STATUS = 'status'
    HIT_POINTS = 'hit_points'
    SIZE = 'size'
    BASE_SIZE = 'base_size'
    UNIT_QUANTITY = 'unit_quantity'
    IN_UNIT_DESCRIPTION = 'unit'
    OPERATING_CODE = 'code'


class ACTION():
    REQUEST_NAME = 'action'
    STATUS = 'status'
    ATTACK = 'attack'
    FIRING_POINT = "firing_point"


class STATUS():
    SUCCESS = 'success'
    FAIL = 'fail'


class INITIAL():
    MAP_SIZE = 'map_size'
    TIME_LIMIT = 'time_limit'
    MAP_ELEMENTS = 'map_elements'
    IS_STREAM = 'is_stream'
    REWARDS = 'rewards'
    CODES = 'codes'


class RESOURCE():
    CRYSTALITE = 'crystalite'
    ADAMANTITE = 'adamantite'


class PLAYER():
    PLAYER_ID = 'player_id'
    ENV_NAME = 'env_name'
    DEFEAT_REASONS = 'defeat'


class DEFEAT_REASON():
    UNITS = 'units'
    CENTER = 'center'
    TIME = 'time'


class OUTPUT():
    INITIAL_CATEGORY = 'initial'
    RESULT_CATEGORY = 'result'
    FRAME_CATEGORY = 'frames'
    UNITS = 'units'
    CRAFTS = 'crafts'
    BUILDINGS = 'buildings'
    ITEM_ID = 'id'
    TILE_POSITION = 'tilePosition'
    ITEM_TYPE = 'type'
    ALIAS = 'alias'
    ITEM_STATUS = 'status'
    ITEM_LEVEL = 'level'
    HIT_POINTS_PERCENTAGE = 'hitPointPercentage'
    FIRING_POINT = "firingPoint"
    FIRING_POINT_LEGACY = "firing_point"
    DEFEAT_REASON = 'reason'
    REWARDS = 'rewards'
    WINNER = 'winner'
    CASUALTIES = "casualties"
