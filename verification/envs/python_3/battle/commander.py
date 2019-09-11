from battle import ROLE, PARTY
from battle.tools import euclidean_distance
import battle.map_filters as MF
import warnings

ERR_ID_TYPE = "{name} ID must be an integer"
ERR_ARRAY_TYPE = "{name} must be a list/tuple"
ERR_COORDINATES_TYPE = "{name} must be a list/tuple with two numbers."
ERR_CALLABLE_TYPE = "{name} must be callable (function)"
ERR_STR_TYPE = "{name} must be a string"
ERR_NUMBER_TYPE = "{name} must be a number."
ERR_NUMBER_POSITIVE_VALUE = "{name} must be a positive."
ERR_NUMBER_PERCENTAGE_VALUE = "{name} must be a percentage."
ERR_ARRAY_VALUE = "{name} must contains only correct values"


def check_coordinates(coordinates, name):
    if not (isinstance(coordinates, (list, tuple)) and
            len(coordinates) == 2 and
            all(isinstance(n, (float, int)) for n in coordinates)):
        raise TypeError(ERR_COORDINATES_TYPE.format(name=name))


def check_angle(angle, name):
    if not isinstance(angle, (int, float)):
        raise TypeError(ERR_COORDINATES_TYPE.format(name=name))

    if angle < 0 or angle > 360:
        raise ValueError(ERR_NUMBER_POSITIVE_VALUE.format(name=name))


def check_item_id(item_id):
    if not isinstance(item_id, int):
        raise TypeError(ERR_ID_TYPE.format(name="Item"))


def check_array(array, correct_values, name):
    if not isinstance(array, (list, tuple)):
        raise TypeError(ERR_ARRAY_TYPE.format(name=name))
    if not all(el in correct_values for el in array):
        raise ValueError(ERR_ARRAY_VALUE.format(name=name))


def check_radius(number):
    if not isinstance(number, (int, float)):
        raise TypeError(ERR_NUMBER_TYPE.format(name="Radius"))
    if number <= 0:
        raise ValueError(ERR_NUMBER_POSITIVE_VALUE.format(name="Radius"))


def check_distance(number):
    if number is None:
        return
    if not isinstance(number, (int, float)):
        raise TypeError(ERR_NUMBER_TYPE.format(name="Distance"))
    if number <= 0:
        raise ValueError(ERR_NUMBER_POSITIVE_VALUE.format(name="Distance"))


def check_percentage(number):
    if number is None:
        return
    if not isinstance(number, (int, float)):
        raise TypeError(ERR_NUMBER_TYPE.format(name="Percentage"))
    if number < 0:
        raise ValueError(ERR_NUMBER_PERCENTAGE_VALUE.format(name="Percentage"))
    if number > 100:
        raise ValueError(ERR_NUMBER_PERCENTAGE_VALUE.format(name="Percentage"))


def check_callable(func, name):
    if not callable(func):
        raise TypeError(ERR_CALLABLE_TYPE.format(name=name))


def check_str_type(data, name):
    if not isinstance(data, str):
        raise TypeError(ERR_STR_TYPE.format(name=name))


class Client(object):
    CLIENT = None
    OPTS = {}

    def __init__(self):
        assert Client.CLIENT

    @property
    def my_data(self):
        return Client.CLIENT._my_data

    @property
    def env_data(self):
        return Client.CLIENT._env_data

    @property
    def env_map(self):
        return self.env_data['map']

    @property
    def my_info(self):
        return self.env_map[str(self.my_data['id'])]

    @classmethod
    def set_client(cls, client):
        Client.CLIENT = client

    @classmethod
    def set_opts(cls, opts):
        Client.OPTS = opts

    def get_opt(self, name, default=None):
        return self.OPTS.get(name, default)

    def ids_my_craft(self):
        my_info = self.my_info
        ret = []
        for uid, unit in self.env_map.items():
            if uid == str(my_info['id']):
                continue
            if my_info['craft_id'] == unit['craft_id']:
                ret.append(uid)
        return ret

    def ids_my_team(self):
        my_info = self.my_info
        ret = []
        for uid, unit in self.env_map.items():
            if uid == str(my_info['id']):
                continue
            if my_info['player_id'] == unit['player_id']:
                ret.append(uid)
        return ret

    def ask_my_info(self):
        return self.my_info

    def ask_item_info(self, item_id):
        check_item_id(item_id)
        return self.env_map[str(item_id)]

    def env_map_filter(self, filters):
        def _filters_passed(item):
            for _filter in filters:
                if not _filter(self, item):
                    return False
            return True

        ret = []  # TODO: change to generators
        for item in self.env_map.values():
            if item['is_dead']:
                continue
            # if item['is_departed']:
            #     continue
            if 'coordinates' not in item:
                continue
            if _filters_passed(item):
                ret.append(item)
        return ret

    def ask_cur_time(self):
        return self.env_data['game']['time']

    def ask_items(self, parties=PARTY.ALL, roles=ROLE.ALL):
        #  DEPRECATED function
        check_array(parties, PARTY.ALL, "Parties")
        check_array(roles, ROLE.ALL, "Roles")
        _filters = []
        if len(set(parties)) <= 1:
            if parties[0] == PARTY.MY:
                _filters.append(MF.my)
            if parties[0] == PARTY.ENEMY:
                _filters.append(MF.enemy)

        _filters.append(MF.roles(roles))
        return self.env_map_filter(_filters)

    def ask_enemy_items(self):
        return self.ask_items(parties=(PARTY.ENEMY,))

    def ask_my_items(self):
        return self.ask_items(parties=(PARTY.MY,))

    def ask_buildings(self):
        return self.ask_items(roles=(ROLE.CENTER, ROLE.BUILDING))

    def ask_towers(self):
        return self.ask_items(roles=(ROLE.TOWER,))

    def ask_center(self):
        centers = self.ask_items(roles=(ROLE.CENTER,))
        return centers[0] if centers else None

    def ask_units(self):
        return self.ask_items(roles=(ROLE.UNIT,))

    def ask_nearest_enemy(self, roles=None):
        min_length = 1000
        nearest_enemy = None
        fighter = self.my_info
        filters = [MF.enemy]

        if roles:
            filters.append(MF.roles(roles))
        for item in self.env_map_filter(filters):
            length = euclidean_distance(item['coordinates'], fighter['coordinates'])

            if length < min_length:
                min_length = length
                nearest_enemy = item
        return self.ask_item_info(nearest_enemy['id']) if nearest_enemy else {}

    def ask_my_range_enemy_items(self):
        return self.env_map_filter([MF.enemy, MF.in_my_range])

    ask_enemy_items_in_my_firing_range = ask_my_range_enemy_items

    def do(self, action, data):
        return Client.CLIENT.set_action(action, data)

    def command(self, action, data):
        return Client.CLIENT.send_command(action, data)

    def do_attack(self, item_id):
        check_item_id(item_id)
        return self.do('attack', {'id': item_id})

    attack_item = do_attack

    def do_attack_coordinates(self, coordinates):
        check_coordinates(coordinates, "Coordinates")
        return self.do('attack_coor', {'coordinates': coordinates})

    def do_move(self, coordinates):
        check_coordinates(coordinates, "Coordinates")
        return self.do('move', {'coordinates': coordinates})

    move_to_point = do_move

    def do_moves(self, steps):
        for coordinates in steps:
            check_coordinates(coordinates, "Coordinates")
        return self.do('moves', {'steps': steps})

    # TODO: dev-118 methods only for towers?

    def do_fire(self):
        return self.do('fire', {})

    fire = do_fire

    def do_turn(self, angle):
        check_angle(angle, 'Angle')
        return self.do('turn', {'angle': angle})

    turn_to_angle = do_turn

    def do_turn_to_fire(self, item_id):
        check_item_id(item_id)
        return self.do('turn_to_fire', {'id': item_id})

    turn_to_fire = do_turn_to_fire

    def do_message(self, message, ids):
        self.do('message', {'message': message, 'ids': ids})

    def do_message_to_id(self, message, item_id):
        return self.do_message(message, [item_id])

    def do_message_to_craft(self, message):
        return self.do_message(message, self.ids_my_craft())

    def do_message_to_team(self, message):
        return self.do_message(message, self.ids_my_team())

    def when(self, event, callback, data=None, infinity=False):
        check_callable(callback, "Callback")
        check_str_type(event, "Event")
        if infinity:
            def new_call(*args, **kwargs):
                self.when(event, callback, data, infinity=True)
                callback(*args, **kwargs)
        else:
            new_call = callback
        return Client.CLIENT.subscribe(event, new_call, data)

    def unsubscribe_all(self):
        return self.when('unsubscribe_all', None)

    def when_in_area(self, center, radius, callback):
        check_coordinates(center, "Center coordinates")
        check_radius(radius)
        return self.when('im_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })

    def when_item_in_area(self, center, radius, callback):
        check_coordinates(center, "Center coordinates")
        check_radius(radius)
        return self.when('any_item_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })

    def when_im_idle(self, callback):
        return self.when('idle', callback, {
            'id': self.my_info['id']
        })

    def when_id_idle(self, item_id, callback):
        check_item_id(item_id)
        return self.when('idle', callback, {
            'id': item_id
        })

    def when_enemy_in_range(self, callback, distance=None, percentage=None):
        check_distance(distance)
        check_percentage(percentage)
        return self.when('enemy_in_my_firing_range', callback, {
            'distance': distance,
            'percentage': percentage,
        })

    def when_item_destroyed(self, item_id, callback):
        check_item_id(item_id)
        return self.when('death', callback, {'id': item_id})

    def when_time(self, secs, callback):
        return self.when('time', callback, {'time': secs})

    def when_message(self, callback, infinity=True):
        return self.when('message', callback, infinity=infinity)


class CraftClient(Client):

    def do_land_units(self):
        self.do('land_units', {})

    def when_unit_landed(self, callback):
        self.when('unit_landed', callback, {'craft_id': self.my_info['craft_id']}, infinity=True)


class FlagmanClient(Client):

    def command_rocket(self, coordinates):
        self.command('rocket', {
                'coordinates': coordinates
            })

    def command_heal(self, coordinates):
        self.command('heal', {
                'coordinates': coordinates
            })

    def command_power(self, coordinates):
        self.command('power', {
                'coordinates': coordinates
            })


class UnitClient(Client):

    def __init__(self, _id):
        self._id = _id

    @property
    def is_alive(self):
        return str(self._id) in self.env_map

    @property
    def my_data(self):
        return super().my_data['children'][str(self._id)]

    def do(self, action, data):
        if not self.is_alive:
            print('(DO) NOT ALIVE')
            return
        self.command(action, data)

    def command(self, action, data):
        new_data = {'by': self._id}
        new_data.update(data)
        super().command(action, new_data)

    def do_depart(self):
        return self.do('depart', {})

    def do_teleport(self, coordinates):
        self.command('teleport', {
            'coordinates': coordinates
        })

    def when(self, event, callback, data=None, infinity=False):
        if not self.is_alive:
            print('(WHEN) NOT ALIVE')
            return
        def new_callback(*args, **kwargs):
            if not self.is_alive:
                return
            callback(*args, **kwargs)

        super().when(event, new_callback, data, infinity)
