from tools import ROLE, ATTRIBUTE, ACTION, DEFEAT_REASON, OUTPUT, STD,\
    OBSTACLE, INITIAL, PLAYER


def gen_xy_pos(position):
    if not position:
        return position
    return {
        'x': position[0],
        'y': position[1]
    }


class FightLogger:
    def __init__(self, fight_handler):
        self._fight_handler = fight_handler
        self.data = {
            OUTPUT.INITIAL_CATEGORY: {
                OUTPUT.BUILDINGS: {},
                OUTPUT.OBSTACLES: {},
                OUTPUT.UNITS: {},
                OUTPUT.CRAFTS: {},
                OUTPUT.PLAYERS: {}
            },
            OUTPUT.FRAME_CATEGORY: [],
            OUTPUT.RESULT_CATEGORY: {}
        }

    def get_battle_fighters(self):
        return self._fight_handler.get_battle_fighters()

    def get_all_fighters(self):
        return self._fight_handler.fighters.values()

    def get_crafts(self):
        return self._fight_handler.get_crafts()

    def get_flagman(self):
        return self._fight_handler.get_flagman()

    def get_players(self):
        return self._fight_handler.players.values();

    def send_battle(self, data):
        self._fight_handler.editor_client.send_battle(data)

    def initial_state(self):
        for item in self.get_battle_fighters():
            if item.role == ROLE.UNIT:
                self.initial_state_unit(item)
            elif item.role in ROLE.PLAYER_STATIC:
                self.initial_state_building(item)
            elif item.role == ROLE.OBSTACLE:
                if item.item_type == OBSTACLE.ROCK:
                    self.initial_state_obstacle(item)
                elif item.item_type == OBSTACLE.FLAG_STOCK:
                    self.initial_state_flag_stock(item)
                else:
                    self.initial_state_building(item)
        for craft in self.get_crafts():
            self.initial_state_craft(craft)
        for player in self.get_players():
            self.initial_state_player(player)
        self.initial_state_system()

    def initial_state_unit(self, unit):
        self.data[OUTPUT.INITIAL_CATEGORY][OUTPUT.UNITS][unit.id] = {
            OUTPUT.ITEM_ID: unit.id,
            OUTPUT.TILE_POSITION: gen_xy_pos(unit.tile_position),
            OUTPUT.ITEM_TYPE: unit.item_type,
            OUTPUT.PLAYER_ID: unit.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: unit.player[PLAYER.ID]
        }

    def initial_state_building(self, building):
        log_record = {
            OUTPUT.ITEM_ID: building.id,
            OUTPUT.TILE_POSITION: gen_xy_pos(building.tile_position),
            OUTPUT.ITEM_TYPE: building.item_type,
            OUTPUT.SIZE: building.base_size,
            OUTPUT.ITEM_STATUS: building.item_status,
            OUTPUT.ITEM_LEVEL: building.level,
            OUTPUT.PLAYER_ID: building.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: building.player[PLAYER.ID]
        }
        self.data[OUTPUT.INITIAL_CATEGORY][OUTPUT.BUILDINGS][building.id] = log_record
        return log_record

    def initial_state_flag_stock(self, building):
        log = self._log_initial_building(building)
        log[OUTPUT.FLAG_SLUG] = building.player[PLAYER.ENV_NAME]

    def initial_state_obstacle(self, obstacle):
        self.data[OUTPUT.INITIAL_CATEGORY][OUTPUT.OBSTACLES][obstacle.id] = {
            OUTPUT.TILE_POSITION: gen_xy_pos(obstacle.tile_position),
            OUTPUT.SIZE: obstacle.base_size,
            OUTPUT.ID: obstacle.id,
        }

    def initial_state_craft(self, craft):
        self.data[OUTPUT.INITIAL_CATEGORY][OUTPUT.CRAFTS][craft.id] = {
            OUTPUT.ITEM_ID: craft.id,
            OUTPUT.TILE_POSITION: gen_xy_pos(craft.tile_position),
            OUTPUT.ITEM_TYPE: craft.item_type,
            OUTPUT.ITEM_LEVEL: craft.level,
            OUTPUT.PLAYER_ID: craft.player[PLAYER.ID],
            OUTPUT.PLAYER_ID_DEP: craft.player[PLAYER.ID]
        }

    def initial_state_player(self, player):
        self.data[OUTPUT.INITIAL_CATEGORY][OUTPUT.PLAYERS][player[PLAYER.ID]] = {
            OUTPUT.ID: player[PLAYER.ID],
            OUTPUT.USERNAME: player.get(PLAYER.USERNAME, str(player[PLAYER.ID]))
        }

    def initial_state_system(self):
        self.data[OUTPUT.SYSTEM] = {
            'mapSize': self._fight_handler.map_size,
            'timeLimit': self._fight_handler.time_limit,
            'timeAccuracy': self._fight_handler.GAME_FRAME_TIME
        }

    def new_frame(self):
        self.data[OUTPUT.FRAME_CATEGORY].append(self.snapshot())

    def snapshot(self):
        snapshot = []
        for item in self.get_all_fighters():
            if item.is_obstacle:
                continue
            item_info = {
                OUTPUT.ITEM_ID: item.id,
                OUTPUT.TILE_POSITION: gen_xy_pos(item.coordinates if item.role == ROLE.UNIT
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
                item_info[OUTPUT.STDOUT] = item.get_std(STD.OUT)
            if item.has_std(STD.ERR):
                item_info[OUTPUT.STDERR] = item.get_std(STD.ERR)

            item.reset_std()

            if item.sub_items:
                item_info[OUTPUT.SUBITEMS] = item.output_sub_items()

            snapshot.append(item_info)
        return snapshot

    def battle_result(self, winner_id):
        self.data[OUTPUT.RESULT_CATEGORY] = {
            OUTPUT.WINNER: winner_id,
            OUTPUT.REWARDS: self._fight_handler.initial_data.get(INITIAL.REWARDS, {}),
            OUTPUT.CASUALTIES: self._fight_handler.count_unit_casualties(),
            OUTPUT.DEFEAT_REASON: self._fight_handler.defeat_reason
        }
    def send_full_battle(self):
        self.send_battle(self.data)

    def done_battle(self, winner):
        self.new_frame()
        self.send_full_battle()


class StreamFightLogger(FightLogger):
    def new_frame(self, status=None):
        if status is None:
            status = {}

        fight_items = [fighter.internal_info for fighter in self.get_all_fighters()]
        craft_items = [craft.info for craft in self.get_crafts()]
        flagman = self.get_flagman()

        self.send_battle({
            "status": status,
            "is_stream": True,
            'fight_items': fight_items,
            'craft_items': craft_items,
            'map_size': self._fight_handler.map_size,
            'map_grid': self._fight_handler.map_grid,
            'current_frame': self._fight_handler.current_frame,
            'current_game_time': self._fight_handler.current_game_time,
            'flagman': flagman and flagman.info
        })

        for fighter in self.get_all_fighters():
            fighter.reset_std()


    def done_battle(self, winner):
        self.new_frame({
            'winner': winner
        })