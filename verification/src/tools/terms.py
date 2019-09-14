__all__ = ['ROLE', 'PARTY', 'ATTRIBUTE', 'ACTION', 'STATUS',
           'INITIAL', 'PLAYER', 'DEFEAT_REASON', 'OUTPUT', "STD", 'OBSTACLE', 'DEF_TYPE', 'ATTACK_TYPE']


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
    FLAGMAN = 'flagman'
    MINE = 'mine'
    DEF_PLATFORM = 'defPlatform'
    ALL = (CENTER, TOWER, UNIT, BUILDING, OBSTACLE)
    STATIC = (BUILDING, CENTER, OBSTACLE, TOWER)
    PLAYER_STATIC = (BUILDING, CENTER, TOWER)


class DEF_TYPE():
    SENTRY = 'sentryGun'
    MACHINE = 'machineGun'
    ROCKET_GUN = 'rocketGun'


class ATTACK_TYPE():
    INFANTRY = 'infantryBot'
    HEAVY = 'heavyBot'
    ROCKET_BOT = 'rocketBot'


class OBSTACLE():
    ROCK = 'rock'
    FLAG_STOCK = 'flagStock'


class ATTRIBUTE():
    ID = 'id'
    PLAYER_ID = 'player_id'
    CRAFT_ID = 'craft_id'
    COORDINATES = 'coordinates'
    LEVEL = 'level'
    TILE_POSITION = 'tile_position'
    SPEED = 'speed'

    ITEM_TYPE = 'type'
    UNIT_TYPE = 'unit_type'
    ROLE = 'role'
    ITEM_STATUS = 'status'
    HIT_POINTS = 'hit_points'
    SIZE = 'size'
    BASE_SIZE = 'base_size'
    UNIT_QUANTITY = 'unit_quantity'
    IN_UNIT_DESCRIPTION = 'unit'
    OPERATING_CODE = 'code'
    OPERATING_CODE_OPTS = 'code_opts'
    ANGLE = 'angle'
    ACTION = 'action'
    INITIAL_UNITS_IN = 'initial_units_in'
    UNITS_IN = 'units_in'
    IS_GONE = 'is_gone'
    IS_DEAD = 'is_dead'
    IS_DEPARTED = 'is_departed'
    STATE = 'state'
    IS_FLYING = 'is_flying'
    OPERATIONS = 'operations'
    CHARGE_SIZE = 'charge_size'
    CHARGE = 'charge'
    SUBITEMS = 'subitems'
    EXTRAS = 'extras'
    MODULES = 'modules'
    CRAFT_FIGHT_ID = 'craft_fight_id'
    IS_IMMORTAL = 'is_immortal'
    # MachineGun Attributes
    FIELD_OF_VIEW = 'field_of_view'
    RATE_OF_TURN = 'rate_of_turn'
    DAMAGE_PER_SECOND = 'damage_per_second'
    FIRING_TIME_LIMIT = 'firing_time_limit'
    FULL_COOLDOWN_TIME = 'full_cooldown_time'
    MIN_PERCENTAGE_AFTER_OVERHEAT = 'min_percentage_after_overheat'
    FIRING_TIME = 'firing_time'
    OVERHEATED = 'overheated'
    # SentryGun Attributes
    CHARGING_TIME = 'charging_time'
    DAMAGE_PER_SHOT = 'damage_per_shot'
    FIRING_RANGE = 'firing_range'
    FIRING_RANGE_ALWAYS_HIT = 'firing_range_100'
    START_CHANCE = 'start_chance'

    ROCKET_SPEED = 'rocket_speed'
    ROCKET_EXPLOSION_RADIUS = 'rocket_explosion_radius'


class ACTION():
    REQUEST_NAME = 'action'
    STATUS = 'status'
    ATTACK = 'attack'
    FIRING_POINT = 'firing_point'
    AID = 'aid'
    DEMAGED = 'damaged'
    CHARGE = 'charge'


class OPERATION():
    ROCKET = 'rocket'
    HEAL = 'heal'
    POWER = 'power'


class STATUS():
    SUCCESS = 'success'
    FAIL = 'fail'


class INITIAL():
    MAP_SIZE = 'map_size'
    TIME_LIMIT = 'time_limit'
    MAP_ELEMENTS = 'map_elements'
    IS_STREAM = 'is_stream'
    REWARDS = 'rewards'
    STRAT_REWARDS = 'strategies'
    CODES = 'codes'
    SEND_PROGRESS = 'send_progress'


class RESOURCE():
    CRYSTALITE = 'crystalite'
    ADAMANTITE = 'adamantite'


class PLAYER():
    KEY = "players"
    ID = "id"
    PLAYER_ID = 'player_id'
    ENV_NAME = 'env_name'
    DEFEAT_REASONS = 'defeat'
    USERNAME = "username"


class DEFEAT_REASON():
    UNITS = 'units'
    CENTER = 'center'
    TIME = 'time'


class OUTPUT():
    ID = "id"
    INITIAL_CATEGORY = 'initial'
    RESULT_CATEGORY = 'result'
    FRAME_CATEGORY = 'frames'
    UNITS = 'units'
    CRAFTS = 'crafts'
    BUILDINGS = 'buildings'
    OBSTACLES = 'obstacles'
    SIZE = 'size'
    PLAYERS = "players"
    PLAYER_ID = "playerId"
    USERNAME = "username"
    ITEM_ID = 'id'
    TILE_POSITION = 'tilePosition'
    ITEM_TYPE = 'type'
    ITEM_STATUS = 'status'
    ITEM_LEVEL = 'level'
    HIT_POINTS_PERCENTAGE = 'hitPointsPer'
    FIRING_POINT = "firingPoint"
    CHARGING_TIME = 'chargingTime'
    FIRING_ID = "firingId"
    FIRING_POINT_LEGACY = "firing_point"
    DEFEAT_REASON = 'reason'
    REWARDS = 'rewards'
    STRAT_REWARDS = 'strategies'
    WINNER = 'winner'
    CASUALTIES = "casualties"
    CRAFT_ID = "craft_id"
    COUNT = "count"
    DEMAGED = 'demaged'
    SYSTEM = 'system'
    FLAG_SLUG = 'flagSlug'
    SUBITEMS = 'subItems'
    ACTION = 'action'
    ANGLE = 'angle'
    FIRING_TIME = 'firing_time'
    DEPARTING_TIME = 'departing_time'
    FLAGS = 'flags'
    ONE_ACTION = 'one_action'
    INTERNAL = 'internal'
    INITIAL_UNITS_IN = 'inUnitsIn'
    UNITS_IN = 'unitsIn'
    STD = 'std'
    STATUS = 'status'
    STATE = 'state'
    OPERATIONS = 'operations'
    FLAGMAN = 'flagman'
    CHARGE = 'charge'
    IS_IMMORTAL = 'is_immortal'


class STD():
    OUT = "out"
    ERR = "err"


class ENV():
    DATA = '__env_data'
    MY_DATA = '__my_data'

class FEATURE():
    TELEPORT = 'teleport'
