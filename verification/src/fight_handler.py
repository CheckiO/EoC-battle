import logging
from tornado import gen
from tornado.ioloop import IOLoop
from random import choice
import os
import shutil

from checkio_referee.handlers.base import BaseHandler

from fight_item import FightItem, CraftItem, FlagItem, UnitItem, MineItem, \
    DefPlatformItem, SentryGunTowerItem, MachineGunTowerItem, HeavyBotUnit
from fight_logger import FightLogger, StreamFightLogger
from fight_events import FightEvent

from tools import precalculated, fill_square, grid_to_graph
from consts import COORDINATE_EDGE_CUT, PERCENT_CENTER_AUTO_DAMAGE, FOLDER_CODES
from tools import ROLE, ATTRIBUTE, ACTION, DEFEAT_REASON, OUTPUT, STD,\
    OBSTACLE, INITIAL, PLAYER, DEF_TYPE, ATTACK_TYPE
from tools.terms import ENV
from tools.distances import euclidean_distance


logger = logging.getLogger(__name__)

def gen_xy_pos(position):
    if not position:
        return position
    return {
        'x': position[0],
        'y': position[1]
    }


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

    
    def __init__(self, editor_data, editor_client, referee):
        self.editor_client = editor_client 
        self.initial_data = editor_data['battle_info']
        self._referee = referee #referee.Referee

        self.players = {p['id']: p for p in self.initial_data[PLAYER.KEY]}
        self.players[-1] = {"id": -1} # im not sure yet, why are we doing this
        self.fighters = {} # {id: FigherItem}
        
        self.map_size = self.initial_data[INITIAL.MAP_SIZE]
        self.time_limit = self.initial_data.get(INITIAL.TIME_LIMIT, float("inf"))
        self.codes = self.initial_data[INITIAL.CODES]

        # generated to optimize path finding algo
        self.map_grid = [[]]
        self.map_graph = {}
        self.map_hash = 0
        
        
        self.current_frame = 0
        self.current_game_time = 0
        self.defeat_reason = None

        # FightItem for CommandCenter
        self.fi_center = None

        self.setup_usercodes(self.initial_data[INITIAL.CODES])

        # is using by referee
        self._is_stopping = None 
        self._stop_callback = None
        self.environment = None

        self.event = FightEvent(self)
        self.log = FightLogger(self)

    def setup_usercodes(self, players):
        for player_id, codes in players.items():
            for name, source in codes.items():
                username = 'player' + player_id
                filename = os.path.join(FOLDER_CODES, username, name)
                dirname = os.path.dirname(filename)
                os.makedirs(dirname, mode=0o700, exist_ok=True)
                shutil.chown(dirname, user=username)
                
                with open(filename, mode='w', encoding='utf-8') as fh:
                    fh.write(source)

                shutil.chown(filename, user=username)
                os.chmod(filename, 0o700)

    def get_crafts(self):
        return filter(lambda a: a.is_craft, self.fighters.values())

    def get_flagman(self):
        for item in self.fighters.values():
            if item.is_flagman:
                return item

    def all_crafts_empty(self):
        return all([item.is_empty() for item in self.get_crafts()])

    def get_battle_fighters(self):
        """
        Returns units that are on the battle
        :return: battle fighters
        """
        return filter(lambda a: not a.is_craft and not a.is_flagman, self.fighters.values())

    def get_active_battle_fighters(self):
        """
        Returns units that are currently on the battle
        :return: current battle fighters
        """
        return filter(
            lambda a: not a.is_craft and not a.is_flagman and not a.is_dead and not a.is_departed,
            self.fighters.values()
        )

    def set_center(self, center):
        self.fi_center = center

    def damage_center(self, building):
        auto_health_part = self.fi_center.start_hit_points * PERCENT_CENTER_AUTO_DAMAGE
        total_buildings = len(list(filter(lambda a: a.role == ROLE.BUILDING, self.fighters.values())))
        self.fi_center.get_shot(auto_health_part/total_buildings)

    def get_my_data(self, id):
        fighter = self.fighters[id]
        children = {}
        if hasattr(fighter, 'children'):
            for child_id in fighter.children:
                children[child_id] = self.get_my_data(child_id)

        return {
            'id': id,
            'level': fighter.level,
            'role': fighter.role,
            'type': fighter.item_type,
            'children': children,
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
            if value.is_departed:
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

    @gen.coroutine
    def start(self):
        if self.initial_data.get(INITIAL.IS_STREAM, True):
            self.log = StreamFightLogger(self)

        self.event.setup() # there are no specific reasons for setting up 
                           # on start and not on init

        # WHY: can't we move an initialisation of players in the __init__ function?
        # in that case we can use it before start
        
        fight_items = []
        for item in sorted(self.initial_data[INITIAL.MAP_ELEMENTS], key=lambda a: a.get(PLAYER.PLAYER_ID, -1), reverse=True):
            player = self.players[item.get(PLAYER.PLAYER_ID, -1)]

            #TODO: dev-118 flagman as flagPad
            if item[ATTRIBUTE.ITEM_TYPE] == 'flagman' and item.get(ATTRIBUTE.IS_FLYING):
                cls_name = FlagItem
            else:
                cls_names = {
                    DEF_TYPE.SENTRY: SentryGunTowerItem,
                    DEF_TYPE.MACHINE: MachineGunTowerItem,
                    ROLE.CRAFT: CraftItem,
                    ROLE.MINE: MineItem,
                    ROLE.DEF_PLATFORM: DefPlatformItem,
                }
                cls_name = cls_names.get(item[ATTRIBUTE.ITEM_TYPE], FightItem)
            fight_item = cls_name(item, player=player, fight_handler=self)
            self.fighters[fight_item.id] = fight_item
            fight_item.set_state_idle()
            fight_items.append(fight_item.start())

        self.log.initial_state()

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

        cls_names = {
            ATTACK_TYPE.INFANTRY: UnitItem,
            ATTACK_TYPE.HEAVY: HeavyBotUnit,
            ATTACK_TYPE.ROCKET: UnitItem,
        }
        cls_name = cls_names.get(unit[ATTRIBUTE.ITEM_TYPE], FightItem)
        fight_item = cls_name(unit, player=player, fight_handler=self)

        self.fighters[fight_item.id] = fight_item
        fight_item.set_parent_id(craft.id)
        fight_item.set_state_idle()
        fight_item.set_fflag('landed')
        craft.add_child_id(fight_item.id)
        self.log.initial_state_unit(fight_item)

    def generate_craft_place(self):
        width = self.map_size[1]
        craft_positions = [cr.coordinates[1] for cr in self.get_crafts()] # + [20, ] # one extra place for flag
        available = [y for y in range(3, width - 3)
                     if not any(pos - 2 <= y <= pos + 2 for pos in craft_positions)]
        return [self.map_size[0], choice(available) if available else 0]

    def get_frame_time(self):
        # frame time can be variated depends on factors
        return self.FIRST_STEP_FRAME_TIME

    @gen.coroutine
    def compute_frame(self):
        """
            calculate every frame and action for every FightItem
        """
        self.log.new_frame()
        self.current_frame += 1
        self.current_game_time += self.GAME_FRAME_TIME

        # list() - function is required here fot coping 
        # because fighters might be changed during iterations
        for key, fighter in list(self.fighters.items()):
            #print('COMPUTE', fighter.id, fighter.coordinates, fighter.item_type, fighter.action, fighter._state)
            fighter.reset_fflags()
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
            if fighter.is_dead or fighter.is_departed:
                #print('DEAD')
                continue

            if fighter.action is None:
                fighter.set_state_idle()
                continue

            fighter.run_all_one_actions()
            fighter.do_frame_action()

        self.event.check()

        winner = self.get_winner()

        if self.initial_data.get(INITIAL.SEND_PROGRESS):
            self.log.send_frame_progress()

        if winner is not None: 
            self.log.done_battle(winner)
            IOLoop.current().call_later(3, self.stop)
        else:
            IOLoop.current().call_later(self.get_frame_time(), self.compute_frame)

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
                self.log.battle_result(real_players[0])
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
            if item.player['id'] == player['id'] and item.role == role and not item.is_dead and not item.is_departed:
                return True
        return False

    def subscribe(self, event_name, item_id, lookup_key, data):
        """
            subscribe an FightItem with ID "item_id" on event "event_name" with data "data"
            and on item side it registered as lookup_key
        """

        subscribe_data = {
            'receiver_id': item_id,
            'lookup_key': lookup_key,
            'data': data
        }
        
        self.event.add_subscriptions(event_name, subscribe_data)
        return True
    def unsubscribe(self, fight_item):
        self.event.unsubscribe_all(fight_item.id)

    def battle_fighters(self):
        for item in self.fighters.values():
            if item.is_obstacle:
                continue
            if item.is_dead:
                continue
            if item.is_departed:
                continue
            yield item
