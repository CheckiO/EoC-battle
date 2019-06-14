import logging
from tornado import gen
from tornado.ioloop import IOLoop
from random import choice

from checkio_referee.handlers.base import BaseHandler

from fight_item import FightItem, CraftItem, FlagItem, UnitItem, MineItem, \
    DefPlatformItem
from tools import precalculated, fill_square, grid_to_graph
from consts import COORDINATE_EDGE_CUT, PERCENT_CENTER_AUTO_DEMAGE
from tools import ROLE, ATTRIBUTE, ACTION, DEFEAT_REASON, OUTPUT, STD,\
    OBSTACLE, INITIAL, PLAYER
from tools.terms import ENV
from tools.distances import euclidean_distance


logger = logging.getLogger(__name__)


class FightHandler(BaseHandler):
    """
        The main class of the game.
        Where all the game calculation do
    """

    FIRST_STEP_FRAME_TIME = 0.5
    FRAME_TIME = 0.005  # compute and send info each time per FRAME_TIME
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
        'idle': [],
        'enemy_in_my_firing_range': [],
        'time': [],
        'message': [],
        'unit_landed': [],
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

        # FightItem for CommandCenter
        self.fi_center = None

        self._total_events_sent = 1

    def get_crafts(self):
        return filter(lambda a: a.is_craft, self.fighters.values())

    def get_flagman(self):
        for item in self.fighters.values():
            if item.is_flagman:
                return item

    def all_crafts_empty(self):
        return all([item.is_empty() for item in self.get_crafts()])

    def get_battle_fighters(self):
        '''
            returns only units that are on the battle
        '''
        return filter(lambda a: not a.is_craft and not a.is_flagman, self.fighters.values())

    def set_center(self, center):
        self.fi_center = center

    def demage_center(self, building):
        auto_health_part = self.fi_center.start_hit_points * PERCENT_CENTER_AUTO_DEMAGE
        total_buildings = len(list(filter(lambda a: a.role == ROLE.BUILDING, self.fighters.values())))
        self.fi_center.get_shoted(auto_health_part/total_buildings)

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
            'game': self.get_env_game_data()
        }

    def get_env_map_data(self):
        data = {}
        for key, value in self.fighters.items():
            if value.is_dead:
                continue
            if value.is_obstacle:
                continue
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
    def send_editor_current_frame(self):
        self.editor_client.send_process({'type': 'frame', 'current': self.current_frame})
        IOLoop.current().call_later(1, self.send_editor_current_frame)

    @gen.coroutine
    def start(self):
        self.send_editor_current_frame()
        self.is_stream = self.initial_data.get(INITIAL.IS_STREAM, True)
        # WHY: can't we move an initialisation of players in the __init__ function?
        # in that case we can use it before start
        self.players = {p['id']: p for p in self.initial_data[PLAYER.KEY]}
        self.players[-1] = {"id": -1}
        for code_data in self.initial_data[INITIAL.CODES]:
            self.codes[code_data["id"]] = code_data

        self.map_size = self.initial_data[INITIAL.MAP_SIZE]
        self.rewards = self.initial_data.get(INITIAL.REWARDS, {})
        self.strat_rewards = self.initial_data.get(INITIAL.STRAT_REWARDS, {})
        self.time_limit = self.initial_data.get(INITIAL.TIME_LIMIT, float("inf"))
        fight_items = []
        for item in sorted(self.initial_data[INITIAL.MAP_ELEMENTS], key=lambda a: a.get(PLAYER.PLAYER_ID, -1), reverse=True):
            player = self.players[item.get(PLAYER.PLAYER_ID, -1)]
            if item[ATTRIBUTE.ITEM_TYPE] == 'craft':
                cls_name = CraftItem
            elif item[ATTRIBUTE.ITEM_TYPE] == 'flagman' and item.get(ATTRIBUTE.IS_FLYING):
                cls_name = FlagItem
            elif item[ATTRIBUTE.ITEM_TYPE] == 'mine':
                cls_name = MineItem
            elif item[ATTRIBUTE.ITEM_TYPE] == 'defPlatform':
                cls_name = DefPlatformItem
            else:
                cls_name = FightItem
            fight_item = cls_name(item, player=player, fight_handler=self)
            self.fighters[fight_item.id] = fight_item
            fight_item.set_state_idle()
            fight_items.append(fight_item.start())


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
            if not it.size or not it.coordinates:
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
        player = self.players[craft_data.get(PLAYER.PLAYER_ID, -1)]
        fight_item = UnitItem(unit, player=player, fight_handler=self)
        self.fighters[fight_item.id] = fight_item
        fight_item.set_parent_id(craft.id)
        fight_item.set_state_idle()
        self._log_initial_unit(fight_item)
        self._send_unit_landed(craft.craft_id, fight_item.id)

    def generate_craft_place(self):
        width = self.map_size[1]
        craft_positions = [cr.coordinates[1] for cr in self.get_crafts()]
        available = [y for y in range(3, width - 3)
                     if not any(pos - 2 <= y <= pos + 2 for pos in craft_positions)]
        return [self.map_size[0], choice(available) if available else 0]

    def inc_total_events_sent(self):
        self._total_events_sent += 1

    def reset_total_events_sent(self):
        self._total_events_sent = 1

    def get_frame_time(self):
        # frame time can be variated depends on factors
        return self.FIRST_STEP_FRAME_TIME

    @gen.coroutine
    def compute_frame(self):
        """
            calculate every frame and action for every FightItem
        """
        self.send_frame()
        self.current_frame += 1
        self.current_game_time += self.GAME_FRAME_TIME

        # list() - function is required here fot coping 
        # because fighters might be changed during iterations
        for key, fighter in list(self.fighters.items()):
            for sub_item in list(fighter.get_sub_items()):
                sub_item.do_frame_action()
                if sub_item.is_dead:
                    fighter.remove_sub_item(sub_item)

            for extra in list(fighter.get_extras()):
                extra.do_frame_action(fighter)
                if extra.is_dead:
                    fighter.remove_extras(extra)

            # WHY: can't we move in the FightItem class?
            # When in can be None?
            if fighter.is_dead:
                continue

            if fighter.action is None:
                fighter.set_state_idle()
                continue

            fighter.run_all_one_actions()
            fighter.do_frame_action()

        self._send_time()
        self._send_message()
        self._send_position()
        self._send_idle()
        self._send_dead()

        winner = self.get_winner()

        if winner is not None:
            self.send_frame({'winner': winner}, True)
            IOLoop.current().call_later(3, self.stop)
        else:
            IOLoop.current().call_later(self.get_frame_time(), self.compute_frame)
            self.reset_total_events_sent()

    def count_unit_casualties(self):
        result = {craft.craft_id: {
            OUTPUT.CRAFT_ID: craft.craft_id,
            OUTPUT.COUNT: 0,
            OUTPUT.ITEM_TYPE: craft.unit_type} for craft in self.get_crafts()}
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
                not self._is_player_has_item_role(player, ROLE.UNIT) and
                self.all_crafts_empty()):
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
            craft_items = [craft.info for craft in self.get_crafts()]
            flagman = self.get_flagman()

            self.editor_client.send_battle({
                "is_stream": True,
                'status': status,
                'fight_items': fight_items,
                'craft_items': craft_items,
                'map_size': self.map_size,
                'map_grid': self.map_grid,
                'current_frame': self.current_frame,
                'current_game_time': self.current_game_time,
                'flagman': flagman and flagman.info
            })
        self.battle_log["frames"].append(self._get_battle_snapshot())
        if battle_finished and not self.is_stream:
            self.editor_client.send_battle(self.battle_log)

    def _log_initial_state(self):
        for item in self.get_battle_fighters():
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
        for craft in self.get_crafts():
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

            if item.sub_items:
                item_info[OUTPUT.SUBITEMS] = item.output_sub_items()

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
        # TODO: The function should be remove for overcompexity
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

    def battle_fighters(self):
        for item in self.fighters.values():
            if item.is_obstacle:
                continue
            if item.is_dead:
                continue
            yield item

    def _send_position(self):
        """
            Go through all events and check intersections
        """

        events = self.EVENTS['im_in_area']
        for event in events[:]:
            receiver = self.fighters[event['receiver_id']]
            distance = euclidean_distance(receiver.coordinates, event["data"]["coordinates"])
            if distance < event["data"]["radius"]:
                data_to_event = {
                    ENV.DATA: self.get_env_data(),
                    ENV.MY_DATA: self.get_my_data(event['receiver_id']),
                    ATTRIBUTE.ID: receiver.id,
                    "distance": distance
                }
                receiver.send_event(lookup_key=event['lookup_key'],
                                    data=data_to_event)
                events.remove(event)

        events = self.EVENTS['enemy_in_my_firing_range']
        for event in events[:]:
            receiver = self.fighters[event['receiver_id']]
            for event_item in self.battle_fighters():
                if event_item.is_dead:
                    continue
                if receiver == event_item:
                    continue
                if event_item.player == receiver.player:
                    continue
                if not event_item.coordinates:
                    continue
                distance = euclidean_distance(receiver.coordinates, event_item.coordinates)
                if distance - event_item.size / 2 > receiver.firing_range:
                    continue

                data_to_event = {
                    ENV.DATA: self.get_env_data(),
                    ENV.MY_DATA: self.get_my_data(event['receiver_id']),
                    'id': event_item.id
                }
                receiver.send_event(lookup_key=event['lookup_key'],
                                    data=data_to_event)
                events.remove(event)
                break

        events = self.EVENTS['any_item_in_area']
        for event in events[:]:
            receiver = self.fighters[event['receiver_id']]
            for event_item in self.battle_fighters():
                if event_item.is_dead:
                    continue
                distance = euclidean_distance(event['data']['coordinates'], event_item.coordinates)
                if distance > event['data']['radius']:
                    continue

                data_to_event = {
                    ENV.DATA: self.get_env_data(),
                    ENV.MY_DATA: self.get_my_data(event['receiver_id']),
                    'id': event_item.id
                }
                receiver.send_event(lookup_key=event['lookup_key'],
                                    data=data_to_event)
                events.remove(event)
                break

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

    def _send_idle(self):
        def check_function(event, event_item, receiver):
            return (
                    event['data']['id'] in self.fighters and
                    self.fighters[event['data']['id']]._state.get('action') == 'idle'
            )

        def message_data(event, event_item, receiver):
            return {'id': event['data']['id']}

        self._send_event(None, 'idle', check_function, message_data)

    def _send_dead(self):

        def check_function(event, event_item, receiver):
            fighter = receiver._fight_handler.fighters.get(event['data']['id'])
            return fighter is None or fighter.is_dead

        def data_id(event, event_item, receiver):
            return {'id': event['data']['id']}

        self._send_event(None, 'death', check_function, data_id)

    def _send_unit_landed(self, craft_id, unit_id):

        def check_function(event, event_item, receiver):
            return event['data']['craft_id'] == craft_id

        def data_id(event, event_item, receiver):
            return self.fighters[unit_id].info

        self._send_event(None, 'unit_landed', check_function, data_id)

