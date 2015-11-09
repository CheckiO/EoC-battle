from tornado import gen
from tornado.ioloop import IOLoop

from random import choice
from tools import precalculated, fill_square, grid_to_graph
from tools import ROLE, ATTRIBUTE, PARTY, ACTION, STATUS, INITIAL, DEFEAT_REASON, OUTPUT, STD,\
    OBSTACLE

from checkio_referee import RefereeBase
from checkio_referee.handlers.base import BaseHandler

import settings_env
from actions import ItemActions
from actions.exceptions import ActionValidateError, ActionSkip
from environment import BattleEnvironmentsController
from tools.distances import euclidean_distance
from tools.terms import PLAYER, ENV
from tools.result_processors import unit_dispersion

CUT_FROM_BUILDING = 1
COORDINATE_EDGE_CUT = 10 ** -3


class Item(object):
    ITEMS_COUNT = 0

    @classmethod
    def generate_id(cls):
        cls.ITEMS_COUNT += 1
        return cls.ITEMS_COUNT


class FightItem(Item):
    """
        class for a single item in the fight.
        It can be a simple building, a defence building,
        a unit that move and attack other buildings
    """
    HANDLERS = None
    ACTIONS = None

    def __init__(self, item_data, player, fight_handler):
        self.init_handlers()
        self.id = self.generate_id()
        self.craft_id = item_data.get(ATTRIBUTE.CRAFT_ID)
        self.player = player  # dict, data about the player who owns this Item
        # available types: center, unit, tower, building, obstacle
        self.role = item_data.get(ATTRIBUTE.ROLE)  # type of current Item

        self.item_type = item_data.get(ATTRIBUTE.ITEM_TYPE)
        self.alias = item_data.get(ATTRIBUTE.ALIAS)
        self.level = item_data.get(ATTRIBUTE.LEVEL, 1)
        self.tile_position = item_data.get(ATTRIBUTE.TILE_POSITION)
        self.item_status = item_data.get(ATTRIBUTE.ITEM_STATUS, 'idle')

        self.start_hit_points = item_data.get(ATTRIBUTE.HIT_POINTS)
        self.hit_points = item_data.get(ATTRIBUTE.HIT_POINTS)
        self.size = item_data.get(ATTRIBUTE.SIZE, 0)
        self.base_size = item_data.get(ATTRIBUTE.BASE_SIZE, 0)
        self.speed = item_data.get(ATTRIBUTE.SPEED)

        self.coordinates = item_data.get(ATTRIBUTE.COORDINATES)  # list of two

        self.rate_of_fire = item_data.get(ATTRIBUTE.RATE_OF_FIRE)
        self.damage_per_shot = item_data.get(ATTRIBUTE.DAMAGE_PER_SHOT)
        self.firing_range = item_data.get(ATTRIBUTE.FIRING_RANGE)
        self.area_damage_per_shot = item_data.get(ATTRIBUTE.AREA_DAMAGE_PER_SHOT, 0)
        self.area_damage_radius = item_data.get(ATTRIBUTE.AREA_DAMAGE_RADIUS, 0)

        # a current command that was send from code
        self.action = item_data.get(ACTION.REQUEST_NAME)
        self.charging = 0

        self._fight_handler = fight_handler  # object of FightHandler
        self.code = self._fight_handler.codes.get(item_data.get(ATTRIBUTE.OPERATING_CODE))
        self._initial = item_data
        self._env = None  # ??
        self._state = None  # dict of current FightItem state
        self._action_queue = []

        self._std = {
            "out": [],
            "err": []
        }
        self.messages =[]
        # every state has a key "action"
        # {'action': 'idle'}
        # {'action': 'dead'}
        self._actions_handlers = ItemActions.get_factory(self, fight_handler=fight_handler)

    def add_message(self, message, from_id):
        self.messages.append([message, from_id])

    def pop_last_message(self):
        if not self.messages:
            return
        return self.messages.pop(0)

    @property
    def is_dead(self):
        return self.hit_points <= 0

    @property
    def is_obstacle(self):
        return self.role == "obstacle"

    @property
    def info(self):
        return {
            ATTRIBUTE.ID: self.id,
            ATTRIBUTE.CRAFT_ID: self.craft_id,
            ATTRIBUTE.PLAYER_ID: self.player["id"],
            ATTRIBUTE.ROLE: self.role,
            ATTRIBUTE.HIT_POINTS: self.hit_points,
            ATTRIBUTE.SIZE: self.size,
            ATTRIBUTE.SPEED: self.speed,
            ATTRIBUTE.COORDINATES: self.coordinates,
            ATTRIBUTE.RATE_OF_FIRE: self.rate_of_fire,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.AREA_DAMAGE_PER_SHOT: self.area_damage_per_shot,
            ATTRIBUTE.AREA_DAMAGE_RADIUS: self.area_damage_radius,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ACTION.REQUEST_NAME: self.action,
            ATTRIBUTE.LEVEL: self.level,
            # TODO State should be reworked
            ATTRIBUTE.IS_DEAD: self.is_dead,
            'state': self._state
        }

    @property
    def internal_info(self):
        info = self.info
        info.update({
            'std': self._std
        })
        return info

    def init_handlers(self):
        """
            there are only 3 kind of actions that can be send from FightItem to Referee
            set_action - to command unit to do
            subscribe - to subscribe on some event
        """
        self.HANDLERS = {
            'set_action': self.method_set_action,
            'subscribe': self.method_subscribe,
        }

    def get_percentage_hit_points(self):
        return max(0, round(100 * self.hit_points / self.start_hit_points))

    def get_action_status(self):
        return self._state["action"]

    def set_state_idle(self):
        self._fight_handler.send_im_idle(self.id)
        self._state = {'action': 'idle'}

    def set_state_dead(self):
        if self.size:
            self._fight_handler.clear_from_map(self)
        self._state = {'action': 'dead'}

    def set_coordinates(self, coordinates):
        self.coordinates = coordinates
        self._fight_handler.send_range_events(self.id)

    @property
    def is_executable(self):
        if self.role == ROLE.UNIT:
            if self.coordinates is not None:
                return True
        elif self.code is not None:
            return True
        return False

    @gen.coroutine
    def start(self):
        raise ValueError('SSTART')
        if not self.is_executable:
            return
        controller = self._fight_handler._referee.environments_controller
        self._env = yield controller.get_environment(self.player[PLAYER.ENV_NAME],
                                                     on_stdout=self.stdout,
                                                     on_stderr=self.stderr)
        env_data = self._fight_handler.get_env_data()
        my_data = self._fight_handler.get_my_data(self.id)
        result = yield self._env.run_code(self.code, env_data, my_data)
        while True:
            if result is not None:
                status = result.pop('status')
                if status and status != STATUS.SUCCESS:
                    pass  # TODO:
                self.handle_result(result)
            result = yield self._env.read_message()

    def stdout(self, connection_id, out):
        self._std[STD.OUT].append(out)

    def stderr(self, connection_id, err):
        self._std[STD.ERR].append(err)

    def has_std(self, std_name):
        return bool(self._std[std_name])

    def pull_std(self, std_name):
        data = "".join(self._std[std_name])
        self._std[std_name] = []
        return data

    def handle_result(self, data):
        handler_name = data.pop('method', None)
        if handler_name is None:
            # raise Exception("WTF")
            return  # TODO: this data is not from commander, then for what?
        handler = self.HANDLERS[handler_name]
        handler(**data)

    def method_set_action(self, action, data):
        try:
            self.action = self._actions_handlers.parse_action_data(action, data)
        except ActionValidateError as e:
            self._env.bad_action(e)
        except ActionSkip:
            self._env.confirm()
        else:
            self._env.confirm()

    def method_subscribe(self, event, lookup_key, data):
        result = self._fight_handler.subscribe(event, self.id, lookup_key, data)
        if not result:
            self._env.bad_action("Subscribing Error")
            return
        self._env.confirm()

    def do_frame_action(self):
        try:
            self._state = self._actions_handlers.do_action(self.action)
        except ActionValidateError:
            self.set_state_idle()

    def send_event(self, lookup_key, data):
        self._env.send_event(lookup_key, data)


class CraftItem(Item):
    def __init__(self, item_data, player, fight_handler):
        self.id = self.generate_id()
        self.craft_id = item_data.get(ATTRIBUTE.CRAFT_ID)
        self.unit_type = item_data.get(ATTRIBUTE.UNIT_TYPE)
        self.coordinates = item_data.get(ATTRIBUTE.COORDINATES)
        self.tile_position = item_data.get(ATTRIBUTE.COORDINATES)[:]
        self.level = item_data.get(ATTRIBUTE.LEVEL)
        self.alias = item_data.get(ATTRIBUTE.ALIAS)
        self.item_type = item_data.get(ATTRIBUTE.ITEM_TYPE)
        self.initial_amount_units_in = self.amount_units_in = item_data.get(ATTRIBUTE.UNIT_QUANTITY)
        craft_coor = item_data[ATTRIBUTE.COORDINATES]
        self.units_position = [[craft_coor[0] + shift[0], craft_coor[1] + shift[1]]
                               for shift in precalculated.LAND_POSITION_SHIFTS[:self.amount_units_in]]

        # im not sute it is nessesary, but still...
        self.item_data = item_data
        self.player = player
        self.role = ROLE.CRAFT

    @property
    def info(self):
        return {
            ATTRIBUTE.ID: self.id,
            ATTRIBUTE.PLAYER_ID: self.player.get("id"),
            ATTRIBUTE.ROLE: self.role,
            ATTRIBUTE.COORDINATES: self.coordinates,
            ATTRIBUTE.LEVEL: self.level,
            ATTRIBUTE.ITEM_TYPE: self.item_type,  # TODO: I think we need only one of them :)
            ATTRIBUTE.UNIT_TYPE: self.unit_type,
            ATTRIBUTE.INITIAL_UNITS_IN: self.initial_amount_units_in,
            ATTRIBUTE.UNITS_IN: self.amount_units_in
        }


class FightHandler(BaseHandler):
    """
        The main class of the game.
        Where all the game calculation do
    """

    FIRST_STEP_FRAME_TIME = 0.5
    FRAME_TIME = 0.02  # compute and send info each time per FRAME_TIME
    GAME_FRAME_TIME = 0.1  # per one FRAME_TIME in real, in game it would be GAME_FRAME_TIME
    GRID_SCALE = 2
    CELL_SHIFT = 1 / (GRID_SCALE * 2)
    ACCURACY_RANGE = 0.1
    UNITS_LANDING_PERIOD = 0.2

    """
    Each item of an EVENT must have next structure:
    {
        'receiver_id': <item_id>,
        'lookup_key': <lookup_function_key>,
        'data': <data_for_check_event>
    }
    """
    EVENTS = {
        'death': [],
        'im_in_area': [],
        'any_item_in_area': [],
        'im_stop': [],
        'im_idle': [],
        'enemy_in_my_firing_range': [],
        'the_item_out_my_firing_range': [],
        'time': [],
        'message': []
    }

    def __init__(self, editor_data, editor_client, referee):
        """
            self.players is a dict and will be defined at the start of the game
            where key is player ID and value is a dict
            {
                'id': 0,
                'env_name': 'python_3',
                'defeat': 'center'
            }
            defeat shows the rules for defeating current player
                center - to loose a command center
                units - to loose all the units
                time - time is out
        """
        self.players = {}
        self.codes = {}
        self.is_stream = True
        self.battle_log = {
            OUTPUT.INITIAL_CATEGORY: {
                OUTPUT.BUILDINGS: [],
                OUTPUT.OBSTACLES: [],
                OUTPUT.UNITS: [],
                OUTPUT.CRAFTS: [],
                OUTPUT.PLAYERS: []
            },
            OUTPUT.FRAME_CATEGORY: [],
            OUTPUT.RESULT_CATEGORY: {}
        }
        self.map_size = (0, 0)
        self.map_grid = [[]]
        self.map_graph = {}
        self.time_limit = float("inf")
        self.map_hash = 0
        """
            self.fighters is a dict of all available fighters on the map.
            where key is an id of the fighter and value is an object of FightItem
        """
        self.fighters = {}
        self.crafts = {}

        self.current_frame = 0
        self.current_game_time = 0
        self.initial_data = editor_data['battle_info']
        self.rewards = {}
        self.defeat_reason = None

        self.editor_client = editor_client
        self._referee = referee

        self.environment = None
        self._is_stopping = None
        self._stop_callback = None

        self.unit_landing_countdown = 0
        self.crafts_landing_stack = []

    def get_my_data(self, id):
        fighter = self.fighters[id]
        return {
            'id': id,
            'level': fighter.level,
            'role': fighter.role,
            'type': fighter.item_type
        }

    def get_env_data(self):
        return {
            'map': self.get_env_map_data(),
            'crafts': self.get_env_crafts_data(),
            'game': self.get_env_game_data()
        }

    def get_env_map_data(self):
        data = {}
        for key, value in self.fighters.items():
            if value.is_obstacle:
                continue
            data[key] = value.info
        return data

    def get_env_crafts_data(self):
        data = {}
        for key, value in self.crafts.items():
            data[key] = value.info
        return data

    def get_env_game_data(self):
        return {
            'time': self.current_game_time,
            'time_accuracy': self.GAME_FRAME_TIME,
            'map_size': self.map_size,
            'time_limit': self.time_limit
        }

    def add_messages_to(self, message, ids, from_id):
        for item_id in ids:
            self.fighters[item_id].add_message(message, from_id)

    @gen.coroutine
    def start(self):
        self.is_stream = self.initial_data.get(INITIAL.IS_STREAM, True)
        # WHY: can't we move an initialisation of players in the __init__ function?
        # in that case we can use it before start
        self.players = {p['id']: p for p in self.initial_data[PLAYER.KEY]}
        self.players[-1] = {"id": -1}
        for code_data in self.initial_data[INITIAL.CODES]:
            self.codes[code_data["id"]] = code_data["code"]

        self.map_size = self.initial_data[INITIAL.MAP_SIZE]
        self.rewards = self.initial_data.get(INITIAL.REWARDS, {})
        self.strat_rewards = self.initial_data.get(INITIAL.STRAT_REWARDS, {})
        self.time_limit = self.initial_data.get(INITIAL.TIME_LIMIT, float("inf"))
        fight_items = []
        for item in self.initial_data[INITIAL.MAP_ELEMENTS]:
            player = self.players[item.get(PLAYER.PLAYER_ID, -1)]
            if item[ATTRIBUTE.ROLE] == ROLE.CRAFT:
                self.add_craft_item(item, player)
            else:
                fight_items.append(self.add_fight_item(item, player))

        self._log_initial_state()

        self.compute_frame()
        self.create_map()
        self.create_route_graph()
        yield fight_items

    def create_map(self):
        height = self.map_size[0] * self.GRID_SCALE
        width = self.map_size[1] * self.GRID_SCALE
        self.map_grid = [[1] * width for _ in range(height)]
        for it in self.fighters.values():
            if not it.size:
                continue
            size = it.size * self.GRID_SCALE
            fill_square(self.map_grid, int(it.coordinates[0] * self.GRID_SCALE) - size // 2,
                        int(it.coordinates[1] * self.GRID_SCALE) - size // 2, size, 0)
        self.hash_grid()

    def adjust_coordinates(self, x, y):
        adjust = lambda t, edge: min(max(t, 0), edge - COORDINATE_EDGE_CUT)
        return adjust(x, self.map_size[0]), adjust(y, self.map_size[1])

    def create_route_graph(self):
        self.map_graph = grid_to_graph(self.map_grid)

    def hash_grid(self):
        self.map_hash = hash(tuple(map(tuple, self.map_grid)))

    def clear_from_map(self, item):
        size = item.size * self.GRID_SCALE
        fill_square(self.map_grid, item.coordinates[0] * self.GRID_SCALE - size // 2,
                    item.coordinates[1] * self.GRID_SCALE - size // 2, size, 1)
        self.create_route_graph()
        self.hash_grid()

    @gen.coroutine
    def add_fight_item(self, item_data, player):
        size = item_data.get(ATTRIBUTE.SIZE, 0)
        # [SPIKE] We use center coordinates
        coordinates = [
            round(item_data[ATTRIBUTE.TILE_POSITION][0] + size / 2, 6),
            round(item_data[ATTRIBUTE.TILE_POSITION][1] + size / 2, 6)]
        # [SPIKE] We use center coordinates
        cut_size = (size if item_data[ATTRIBUTE.ROLE] == ROLE.OBSTACLE
                    else max(size - CUT_FROM_BUILDING, 0))
        item_data[ATTRIBUTE.BASE_SIZE] = size
        item_data[ATTRIBUTE.SIZE] = cut_size
        item_data[ATTRIBUTE.COORDINATES] = coordinates
        fight_item = FightItem(item_data, player=player, fight_handler=self)
        self.fighters[fight_item.id] = fight_item
        if self.current_frame:
            self._log_initial_unit(fight_item)
        fight_item.set_state_idle()
        yield fight_item.start()

    def add_craft_item(self, craft_data, player):
        craft_coor = self.generate_craft_place()
        if not craft_coor[1]:
            return
        craft_data[ATTRIBUTE.COORDINATES] = craft_coor
        in_unit_description = craft_data[ATTRIBUTE.IN_UNIT_DESCRIPTION]
        craft_data[ATTRIBUTE.UNIT_TYPE] = in_unit_description[ATTRIBUTE.ITEM_TYPE]
        craft = CraftItem(craft_data, player=player, fight_handler=self)
        self.crafts[craft.id] = craft
        self.crafts_landing_stack.append(craft.id)
        return craft

    @gen.coroutine
    def add_unit_from_craft(self, craft):
        craft_data = craft.item_data
        unit = craft_data[ATTRIBUTE.IN_UNIT_DESCRIPTION].copy()
        unit[ATTRIBUTE.OPERATING_CODE] = craft_data[ATTRIBUTE.OPERATING_CODE]
        unit_position = craft.units_position.pop()
        unit[ATTRIBUTE.COORDINATES] = unit_position
        unit[ATTRIBUTE.TILE_POSITION] = unit_position[:]
        unit[ATTRIBUTE.ROLE] = ROLE.UNIT
        unit[ATTRIBUTE.CRAFT_ID] = craft.craft_id
        craft.amount_units_in -= 1
        yield self.add_fight_item(unit, self.players[craft_data.get(PLAYER.PLAYER_ID, -1)])

    def generate_craft_place(self):
        width = self.map_size[1]
        craft_positions = [cr.coordinates[1] for cr in self.crafts.values()]
        available = [y for y in range(6, width - 6)
                     if not any(pos - 5 <= y <= pos + 5 for pos in craft_positions)]
        return [self.map_size[0], choice(available) if available else 0]

    def all_crafts_empty(self):
        for craft in self.crafts.values():
            if craft.amount_units_in:
                return False
        return True

    @gen.coroutine
    def unit_lands_from_stack(self):
        if self.unit_landing_countdown > 0:
            self.unit_landing_countdown -= self.GAME_FRAME_TIME
            return
        self.unit_landing_countdown = self.UNITS_LANDING_PERIOD
        craft_id = self.crafts_landing_stack.pop()
        craft = self.crafts[craft_id]
        if craft.amount_units_in > 1:
            self.crafts_landing_stack.insert(0, craft_id)
        yield self.add_unit_from_craft(craft)

    @gen.coroutine
    def compute_frame(self):
        """
            calculate every frame and action for every FightItem
        """
        self.send_frame()
        self.current_frame += 1
        self.current_game_time += self.GAME_FRAME_TIME

        for key, fighter in self.fighters.items():
            # WHY: can't we move in the FightItem class?
            # When in can be None?
            if fighter.is_dead:
                continue

            if fighter.action is None:
                fighter.set_state_idle()
                continue

            fighter.do_frame_action()

        self._send_time()
        self._send_message()

        winner = None
        if self.all_crafts_empty():
            winner = self.get_winner()

        if winner is not None:
            self.send_frame({'winner': winner}, True)
            IOLoop.current().call_later(3, self.stop)
        else:
            if self.all_crafts_empty() or self.unit_landing_countdown > 0:
                frame_time = self.FRAME_TIME
            else:
                frame_time = self.FIRST_STEP_FRAME_TIME
            IOLoop.current().call_later(frame_time, self.compute_frame)

        if self.crafts_landing_stack:
            yield self.unit_lands_from_stack()

    def count_unit_casualties(self):
        result = {craft.craft_id: {
            OUTPUT.CRAFT_ID: craft.craft_id,
            OUTPUT.COUNT: 0,
            OUTPUT.ITEM_TYPE: craft.unit_type} for craft in self.crafts.values()}
        for it in self.fighters.values():
            if it.is_dead and it.role in ROLE.UNIT:
                result[it.craft_id][OUTPUT.COUNT] += 1
        return [casualty for casualty in result.values() if casualty[OUTPUT.COUNT]]

    def get_winner(self):
        for player_id, player in tuple(self.players.items()):
            if self._is_player_defeated(player):
                del self.players[player_id]
            real_players = [k for k in self.players if k >= 0]
            if len(real_players) == 1:
                self.battle_log[OUTPUT.RESULT_CATEGORY] = {
                    OUTPUT.WINNER: real_players[0],
                    OUTPUT.REWARDS: self.rewards,
                    OUTPUT.STRAT_REWARDS: self.strat_rewards,
                    OUTPUT.CASUALTIES: self.count_unit_casualties(),
                    OUTPUT.DEFEAT_REASON: self.defeat_reason
                }
                return self.players[real_players[0]]
        return None

    def _is_player_defeated(self, player):
        defeat_reasons = player.get(PLAYER.DEFEAT_REASONS, [])
        if (DEFEAT_REASON.UNITS in defeat_reasons and
                not self._is_player_has_item_role(player, ROLE.UNIT)):
            self.defeat_reason = DEFEAT_REASON.UNITS
            return True
        elif (DEFEAT_REASON.CENTER in defeat_reasons and
                not self._is_player_has_item_role(player, ROLE.CENTER)):
            self.defeat_reason = DEFEAT_REASON.CENTER
            return True
        elif DEFEAT_REASON.TIME in defeat_reasons and self.current_game_time >= self.time_limit:
            self.defeat_reason = DEFEAT_REASON.TIME
            return True
        return False

    def _is_player_has_item_role(self, player, role):
        for item in self.fighters.values():
            if item.player['id'] == player['id'] and item.role == role and not item.is_dead:
                return True
        return False

    def send_frame(self, status=None, battle_finished=False):
        """
            prepare and send data to an interface for visualisation
        """
        if self.is_stream:
            # TODO: DEPRECATED Change to single out format
            if status is None:
                status = {}

            fight_items = [fighter.internal_info for fighter in self.fighters.values()]
            craft_items = [craft.info for craft in self.crafts.values()]
            self.editor_client.send_battle({
                "is_stream": True,
                'status': status,
                'fight_items': fight_items,
                'craft_items': craft_items,
                'map_size': self.map_size,
                'map_grid': self.map_grid,
                'current_frame': self.current_frame,
                'current_game_time': self.current_game_time
            })
        self.battle_log["frames"].append(self._get_battle_snapshot())
        if battle_finished:
            self.editor_client.send_battle(unit_dispersion(self.battle_log))

    def _log_initial_state(self):
        for item in self.fighters.values():
            if item.role == ROLE.UNIT:
                self._log_initial_unit(item)
            elif item.role in ROLE.PLAYER_STATIC:
                self._log_initial_building(item)
            elif item.role == ROLE.OBSTACLE:
                if item.item_type == OBSTACLE.ROCK:
                    self._log_initial_obstacle(item)
                elif item.item_type == OBSTACLE.FLAG_STOCK:
                    self._log_initial_flag_stock(item)
                else:
                    self._log_initial_building(item)
        for craft in self.crafts.values():
            self._log_initial_craft(craft)
        for player in self.initial_data[PLAYER.KEY]:
            self._log_initial_player(player)
        self._log_system()

    def _log_system(self):
        #  We should use cammel-case attributes while server issue
        self.battle_log[OUTPUT.SYSTEM] = {
            'mapSize': self.map_size,
            'timeLimit': self.time_limit,
            'timeAccuracy': self.GAME_FRAME_TIME
        }

    def _log_initial_unit(self, unit):
        log = self.battle_log[OUTPUT.INITIAL_CATEGORY][OUTPUT.UNITS]
        log.append({
            OUTPUT.ITEM_ID: unit.id,
            OUTPUT.TILE_POSITION: unit.tile_position,
            OUTPUT.ITEM_TYPE: unit.item_type,
            OUTPUT.PLAYER_ID: unit.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: unit.player[PLAYER.ID]
        })

    def _log_initial_building(self, building):
        log_record = {
            OUTPUT.ITEM_ID: building.id,
            OUTPUT.TILE_POSITION: building.tile_position,
            OUTPUT.ITEM_TYPE: building.item_type,
            OUTPUT.SIZE: building.base_size,
            OUTPUT.ALIAS: building.alias,
            OUTPUT.ITEM_STATUS: building.item_status,
            OUTPUT.ITEM_LEVEL: building.level,
            OUTPUT.PLAYER_ID: building.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: building.player[PLAYER.ID]
        }
        log = self.battle_log[OUTPUT.INITIAL_CATEGORY][OUTPUT.BUILDINGS]
        log.append(log_record)
        return log_record

    def _log_initial_flag_stock(self, building):
        log = self._log_initial_building(building)
        log[OUTPUT.FLAG_SLUG] = building.player[PLAYER.ENV_NAME]

    def _log_initial_obstacle(self, obstacle):
        log = self.battle_log[OUTPUT.INITIAL_CATEGORY][OUTPUT.OBSTACLES]
        log.append({
            OUTPUT.TILE_POSITION: obstacle.tile_position,
            OUTPUT.SIZE: obstacle.base_size,
            OUTPUT.ID: obstacle.id,
        })

    def _log_initial_craft(self, craft):
        log = self.battle_log[OUTPUT.INITIAL_CATEGORY][OUTPUT.CRAFTS]
        log.append({
            OUTPUT.ITEM_ID: craft.id,
            OUTPUT.TILE_POSITION: craft.tile_position,
            OUTPUT.ITEM_TYPE: craft.item_type,
            OUTPUT.ALIAS: craft.alias,
            OUTPUT.ITEM_LEVEL: craft.level,
            OUTPUT.PLAYER_ID: craft.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: craft.player[PLAYER.ID]
        })

    def _log_initial_player(self, player):
        log = self.battle_log[OUTPUT.INITIAL_CATEGORY][OUTPUT.PLAYERS]
        log.append({
            OUTPUT.ID: player[PLAYER.ID],
            OUTPUT.USERNAME: player.get(PLAYER.USERNAME, str(player[PLAYER.ID]))
        })

    def _get_battle_snapshot(self):
        snapshot = []
        for item in self.fighters.values():
            if item.is_obstacle:
                continue
            item_info = {
                OUTPUT.ITEM_ID: item.id,
                OUTPUT.TILE_POSITION: (item.coordinates if item.role == ROLE.UNIT
                                       else item.tile_position),
                OUTPUT.HIT_POINTS_PERCENTAGE: item.get_percentage_hit_points(),
                OUTPUT.ITEM_STATUS: item.get_action_status()
            }
            if item_info[ACTION.STATUS] in (ACTION.ATTACK, ACTION.CHARGE):
                item_info[OUTPUT.FIRING_POINT] = item._state[ACTION.FIRING_POINT]
                item_info[OUTPUT.FIRING_ID] = item._state[ACTION.AID]
                # TODO LEGACY DEPRECATED
                item_info[OUTPUT.FIRING_POINT_LEGACY] = item_info[OUTPUT.FIRING_POINT]

            if item_info[ACTION.STATUS] == ACTION.ATTACK:
                item_info[OUTPUT.DEMAGED] = item._state[ACTION.DEMAGED]

            if item.has_std(STD.OUT):
                item_info[OUTPUT.STDOUT] = item.pull_std(STD.OUT)
            if item.has_std(STD.ERR):
                item_info[OUTPUT.STDERR] = item.pull_std(STD.ERR)

            snapshot.append(item_info)
        return snapshot

    def subscribe(self, event_name, item_id, lookup_key, data):
        """
            subscribe an FightItem with ID "item_id" on event "event_name" with data "data"
            and on item side it registered as lookup_key
        """
        if event_name == "unsubscribe_all":
            event_item = self.fighters[item_id]
            self.unsubscribe(event_item)
            return
        if event_name not in self.EVENTS:
            return
        subscribe_data = {
            'receiver_id': item_id,
            'lookup_key': lookup_key,
            'data': data
        }
        event = self.EVENTS[event_name]
        if subscribe_data in event:
            return False
        event.append(subscribe_data)
        return True

    def unsubscribe(self, item):
        """
            unsubscribe item from all events
        """
        # WHY: don't we call this method unsubscribe_item or unsubscribe_all
        # because if we have subscribe method working in one way then
        # unsubscribe should work in opposite
        for events in self.EVENTS.values():
            for event in events[:]:
                if event['receiver_id'] == item.id:
                    events.remove(event)

    def _send_event(self, event_item_id, event_name, check_function, data_function):
        if event_item_id:
            event_item = self.fighters.get(event_item_id)
        else:
            event_item = None
        events = self.EVENTS.get(event_name, [])
        for event in events[:]:
            receiver = self.fighters[event['receiver_id']]
            if check_function(event, event_item, receiver):
                data_to_event = data_function(event, event_item, receiver)
                data_to_event.update({
                    ENV.DATA: self.get_env_data(),
                    ENV.MY_DATA: self.get_my_data(event['receiver_id'])
                })
                receiver.send_event(lookup_key=event['lookup_key'],
                                    data=data_to_event)
                events.remove(event)

    @staticmethod
    def _data_event_id(event, event_item, receiver):
        return {'id': event_item.id}

    @staticmethod
    def _check_event_equal_receiver(event, event_item, receiver):
        return receiver.id == event_item.id

    def send_death_event(self, event_item_id):
        """
            send "death" event of FightItem with ID "item_id"
            to all FightItem who subscribe on it
        """

        def check_function(event, event_item, receiver):
            return event['data'][ATTRIBUTE.ID] == event_item.id

        self._send_event(event_item_id, "death", check_function, self._data_event_id)

    def send_im_stop(self, event_item_id):
        """
        Send "stop" event to Item with "item_id"
        """

        def data_function(event, event_item, receiver):
            return {ATTRIBUTE.ID: event_item.id, ATTRIBUTE.COORDINATES: event_item.coordinates}

        self._send_event(event_item_id, "im_stop", self._check_event_equal_receiver, data_function)

    def send_im_idle(self, event_item_id):
        """
        Send "stop" event to Item with "item_id"
        """
        self._send_event(event_item_id, "im_idle",
                         self._check_event_equal_receiver, self._data_event_id)

    def send_range_events(self, event_item_id):
        """
            send "range" event to all FightItems who subscribe on changing event
            if FightItem with ID "item_id" gets in their range
        """
        # TODO: to make 2 signals. get_in_range and get_out_range
        # TODO: if item is moving it is impossible for stable unit to get to its firing_range
        self._send_enemy_in_my_firing_range(event_item_id)
        self._send_the_item_out_my_firing_range(event_item_id)
        self._send_im_in_area(event_item_id)
        self._send_any_item_in_area(event_item_id)

    def _send_im_in_area(self, event_item_id):
        """
        Send "range" event for owner item about it's in an area
        """

        def check_function(event, event_item, receiver):
            if receiver.id == event_item.id:
                distance = euclidean_distance(receiver.coordinates, event["data"]["coordinates"])
                return distance < event["data"]["radius"]
            return False

        def data_function(event, event_item, receiver):
            distance = euclidean_distance(receiver.coordinates, event["data"]["coordinates"])
            return {ATTRIBUTE.ID: event_item.id, "distance": distance}

        self._send_event(event_item_id, "im_in_area", check_function, data_function)

    def _send_enemy_in_my_firing_range(self, event_item_id):
        """
        Send "range" event to owner if any item in firing range
        """

        def check_function(event, event_item, receiver):
            if (receiver.id != event_item.id and
                    not event_item.is_obstacle and
                    event_item.player != receiver.player):
                distance = euclidean_distance(receiver.coordinates, event_item.coordinates)
                return distance - event_item.size / 2 <= receiver.firing_range
            return False

        self._send_event(event_item_id, "enemy_in_my_firing_range",
                         check_function, self._data_event_id)

    def _send_the_item_out_my_firing_range(self, event_item_id):
        """
        Send "range" event to owner if the item out firing range
        """

        def check_function(event, event_item, receiver):
            if event["data"]["item_id"] == event_item.id:
                distance = euclidean_distance(receiver.coordinates, event_item.coordinates)
                return distance - event_item.size / 2 > receiver.firing_range
            return False

        self._send_event(event_item_id, "the_item_out_my_firing_range",
                         check_function, self._data_event_id)

    def _send_any_item_in_area(self, event_item_id):
        """
        Send "range" event about an item in the area for all FightItem who subscribed.
        """

        def check_function(event, event_item, receiver):
            distance = euclidean_distance(event['data']['coordinates'], event_item.coordinates)
            return distance <= event['data']['radius']

        self._send_event(event_item_id, "any_item_in_area", check_function, self._data_event_id)

    def _send_time(self):
        """
            Send Time at specific time
        """

        def check_function(event, event_item, receiver):
            return self.current_game_time >= event['data']['time']

        def time_data(event, event_item, receiver):
            return {'time': event['data']['time']}

        self._send_event(None, 'time', check_function, time_data)

    def _send_message(self):
        '''
            Send message to a specific unit
        '''
        def check_function(event, event_item, receiver):
            return receiver.messages

        def message_data(event, event_item, receiver):
            mess = receiver.pop_last_message()
            return {'message': mess[0], 'from_id': mess[1]}

        self._send_event(None, 'message', check_function, message_data)


class Referee(RefereeBase):
    ENVIRONMENTS = settings_env.ENVIRONMENTS
    EDITOR_LOAD_ARGS = ('battle_info', 'action')
    HANDLERS = {
        'battle': FightHandler
    }

    @property
    def environments_controller(self):
        if not hasattr(self, '_environments_controller'):
            setattr(self, '_environments_controller', BattleEnvironmentsController(
                self.ENVIRONMENTS))
        return getattr(self, '_environments_controller')
