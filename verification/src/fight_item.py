from tornado import gen
from tornado.ioloop import IOLoop
import logging
import sys
import traceback
from functools import reduce

from actions import ItemActions
from tools.balance import unit_display_stats, building_display_stats, operation_stats
from tools.distances import euclidean_distance
from consts import CUT_FROM_BUILDING, IMMORTAL_TIME, FOLDER_CODES
from tools import ROLE, ATTRIBUTE, ACTION, STD, PLAYER, STATUS
from tools import precalculated
from actions.exceptions import ActionValidateError, ActionSkip
from modules import gen_features, map_features, has_feature

logger = logging.getLogger(__name__)

class Item(object):
    ITEMS_COUNT = 0
    is_craft = False
    is_flagman = False

    @classmethod
    def generate_id(cls):
        Item.ITEMS_COUNT += 1
        return Item.ITEMS_COUNT


class FightItem(Item):
    """
        class for a single item in the fight.
        It can be a simple building, a defence building,
        a unit that move and attack other buildings
    """
    HANDLERS = None
    ACTIONS = None

    def __init__(self, item_data, player, fight_handler):
        self._fight_handler = fight_handler  # object of FightHandler
        self.init_handlers()
        self.id = self.generate_id()
        item_data = self.adj_item_data(item_data);
        self.craft_id = item_data.get(ATTRIBUTE.CRAFT_ID)
        self.player = player  # dict, data about the player who owns this Item
        # available types: center, unit, tower, building, obstacle
        self.role = item_data.get(ATTRIBUTE.ROLE)  # type of current Item
        if self.role == ROLE.CENTER:
            fight_handler.set_center(self)

        self.land_time = fight_handler.current_game_time

        self.item_type = item_data.get(ATTRIBUTE.ITEM_TYPE)
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
        self.one_action = []
        self.charging = 0

        if ATTRIBUTE.OPERATING_CODE in item_data:
            self.code = self._fight_handler.codes[str(self.player_id)][item_data[ATTRIBUTE.OPERATING_CODE]]
            self.code_opts = item_data.get(ATTRIBUTE.OPERATING_CODE_OPTS, {})
        else:
            self.code_opts = self.code = None

        self._initial = item_data
        self._env = None  # ??
        self._state = None  # dict of current FightItem state
        self._action_queue = []

        self.sub_items = {}
        self._sub_items_counter = 0

        self.extras = {}

        self._std = {
            "out": [],
            "err": []
        }
        self.messages =[]
        # every state has a key "action"
        # {'action': 'idle'}
        # {'action': 'dead'}
        self._actions_handlers = ItemActions.get_factory(self, fight_handler=fight_handler)

        self.features = gen_features(item_data.get(ATTRIBUTE.MODULES, []))
        self._used_features = {}
        map_features(self.features, 'apply', self)

    def add_one_action(self, name, data):
        self.one_action.append({
                'name': name,
                'data': data
            })

    def pop_first_one_action(self):
        try:
            return self.one_action.pop(0)
        except IndexError:
            return None

    def run_all_one_actions(self):
        while True:
            info = self.pop_first_one_action()
            if info is None:
                break
            self._actions_handlers.parse_one_action_data(info['name'], info['data'])

    def has_feature(self, name):
        return has_feature(self.features, name)

    def use_feature(self, name):
        if name not in self._used_features:
            self._used_features[name] = 0

        self._used_features[name] += 1

    def used_feature(self, name):
        return name in self._used_features

    def adj_item_data(self, item_data):
        item_data.update(building_display_stats(item_data[ATTRIBUTE.ITEM_TYPE], item_data[ATTRIBUTE.LEVEL]))

        size = item_data.get(ATTRIBUTE.SIZE, 0)
        # [SPIKE] We use center coordinates
        coordinates = [
            round(item_data[ATTRIBUTE.TILE_POSITION][0] + size / 2, 6),
            round(item_data[ATTRIBUTE.TILE_POSITION][1] + size / 2, 6)]
        # [SPIKE] We use center coordinates
        cut_size = (size if (item_data[ATTRIBUTE.ROLE] == ROLE.OBSTACLE
                             and item_data[ATTRIBUTE.ITEM_TYPE] == 'rock')
                    else max(size - CUT_FROM_BUILDING, 0))
        item_data[ATTRIBUTE.BASE_SIZE] = size
        item_data[ATTRIBUTE.SIZE] = cut_size
        item_data[ATTRIBUTE.COORDINATES] = coordinates
        
        return item_data


    @property
    def is_hidden(self):
        return False
    
    def add_sub_item(self, sub_item):
        next_id = self.generate_id()
        sub_item.set_id(next_id)
        self.sub_items[next_id] = sub_item

    def remove_sub_item(self, sub_item):
        del self.sub_items[sub_item.id]

    def get_sub_items(self):
        return self.sub_items.values()

    def add_extras(self, extra):
        self.extras[extra.type] = extra

    def remove_extras(self, extra):
        del self.extras[extra.type]

    def get_extras(self):
        return self.extras.values()

    def output_sub_items(self):
        return list(map(lambda a: a.output(), self.get_sub_items()))

    @property
    def is_immortal(self):
        return (self.role == ROLE.UNIT and
                self._fight_handler.current_game_time - self.land_time < IMMORTAL_TIME)

    @property
    def total_damage(self):
        return reduce(
            lambda total, item: (100 + item.extra_damage) * total / 100,
            self.get_extras(), self.damage_per_shot);

    def get_shoted(self, damage):
        if self.is_dead:
            return []

        if not self.is_immortal:
            self.hit_points -= damage

        if self.hit_points <= 0:
            self._dead()

        return [self.id]

    def restore_health(self, power):
        self.hit_points += power
        if self.hit_points > self.start_hit_points:
            self.hit_points = self.start_hit_points

    def _dead(self):
        self.set_state_dead()
        self._fight_handler.unsubscribe(self)
        if self.role == ROLE.BUILDING:
            self._fight_handler.demage_center(self)
        # if self._env:
        #     self._env.stop()

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
    def player_id(self):
        return self.player["id"]
    

    @property
    def info(self):
        return {
            ATTRIBUTE.ID: self.id,
            ATTRIBUTE.CRAFT_ID: self.craft_id,
            ATTRIBUTE.PLAYER_ID: self.player["id"],
            ATTRIBUTE.ROLE: self.role,
            ATTRIBUTE.ITEM_TYPE: self.item_type,
            ATTRIBUTE.HIT_POINTS: self.hit_points,
            ATTRIBUTE.SIZE: self.size,
            ATTRIBUTE.SPEED: self.speed,
            ATTRIBUTE.COORDINATES: self.coordinates,
            ATTRIBUTE.RATE_OF_FIRE: self.rate_of_fire,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.AREA_DAMAGE_PER_SHOT: self.area_damage_per_shot,
            ATTRIBUTE.AREA_DAMAGE_RADIUS: self.area_damage_radius,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.LEVEL: self.level,
            # TODO State should be reworked
            ATTRIBUTE.IS_DEAD: self.is_dead,
            ATTRIBUTE.STATE: self._state,
            ATTRIBUTE.SUBITEMS: self.info_subitems,
            ATTRIBUTE.EXTRAS: self.info_extras,
        }

    @property
    def info_subitems(self):
        return list(map(lambda a: a.output(), self.get_sub_items()))

    @property
    def info_extras(self):
        return list(map(lambda a: a.output(), self.get_extras()))
    
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
            'command': self.method_command
        }

    def get_percentage_hit_points(self):
        if not self.start_hit_points:
            return 100
        return max(0, round(100 * self.hit_points / self.start_hit_points))

    def get_action_status(self):
        return self._state["action"]

    def set_state_idle(self):
        self._state = {'action': 'idle'}

    def set_state_dead(self):
        if self.size:
            self._fight_handler.clear_from_map(self)
        self._state = {'action': 'dead'}

    def set_coordinates(self, coordinates):
        self.coordinates = coordinates

    @property
    def is_executable(self):
        if self.role == ROLE.UNIT:
            return False
        elif self.code is not None:
            return True
        return False

    @gen.coroutine
    def start(self):
        if not self.is_executable:
            return
        controller = self._fight_handler._referee.environments_controller
        self._env = yield controller.get_environment(self.player[PLAYER.ENV_NAME],
                                                     on_stdout=self.stdout,
                                                     on_stderr=self.stderr)
        self._env.ENV_CONFIG = {
            'uid_user': 'player' + str(self.player_id),
            'extra_modules': FOLDER_CODES + 'player' + str(self.player_id) + '/',
            'code_opts': self.code_opts
        }
        env_data = self._fight_handler.get_env_data()
        my_data = self._fight_handler.get_my_data(self.id)
        result = yield self._env.run_code(self.code, env_data, my_data)
        while True:
            if result is not None:
                status = result.pop('status')
                if status and status != STATUS.SUCCESS:
                    pass  # TODO:
                try:
                    self.handle_result(result)
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)
            result = yield self._env.read_message()

    def stdout(self, connection_id, out):
        self._std[STD.OUT].append(out)

    def stderr(self, connection_id, err):
        self._std[STD.ERR].append(err)

    def show_error(self, error_msg):
        self.stderr(None, error_msg)

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

    def method_set_action(self, action, data, from_self=True):
        try:
            self.action = self._actions_handlers.parse_action_data(action, data)
        except ActionValidateError as e:
            self.show_error(str(e))
            if from_self:
                self._env.bad_action(str(e))
            self.set_state_idle()
        except ActionSkip:
            if from_self:
                self._env.confirm()
        else:
            if from_self:
                self._env.confirm()

    def method_command(self, action, data, from_self=True):
        try:
            self._actions_handlers.parse_command_data(action, data)
        except ActionValidateError as e:
            self.show_error(str(e))
            if from_self:
                self._env.bad_action(str(e))
        else:
            if from_self:
                self._env.confirm()

    def subscribe_validation_time(self, data):
        if self.level < 2:
            raise ActionValidateError("Unit level should be at least 2 to use time commands")

    def subscribe_validation_message(self, data):
        if self.level < 4:
            raise ActionValidateError("Unit level should be at least 4 to use message commands")

    def method_subscribe(self, event, lookup_key, data):
        if hasattr(self, 'subscribe_validation_'+event):
            try:
                getattr(self, 'subscribe_validation_' + event)(data)
            except ActionValidateError as e:
                self.show_error(str(e))
                self._env.bad_action(e)
                return

        result = self._fight_handler.subscribe(event, self.id, lookup_key, data)
        if not result:
            self._env.bad_action("Subscribing Error")
            return
        self._env.confirm()

        if hasattr(self, 'subscribe_check_' + event):
            getattr(self, 'subscribe_check_' + event)(data)

    def do_frame_action(self):
        try:
            self._state = self._actions_handlers.do_action(self.action)
        except ActionValidateError as e:
            print('!!!ActionValidateError!!!', self.id, e, self.action )
            print(self.info)
            self.set_state_idle()

    def send_event(self, lookup_key, data):
        self._fight_handler.inc_total_events_sent()
        self._env.send_event(lookup_key, data)

class FlagItem(FightItem):
    is_flagman = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.charge = self._initial[ATTRIBUTE.CHARGE_SIZE]
        self.operations = self._initial[ATTRIBUTE.OPERATIONS]

    @property
    def info(self):
        return {
            ATTRIBUTE.ID: self.id,
            ATTRIBUTE.CHARGE: self.charge,
            ATTRIBUTE.LEVEL: self.level,
            ATTRIBUTE.ROLE: self.role,
            ATTRIBUTE.IS_DEAD: False,
            ATTRIBUTE.SIZE: 0,
            ATTRIBUTE.PLAYER_ID: self.player_id,
            ATTRIBUTE.SUBITEMS: self.info_subitems,
            ATTRIBUTE.ITEM_TYPE: self.item_type,
        }

    def adj_item_data(self, data):
        data.update(building_display_stats(data[ATTRIBUTE.ITEM_TYPE], data[ATTRIBUTE.LEVEL]))
        for action, level in data[ATTRIBUTE.OPERATIONS].items():
            data[ATTRIBUTE.OPERATIONS][action] = operation_stats(action, level)
        if data[ATTRIBUTE.IS_FLYING]:
            data[ATTRIBUTE.ROLE] = ROLE.FLAGMAN
        return data

    def get_operation(self, operation):
        return self.operations[operation]

    def use_operation(self, operation_name):
        operation = self.get_operation(operation_name)
        if not operation or self.charge < operation['charge']:
            return False
        self.charge -= operation['charge']
        return True




class CraftItem(FightItem):
    is_craft = True
    landing_duration = 3
    last_landing = -landing_duration
    def __init__(self, item_data, player, fight_handler):
        super().__init__(item_data, player, fight_handler)
        self.craft_id = item_data.get(ATTRIBUTE.CRAFT_ID)
        self.unit_type = item_data.get(ATTRIBUTE.UNIT_TYPE)
        self.coordinates = item_data.get(ATTRIBUTE.COORDINATES)
        self.tile_position = item_data.get(ATTRIBUTE.COORDINATES)[:]
        self.level = item_data.get(ATTRIBUTE.LEVEL)
        self.item_type = item_data.get(ATTRIBUTE.ITEM_TYPE)
        self.initial_amount_units_in = self.amount_units_in = item_data.get(ATTRIBUTE.UNIT_QUANTITY)
        craft_coor = item_data[ATTRIBUTE.COORDINATES]
        self.units_position = [[craft_coor[0] + shift[0], craft_coor[1] + shift[1]]
                               for shift in precalculated.LAND_POSITION_SHIFTS[:self.amount_units_in]]

        # im not sute it is nessesary, but still...
        self.item_data = item_data
        self.player = player
        self.role = ROLE.CRAFT

        self.children = set() #units

    def is_empty(self):
        return not self.amount_units_in

    def generate_craft_place(self, craft_data):
        return self._fight_handler.generate_craft_place()

    def adj_item_data(self, craft_data):
        craft_coor = self.generate_craft_place(craft_data)
        if not craft_coor[1]:
            return
        craft_data[ATTRIBUTE.HIT_POINTS] = 10*10
        craft_data[ATTRIBUTE.COORDINATES] = craft_coor
        in_unit_description = craft_data[ATTRIBUTE.IN_UNIT_DESCRIPTION]
        craft_data[ATTRIBUTE.UNIT_TYPE] = in_unit_description[ATTRIBUTE.ITEM_TYPE]
        craft_data[ATTRIBUTE.ROLE] = 'craft'
        return craft_data


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
            ATTRIBUTE.UNITS_IN: self.amount_units_in,
            ATTRIBUTE.CRAFT_ID: self.craft_id,
            ATTRIBUTE.IS_DEAD: False,
            ATTRIBUTE.SIZE: 0,
        }

    def land_unit(self):
        if not self.amount_units_in:
            return False
        current_frame = self._fight_handler.current_frame
        if current_frame - self.landing_duration >= self.last_landing:
            self._fight_handler.add_unit_from_craft(self)
            self.last_landing = current_frame
        return True

    def add_child_id(self, id):
        self.children.add(id)

class DefPlatformItem(CraftItem):
    def generate_craft_place(self, craft_data):
        return craft_data[ATTRIBUTE.TILE_POSITION]



class UnitItem(FightItem):
    parent_id = None

    def set_parent_id(self, id):
        self.parent_id = id

        map_features(self.parent_item.features, 'apply', self)

    def has_feature(self, name):
        return has_feature(self.parent_item.features, name)

    @property
    def parent_item(self):
        return self._fight_handler.fighters[self.parent_id]
    

    def adj_item_data(self, item_data):
        item_data.update(unit_display_stats(item_data[ATTRIBUTE.ITEM_TYPE], item_data[ATTRIBUTE.LEVEL]))
        return item_data


class MineItem(FightItem):
    is_activated = False
    is_executable = False
    timer = 0.3

    @property
    def is_hidden(self):
        return self.action.get('name') == 'waiting'

    def detonate(self):
        self.action = {
            'name': 'detonate',
            'data': {}
        }

    def adj_item_data(self, item_data):
        item_data.update(unit_display_stats(item_data[ATTRIBUTE.ITEM_TYPE], item_data[ATTRIBUTE.LEVEL]))
        item_data[ATTRIBUTE.ROLE] = ROLE.MINE
        item_data[ACTION.REQUEST_NAME] = {
            'name': 'waiting',
            'data': {}
        }
        item_data[ATTRIBUTE.COORDINATES] = item_data[ATTRIBUTE.TILE_POSITION]

        return item_data

    def detonator_timer(self):
        self.timer -= self._fight_handler.GAME_FRAME_TIME
        if self.timer <= 0:
            self.explode()

    def explode():
        self.is_dead = True
        for item in self._fight_handler.fighters.values():
            if item.is_dead:
                continue

            if item.player_id == self.item.player_id:
                continue

            if item.role != ROLE.UNIT:
                continue

            distance = euclidean_distance(item.coordinates, self.coordinates)
            if distance > self.firing_range:
                continue

            damage = (self.firing_range - distance) * self.damage_per_shot / self.firing_range
            item.get_shoted(damage)



