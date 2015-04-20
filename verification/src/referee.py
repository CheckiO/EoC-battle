from tornado import gen
from tornado.ioloop import IOLoop

from checkio_referee import RefereeBase
from checkio_referee.handlers.base import BaseHandler

import settings_env
from actions import ItemActions
from actions.exceptions import ActionValidateError
from environment import BattleEnvironmentsController


# TEMPORARILY  HERE
MAP_SIZE = (10, 10)


def distance_to_point(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


class FightItem(object):

    HANDLERS = None
    ACTIONS = None

    ITEMS_COUNT = 0

    def __init__(self, item_data, player, fight_handler):
        self.init_handlers()
        
        self.id = self.generate_id()
        self.player = player
        self.type = item_data.get('type')
        self.health = item_data.get('health')
        self.size = item_data.get('size')
        self.speed = item_data.get('speed')
        self.coordinates = item_data.get('coordinates')
        self.code = item_data.get('code')
        self.fire_speed = item_data.get('fire_speed')
        self.damage = item_data.get('damage')
        self.range = item_data.get('range')

        self.action = item_data.get('action')
        self.charging = 0

        self._fight_handler = fight_handler
        self._initial = item_data
        self._env = None
        self._state = None
        self._actions_handlers = ItemActions.get_factory(self, fight_handler=fight_handler)
        self.set_state_stand()

    @property
    def is_dead(self):
        return self.health <= 0

    @classmethod
    def generate_id(cls):
        cls.ITEMS_COUNT += 1
        return cls.ITEMS_COUNT

    @property
    def info(self):
        return {
            'id': self.id,
            'player': self.player,
            'type': self.type,
            'health': self.health,
            'size': self.size,
            'speed': self.speed,
            'coordinates': self.coordinates,
            'fire_speed': self.fire_speed,
            'damage': self.damage,
            'range': self.range,
            'action': self.action,
            'state': self._state
        }

    def init_handlers(self):
        self.HANDLERS = {
            'select': self.method_select,
            'set_action': self.method_set_action,
            'subscribe': self.method_subscribe,
        }

    def set_state_stand(self):
        self._state = {'action': 'stand'}

    def set_state_dead(self):
        self._state = {'action': 'dead'}

    def set_coordinates(self, coordinates):
        self.coordinates = coordinates
        self._fight_handler.send_range_events(self.id)

    @property
    def is_executable(self):
        if self.type == 'unit':
            if self.coordinates is not None:
                return True
        elif self.code is not None:
            return True
        return False

    @gen.coroutine
    def start(self):
        if not self.is_executable:
            return

        self._env = yield self._fight_handler.get_environment(self.player['env_name'])
        result = yield self._env.run_code(self.code)
        while True:
            status = result.pop('status')
            if status and status != 'success':
                pass  # TODO:
            self.handle_result(result)
            result = yield self._env.read_message()

    def handle_result(self, data):
        handler_name = data.pop('method', None)
        if handler_name is None:
            # raise Exception("WTF")
            return  # TODO: this data is not from commander, then for what?
        handler = self.HANDLERS[handler_name]
        handler(**data)

    def method_select(self, fields):
        data = {}
        for field in fields:
            if field['field'] == 'initials':
                data.update(self._select_info(self.id))
            elif field['field'] == 'info':
                data.update(self._select_info(field['data']['id']))
            elif field['field'] == 'nearest_enemy':
                data.update(self._select_nearest_enemy(field['data']['id']))
            else:
                raise Exception("Wtf")
        self._env.select_result(data)

    def _select_info(self, item_id):
        return self._fight_handler.get_item_info(item_id)

    def _select_nearest_enemy(self, item_id):
        return self._fight_handler.get_nearest_enemy(item_id)

    def method_set_action(self, action, data):
        try:
            self.action = self._actions_handlers.parse_action_data(action, data)
        except ActionValidateError as e:
            self._env.bad_action(e)
        else:
            self._env.confirm()

    def method_subscribe(self, event, lookup_key, data):
        result = self._fight_handler.subscribe(event, self.id, lookup_key, data)
        if not result:
            self._env.bad_action()
            return
        self._env.confirm()

    def do_frame_action(self):
        self._state = self._actions_handlers.do_action(self.action)

    def send_event(self, lookup_key, data):
        self._env.send_event(lookup_key, data)


class FightHandler(BaseHandler):

    FRAME_TIME = 0.1  # compute and send info each time per FRAME_TIME
    GAME_FRAME_TIME = 0.1  # per one FRAME_TIME in real, in game it would be GAME_FRAME_TIME

    """
    Each item must have next structure:
    {
        'receiver_id': <item_id>,
        'lookup_key': <lookup_function_key>,
        'data': <data_for_check_event>
    }
    """
    EVENTS = {
        'death': [],
        'item_in_range': [],
        'item_in_my_range': [],
    }

    def __init__(self, editor_data, editor_client, referee):
        self.players = None
        self.fighters = {}
        self.current_frame = 0
        self.current_game_time = 0
        self.initial_data = editor_data['code']  # TODO: rename attr
        super().__init__(editor_data, editor_client, referee)

    @gen.coroutine
    def start(self):
        self.players = {p['id']:p for p in self.initial_data['players']}
        fight_items = []
        for item in self.initial_data['map']:
            player = self.players[item['player_id']]
            fight_items.append(self.add_fight_item(item, player))

        self.compute_frame()
        yield fight_items

    @gen.coroutine
    def add_fight_item(self, item_data, player):
        fight_item = FightItem(item_data, player=player, fight_handler=self)
        self.fighters[fight_item.id] = fight_item
        yield fight_item.start()

    def compute_frame(self):
        self.send_frame()
        self.current_frame += 1
        self.current_game_time += self.GAME_FRAME_TIME
        for key, fighter in self.fighters.items():
            if fighter.action is None:
                fighter.set_state_stand()
                continue

            if fighter.is_dead:
                continue
            fighter.do_frame_action()

        winner = self.get_winner()
        if winner is not None:
            self.send_frame({'winner': winner})
        else:
            IOLoop.current().call_later(self.FRAME_TIME, self.compute_frame)

    def get_winner(self):
        for player_id, player in self.players.items():
            if self._is_player_defeated(player):
                del self.players[player_id]

            if len(self.players) == 1:
                return next (iter (self.players.values()))
        return None

    def _is_player_defeated(self, player):
        item_require = None
        if player['defeat'] == 'units':
            item_require = 'unit'
        elif player['defeat'] == 'center':
            item_require = 'center'

        for item in self.fighters.values():
            if item.player['id'] != player['id']:
                continue
            if item.type == item_require and not item.is_dead:
                return False
        return True

    def send_frame(self, status=None):
        if status is None:
            status = {}

        units = []
        for fighter in self.fighters.values():
            units.append(fighter.info)

        self.editor_client.send_custom({
            'status': status,
            'units': units,
            'map_size': MAP_SIZE,
            'current_frame': self.current_frame,
            'current_game_time': self.current_game_time
        })

    def get_item_info(self, item_id):
        return self.fighters[item_id].info

    def get_nearest_enemy(self, item_id):
        min_length = 1000
        nearest_enemy = None

        fighter = self.fighters[item_id]

        for enemy in self.fighters.values():
            if enemy.player == fighter.player or enemy.is_dead:
                continue

            length = distance_to_point(enemy.coordinates, fighter.coordinates)

            if length < min_length:
                min_length = length
                nearest_enemy = enemy
        return self.get_item_info(nearest_enemy.id)

    def subscribe(self, event_name, item_id, lookup_key, data):
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
        for events in self.EVENTS.values():
            for event in events:
                if event['receiver_id'] == item.id:
                    events.remove(event)

    def send_death_event(self, item_id):
        events = self.EVENTS['death']
        for event in events:
            if event['data']['id'] != item_id:
                continue
            receiver = self.fighters[event['receiver_id']]
            receiver.send_event(lookup_key=event['lookup_key'], data={'id': item_id})

    def send_range_events(self, item_id):
        self._send_my_range_event(item_id)
        self._send_custom_range_event(item_id)

    def _send_my_range_event(self, item_id):
        event_item = self.fighters[item_id]
        events = self.EVENTS['item_in_my_range']
        for event in events:
            receiver = self.fighters[event['receiver_id']]
            if receiver.id == event_item.id:
                continue

            distance = distance_to_point(receiver.coordinates, event_item.coordinates)
            if distance > receiver.range:
                continue
            receiver.send_event(lookup_key=event['lookup_key'], data={'id': item_id})

    def _send_custom_range_event(self, item_id):
        event_item = self.fighters[item_id]
        events = self.EVENTS['item_in_range']
        for event in events:
            receiver = self.fighters[event['receiver_id']]
            if receiver.id == event_item.id:
                continue

            distance = distance_to_point(event['data']['coordinates'], event_item.coordinates)
            if distance > event['data']['range']:
                continue
            receiver.send_event(lookup_key=event['lookup_key'], data={'id': item_id})


class Referee(RefereeBase):
    ENVIRONMENTS = settings_env.ENVIRONMENTS
    EDITOR_LOAD_ARGS = ('code', 'action', 'env_name')
    HANDLERS = {'check': FightHandler, 'run': FightHandler}

    @property
    def environments_controller(self):
        if not hasattr(self, '_environments_controller'):
            setattr(self, '_environments_controller', BattleEnvironmentsController(
                self.ENVIRONMENTS))
        return getattr(self, '_environments_controller')
