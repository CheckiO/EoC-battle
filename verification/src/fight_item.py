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
from tools import ROLE, ATTRIBUTE, ACTION, DEF_TYPE, ATTACK_TYPE, STD, PLAYER, STATUS, OUTPUT
from tools.generators import landing_position_shifts
from tools.terms import FEATURE
from actions.exceptions import ActionValidateError, ActionSkip
from modules import gen_features, map_features, has_feature

logger = logging.getLogger(__name__)


class Item(object):
    ROLE_TYPE = None

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
        item_data = self.adj_item_data(item_data)
        self.item_data = item_data
        self.craft_id = item_data.get(ATTRIBUTE.CRAFT_ID)
        self.player = player  # dict, data about the player who owns this Item
        # available types: center, unit, tower, building, obstacle
        self.role = item_data.get(ATTRIBUTE.ROLE)  # type of current Item
        if self.role == ROLE.CENTER:
            fight_handler.set_center(self)

        # TODO: Why do we need tile position and coordinates

        self.land_time = fight_handler.current_game_time

        self.item_type = item_data.get(ATTRIBUTE.ITEM_TYPE)
        self.level = item_data.get(ATTRIBUTE.LEVEL, 1)
        self.tile_position = item_data.get(ATTRIBUTE.TILE_POSITION)
        self.item_status = item_data.get(ATTRIBUTE.ITEM_STATUS, 'idle')

        self.start_hit_points = item_data.get(ATTRIBUTE.HIT_POINTS)
        self.hit_points = item_data.get(ATTRIBUTE.HIT_POINTS)
        self.size = item_data.get(ATTRIBUTE.SIZE, 0)
        self.base_size = item_data.get(ATTRIBUTE.BASE_SIZE, 0)

        self.coordinates = item_data.get(ATTRIBUTE.COORDINATES)  # list of two

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

        self.effects = {}

        self._std = {
            "out": [],
            "err": []
        }
        self.has_error = False
        # every state has a key "action"
        # {'action': 'idle'}
        # {'action': 'dead'}

        self.update_additional_attributes()

        self._actions_handlers = ItemActions.get_factory(self, fight_handler=fight_handler)

        self.features = gen_features(item_data.get(ATTRIBUTE.MODULES, []))
        map_features(self.features, 'apply', self)

        self._used_features = {}

        self.reset_fflags()
        self.reset_std()

    def update_additional_attributes(self):
        pass

    def reset_fflags(self):
        self._frame_flags = {}

    def set_fflag(self, name, value=True):
        self._frame_flags[name] = value

    def fflag(self, name):
        return self._frame_flags.get(name)

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
        cut_size = (size if (item_data[ATTRIBUTE.ROLE] == ROLE.OBSTACLE)
                    else max(size - CUT_FROM_BUILDING, 0))
        item_data[ATTRIBUTE.BASE_SIZE] = size
        item_data[ATTRIBUTE.SIZE] = cut_size
        item_data[ATTRIBUTE.COORDINATES] = coordinates
        
        return item_data

    def add_sub_item(self, sub_item):
        next_id = self.generate_id()
        sub_item.set_id(next_id)
        self.sub_items[next_id] = sub_item

    def remove_sub_item(self, sub_item):
        del self.sub_items[sub_item.id]

    def get_sub_items(self):
        return self.sub_items.values()

    def add_effect(self, effect):
        self.effects[effect.type] = effect

    def remove_effect(self, effect):
        del self.effects[effect.type]

    def get_effects(self):
        return self.effects.values()

    def output_sub_items(self):
        return list(map(lambda a: a.output(), self.get_sub_items()))

    @property
    def is_immortal(self):
        return (self.role == ROLE.UNIT and
                self._fight_handler.current_game_time - self.land_time < IMMORTAL_TIME)

    def shot_items(self, damage):
        items = {}

        heavy_protection_feature_units = {}
        for item in self._fight_handler.get_active_battle_fighters():
            if item.player_id != self.player_id or not item.coordinates:
                continue
            if not item.used_feature(FEATURE.HEAVY_PROTECT):
                continue

            distance_to_item = euclidean_distance(item.coordinates, self.coordinates)
            # TODO: how to make radius
            if distance_to_item > 2:
                continue
            heavy_protection_feature_units[item] = distance_to_item

        if heavy_protection_feature_units:
            closest_heavy_protection_feature_units = [k for k in sorted(
                heavy_protection_feature_units, key=heavy_protection_feature_units.get)]
            items[closest_heavy_protection_feature_units[0]] = damage
            return items

        if self.has_feature(FEATURE.GROUP_PROTECT):
            group_protection_feauture_units = []
            for item in self._fight_handler.get_active_battle_fighters():
                if item.player_id != self.player_id or not item.coordinates:
                    continue
                if not item.has_feature(FEATURE.GROUP_PROTECT):
                    continue
                distance_to_item = euclidean_distance(item.coordinates, self.coordinates)
                # TODO: how to make radius
                if distance_to_item > 2:
                    continue
                group_protection_feauture_units.append(item)
            count = len(group_protection_feauture_units)
            # TODO: move to table or something
            if count > 4:
                group_protection_average_item_damage = damage / count
                for item in group_protection_feauture_units:
                    items[item] = group_protection_average_item_damage
                return items

        items[self] = damage
        return items

    def get_shot(self, damage, effects=None):
        if self.is_gone:
            return []

        shot_items = self.shot_items(damage)

        for item, item_damage in shot_items.items():
            if item == self:
                item.get_damaged(item_damage, effects)
            else:
                item.get_damaged(item_damage)
        # TODO: is this still relevant after changes?

        return [self.id]

    def get_damaged(self, damage, effects=None):
        if self.is_immortal:
            return

        self.hit_points -= damage
        if self.hit_points <= 0:
            self._dead()
            return
        if effects is not None:
            for effect in effects:
                self.add_effect(effect)

    def restore_health(self, power):
        self.hit_points += power
        if self.hit_points > self.start_hit_points:
            self.hit_points = self.start_hit_points

    def _dead(self):
        self.set_state_dead()
        self._fight_handler.unsubscribe(self)
        if self.role == ROLE.BUILDING:
            self._fight_handler.damage_center(self)
        # if self._env:
        #     self._env.stop()

    @property
    def is_gone(self):
        return self.is_dead or self.is_departed

    @property
    def is_dead(self):
        if not self.hit_points:
            return False
        return self.hit_points <= 0

    @property
    def is_departed(self):
        if not self._state:
            return False
        return self._state.get('name') == 'departed'

    @property
    def is_hidden(self):
        return False

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
            ATTRIBUTE.COORDINATES: self.coordinates,
            ATTRIBUTE.LEVEL: self.level,
            # TODO State should be reworked
            ATTRIBUTE.IS_DEAD: self.is_dead,
            ATTRIBUTE.IS_DEPARTED: self.is_departed,
            ATTRIBUTE.STATE: self._state,
            ATTRIBUTE.SUBITEMS: self.info_subitems,
            ATTRIBUTE.EFFECTS: self.info_effects,
            ATTRIBUTE.IS_IMMORTAL: self.is_immortal,
            ATTRIBUTE.IS_HIDDEN: self.is_hidden,
        }

    @property
    def info_subitems(self):
        return list(map(lambda a: a.output(), self.get_sub_items()))

    @property
    def info_effects(self):
        return list(map(lambda a: a.output(), self.get_effects()))

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
        return self._state and self._state["name"] or 'idle'

    def set_state_departed(self):
        self._state = {'name': 'departed'}

    def set_state_idle(self):
        self._state = {'name': 'idle'}

    def set_state_dead(self):
        if self.size:
            self._fight_handler.clear_from_map(self)
        self._state = {'name': 'dead'}

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

    def reset_std(self):
        self._std = []

    def stdout(self, connection_id, out):
        self._std.append([STD.OUT, out])

    def stderr(self, connection_id, err):
        self.has_error = True
        self._std.append([STD.ERR, err])

    def show_error(self, error_msg):
        self.stderr(None, error_msg)

    def has_std(self):
        return bool(self._std)

    def get_std(self):
        return self._std

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
            #print('!!!ActionValidateError!!!', self.id, e, self.action )
            #print(self.info)
            self.set_state_idle()

    def send_event(self, lookup_key, data):
        self._env.send_event(lookup_key, data)


class SentryGunTowerItem(FightItem):
    ROLE_TYPE = DEF_TYPE.SENTRY

    def update_additional_attributes(self):
        self.charging_time = self.item_data[ATTRIBUTE.CHARGING_TIME]
        self.damage_per_shot = self.item_data[ATTRIBUTE.DAMAGE_PER_SHOT]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.firing_range_always_hit = self.item_data[ATTRIBUTE.FIRING_RANGE_ALWAYS_HIT]
        self.start_chance = self.item_data[ATTRIBUTE.START_CHANCE]

    @property
    def info(self):
        info = super(SentryGunTowerItem, self).info
        info.update({
            ATTRIBUTE.CHARGING_TIME: self.charging_time,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.FIRING_RANGE_ALWAYS_HIT: self.firing_range_always_hit,
            ATTRIBUTE.START_CHANCE: self.start_chance,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_shot


class MachineGunTowerItem(FightItem):
    ROLE_TYPE = DEF_TYPE.MACHINE

    # TODO: balance update
    def update_additional_attributes(self):
        self.field_of_view = self.item_data[ATTRIBUTE.FIELD_OF_VIEW]
        self.rate_of_turn = self.item_data[ATTRIBUTE.RATE_OF_TURN]
        self.damage_per_second = self.item_data[ATTRIBUTE.DAMAGE_PER_SECOND]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.firing_time_limit = self.item_data[ATTRIBUTE.FIRING_TIME_LIMIT]
        self.full_cooldown_time = self.item_data[ATTRIBUTE.FULL_COOLDOWN_TIME]
        self.min_percentage_after_overheat = self.item_data[ATTRIBUTE.MIN_PERCENTAGE_AFTER_OVERHEAT]

        self.angle = 0
        self.firing_time = 0
        self.overheated = False

    @property
    def info(self):
        info = super(MachineGunTowerItem, self).info
        info.update({
            ATTRIBUTE.FIELD_OF_VIEW: self.field_of_view,
            ATTRIBUTE.RATE_OF_TURN: self.rate_of_turn,
            ATTRIBUTE.DAMAGE_PER_SECOND: self.damage_per_second,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.FIRING_TIME_LIMIT: self.firing_time_limit,
            ATTRIBUTE.FULL_COOLDOWN_TIME: self.full_cooldown_time,
            ATTRIBUTE.MIN_PERCENTAGE_AFTER_OVERHEAT: self.min_percentage_after_overheat,
            ATTRIBUTE.ANGLE: self.angle,
            ATTRIBUTE.FIRING_TIME: self.firing_time,
            ATTRIBUTE.OVERHEATED: self.overheated,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_second * self._fight_handler.GAME_FRAME_TIME


class RocketGunTowerItem(FightItem):
    ROLE_TYPE = DEF_TYPE.ROCKET_GUN

    # TODO: balance update
    def update_additional_attributes(self):
        self.charging_time = self.item_data[ATTRIBUTE.CHARGING_TIME]
        self.damage_per_shot = self.item_data[ATTRIBUTE.DAMAGE_PER_SHOT]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.rocket_speed = self.item_data[ATTRIBUTE.ROCKET_SPEED]
        self.rocket_explosion_radius = self.item_data[ATTRIBUTE.ROCKET_EXPLOSION_RADIUS]

    @property
    def info(self):
        info = super(RocketGunTowerItem, self).info
        info.update({
            ATTRIBUTE.CHARGING_TIME: self.charging_time,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.ROCKET_SPEED: self.rocket_speed,
            ATTRIBUTE.ROCKET_EXPLOSION_RADIUS: self.rocket_explosion_radius,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_shot


class FlagItem(FightItem):
    is_flagman = True
    is_immortal = True

    def update_additional_attributes(self):
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
            ATTRIBUTE.IS_IMMORTAL: self.is_immortal,
        }

    def adj_item_data(self, data):
        data.update(building_display_stats(data[ATTRIBUTE.ITEM_TYPE], data[ATTRIBUTE.LEVEL]))
        for action, level in data[ATTRIBUTE.OPERATIONS].items():
            data[ATTRIBUTE.OPERATIONS][action] = operation_stats(action, level)

        # from pprint import pprint
        # print('OPERATIONS')
        # pprint(data[ATTRIBUTE.OPERATIONS])

        if data[ATTRIBUTE.IS_FLYING]:
            data[ATTRIBUTE.ROLE] = ROLE.FLAGMAN
            data[ATTRIBUTE.TILE_POSITION] = data[ATTRIBUTE.COORDINATES] = [40, 20] # if flagman is flying. It should be right in the middle

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
    ROLE_TYPE = ROLE.CRAFT

    is_craft = True
    landing_duration = 3
    last_landing = -landing_duration
    is_immortal = True

    def update_additional_attributes(self):
        self.craft_id = self.item_data.get(ATTRIBUTE.CRAFT_ID)
        self.unit_type = self.item_data.get(ATTRIBUTE.UNIT_TYPE)
        self.coordinates = self.item_data.get(ATTRIBUTE.COORDINATES)
        #self.tile_position = self.item_data.get(ATTRIBUTE.COORDINATES)[:]
        self.level = self.item_data.get(ATTRIBUTE.LEVEL)
        self.item_type = self.item_data.get(ATTRIBUTE.ITEM_TYPE)
        self.initial_amount_units_in = self.amount_units_in = self.item_data.get(ATTRIBUTE.UNIT_QUANTITY)
        self.landing_shift = 2

        # im not sute it is nessesary, but still...
        self.role = ROLE.CRAFT
        self.children = set() #units

    def is_empty(self):
        return not self.amount_units_in

    def generate_craft_place(self):
        return self._fight_handler.generate_craft_place()

    def find_craft_place(self, coordinates):
        return self._fight_handler.find_craft_place(coordinates)

    def adj_item_data(self, craft_data):
        craft_data[ATTRIBUTE.HIT_POINTS] = 10*10
        craft_data[ATTRIBUTE.UNIT_TYPE] = craft_data[ATTRIBUTE.IN_UNIT_DESCRIPTION][ATTRIBUTE.ITEM_TYPE]
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
            ATTRIBUTE.IS_IMMORTAL: self.is_immortal,
        }

    def land_unit(self, coordinates=None):
        if not self.amount_units_in:
            return False

        if self.coordinates is None:
            if coordinates is None:
                self.coordinates = self.generate_craft_place()
            else:
                self.coordinates = self.find_craft_place(coordinates)

        shifts = landing_position_shifts(self.landing_shift)[:self.amount_units_in]
        self.units_position = [[self.coordinates[0] + shift[0], self.coordinates[1] + shift[1]] for shift in shifts]

        current_frame = self._fight_handler.current_frame
        if current_frame - self.landing_duration >= self.last_landing:
            self._fight_handler.add_unit_from_craft(self)
            self.last_landing = current_frame
        return True

    def add_child_id(self, id):
        self.children.add(id)


# TODO: is this gonna be changed?
class DefPlatformItem(CraftItem):
    ROLE_TYPE = ROLE.DEF_PLATFORM

    def generate_craft_place(self, craft_data):
        return craft_data[ATTRIBUTE.TILE_POSITION]


class UnitItem(FightItem):
    parent_id = None

    def update_additional_attributes(self):
        self.speed = self.item_data[ATTRIBUTE.SPEED]
        self.original_speed = self.item_data[ATTRIBUTE.SPEED]

        self.departing_time = 0


    @property
    def info(self):
        info = super(UnitItem, self).info
        info.update({
            OUTPUT.DEPARTING_TIME: self.departing_time,
            ATTRIBUTE.SPEED: self.speed,
        })
        return info

    def set_parent_id(self, id):
        self.parent_id = id
        self.set_parent_features()

    # TODO: features only for unit
    def set_parent_features(self):
        for feature in self.parent_item.features:
            self.features.append(feature)
        map_features(self.features, 'apply', self)
        #map_features(self.parent_item.features, 'apply', self)

    def has_feature(self, name):
        return has_feature(self.parent_item.features, name)

    @property
    def parent_item(self):
        return self._fight_handler.fighters[self.parent_id]

    def adj_item_data(self, item_data):
        item_data.update(unit_display_stats(item_data[ATTRIBUTE.ITEM_TYPE], item_data[ATTRIBUTE.LEVEL]))
        return item_data


class InfantryBotUnit(UnitItem):
    ROLE_TYPE = ATTACK_TYPE.INFANTRY

    def update_additional_attributes(self):
        super().update_additional_attributes()
        self.damage_per_shot = self.item_data[ATTRIBUTE.DAMAGE_PER_SHOT]
        self.charging_time = self.item_data[ATTRIBUTE.CHARGING_TIME]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]

    @property
    def info(self):
        info = super(InfantryBotUnit, self).info
        info.update({

            ATTRIBUTE.CHARGING_TIME: self.charging_time,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_shot


class HeavyBotUnit(UnitItem):
    ROLE_TYPE = ATTACK_TYPE.HEAVY

    def update_additional_attributes(self):
        super().update_additional_attributes()
        self.rate_of_turn = self.item_data[ATTRIBUTE.RATE_OF_TURN]
        self.damage_per_second = self.item_data[ATTRIBUTE.DAMAGE_PER_SECOND]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.firing_time_limit = self.item_data[ATTRIBUTE.FIRING_TIME_LIMIT]
        self.full_cooldown_time = self.item_data[ATTRIBUTE.FULL_COOLDOWN_TIME]
        self.min_percentage_after_overheat = self.item_data[ATTRIBUTE.MIN_PERCENTAGE_AFTER_OVERHEAT]

        self.angle = 0
        self.firing_time = 0
        self.overheated = False

    @property
    def info(self):
        info = super(HeavyBotUnit, self).info
        info.update({
            ATTRIBUTE.RATE_OF_TURN: self.rate_of_turn,
            ATTRIBUTE.DAMAGE_PER_SECOND: self.damage_per_second,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.FIRING_TIME_LIMIT: self.firing_time_limit,
            ATTRIBUTE.FULL_COOLDOWN_TIME: self.full_cooldown_time,
            ATTRIBUTE.MIN_PERCENTAGE_AFTER_OVERHEAT: self.min_percentage_after_overheat,
            ATTRIBUTE.ANGLE: self.angle,
            ATTRIBUTE.FIRING_TIME: self.firing_time,
            ATTRIBUTE.OVERHEATED: self.overheated,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_second * self._fight_handler.GAME_FRAME_TIME


class RocketBotUnit(UnitItem):
    ROLE_TYPE = ATTACK_TYPE.ROCKET_BOT

    def update_additional_attributes(self):
        super().update_additional_attributes()
        self.charging_time = self.item_data[ATTRIBUTE.CHARGING_TIME]
        self.damage_per_shot = self.item_data[ATTRIBUTE.DAMAGE_PER_SHOT]
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.rocket_speed = self.item_data[ATTRIBUTE.ROCKET_SPEED]
        self.rocket_explosion_radius = 0

    @property
    def info(self):
        info = super(RocketBotUnit, self).info
        info.update({
            ATTRIBUTE.CHARGING_TIME: self.charging_time,
            ATTRIBUTE.DAMAGE_PER_SHOT: self.damage_per_shot,
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.ROCKET_SPEED: self.rocket_speed,
            ATTRIBUTE.ROCKET_EXPLOSION_RADIUS: self.rocket_explosion_radius,
        })
        return info

    @property
    def total_damage(self):
        return self.damage_per_shot


class MineItem(FightItem):
    ROLE_TYPE = ROLE.MINE

    is_executable = False

    def update_additional_attributes(self):
        self.firing_range = self.item_data[ATTRIBUTE.FIRING_RANGE]
        self.damage_per_shot = self.item_data[ATTRIBUTE.DAMAGE_PER_SHOT]
        self.explosion_timer = 0.3

    @property
    def info(self):
        info = super(MineItem, self).info
        info.update({
            ATTRIBUTE.FIRING_RANGE: self.firing_range,
            ATTRIBUTE.DAMAGE_PER_SHOT:self.damage_per_shot,
            ATTRIBUTE.EXPLOSION_TIMER: self.explosion_timer,
        })
        return info

    @property
    def is_hidden(self):
        return self.action.get('name') == 'wait'

    @property
    def is_dead(self):
        return self._state.get('name') == 'dead'

    def detonate(self):
        self.action = {
            'name': 'detonate',
            'data': {}
        }

    def adj_item_data(self, item_data):
        item_data.update(unit_display_stats(item_data[ATTRIBUTE.ITEM_TYPE], item_data[ATTRIBUTE.LEVEL]))
        item_data[ATTRIBUTE.ROLE] = ROLE.MINE
        item_data[ACTION.REQUEST_NAME] = {
            'name': 'wait',
            'data': {}
        }
        item_data[ATTRIBUTE.COORDINATES] = item_data[ATTRIBUTE.TILE_POSITION]
        return item_data

    def detonator_timer(self):
        self.explosion_timer -= self._fight_handler.GAME_FRAME_TIME
        if self.explosion_timer <= 0:
            self.explosion_timer = 0
            self.explode()

    def explode(self):
        for item in self._fight_handler.fighters.values():
            if item.is_gone:
                continue
            if item.player_id == self.player_id:
                continue
            if item.role != ROLE.UNIT:
                continue

            distance = euclidean_distance(item.coordinates, self.coordinates)
            if distance > self.firing_range:
                continue
            damage = (self.firing_range - distance) * self.damage_per_shot / self.firing_range
            item.get_shot(damage)
        self._dead()
