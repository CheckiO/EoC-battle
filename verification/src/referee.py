from tornado import gen

from checkio_referee import RefereeBase
from checkio_referee.handlers.base import BaseHandler

from tornado.ioloop import IOLoop

import settings_env

# TEMPORARILY  HERE

MAP_SIZE = (10, 10)
MAP_X = 2


def short_name(item):
    out_line = ''
    if item['type'] == 'defender':
        out_line += 'D'
    else:
        out_line += 'U'
    out_line += str(item['player'])
    return out_line


def show_data(active):
    #return
    out_map = []
    for item in range(MAP_SIZE[0] * MAP_X):
        out_map.append([None] * (MAP_SIZE[1] * MAP_X))

    out_line = ''
    for item in active:
        coordinates = item['coordinates']
        r_coordinates = (round(coordinates[0] * MAP_X), round(coordinates[1] * MAP_X))
        out_map[r_coordinates[0]][r_coordinates[1]] = item
        out_line += short_name(item) + ':' + str(item['health'])
        out_line += ';'
    print(out_line)

    for line in out_map:
        out_line = ''
        for el in line:
            if el is None:
                out_line += '..'
            else:
                out_line += short_name(el)
        print(out_line)


def distance_to_point(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


class FightHandler(BaseHandler):

    def __init__(self, editor_data, editor_client, referee):
        self.initial_data = editor_data['players']
        self.TIME_STEP = 0.1
        self.SYS_TIME_STEP = 0.01
        self.sysids = {}
        self.cur_time = 0
        self.listeners = {}
        self.next_sys_id = 0
        super().__init__(editor_data, editor_client, referee)

    def sid(self, id, attr):
        return self.sysids[id][attr]

    def get_player_attr(self, player_id, attr):
        return self.initial_data['players'][player_id][attr]

    @gen.coroutine
    def start_sys_env(self, sysid):
        data = self.sysids[sysid]
        env = yield self.get_environment(self.get_player_attr(data['player'], 'env_name'))
        data['env'] = env
        result = yield env.run_code(self.initial_data['sources'][data['player']][data['script']])
        while True:
            self.process_result(sysid, result)
            result = yield env.read_message()

    def process_result(self, sysid, data):
        if 'do' not in data:
            return  # TODO: this data is not from commander, then for what?
        return getattr(self, 'process_do_' + data['do'])(sysid, data)

    @gen.coroutine
    def new_sysid(self, data):
        cur_sysid = self.next_sys_id
        self.next_sys_id += 1

        sdata = {
            'sysid': cur_sysid,
            'subscriptions': {},
            'listeners': {},
            'initial': data
        }
        sdata.update(data)
        self.sysids[cur_sysid] = sdata

        if data['type'] == 'unit':
            if 'coordinates' in data:
                self.start_sys_env(cur_sysid)
        elif 'script' in data:
            self.start_sys_env(cur_sysid)

    @gen.coroutine
    def start(self):
        sysids = []
        for item in self.initial_data['map']:
            sysids.append(self.new_sysid(item))

        self.make_steps()
        yield sysids

    def is_game_over(self):
        active_players = set()
        for item in self.sysids.values():
            active_players.add(item['player'])
            if len(active_players) > 1:
                return False
        return True

    def make_steps(self):
        show_data(self.sysids.values())
        self.cur_time += self.TIME_STEP

        for data in list(self.sysids.values()):
            if 'do' not in data:
                continue

            what, do_data = data['do']
            getattr(self, 'do_' + what)(data['sysid'], do_data)

        if self.is_game_over():
            print("Game OVER")
            show_data(self.sysids.values())
            import sys
            sys.exit()
        else:
            IOLoop.current().call_later(self.SYS_TIME_STEP, self.make_steps)

    def process_do_ask(self, sysid, data):
        env = self.sid(sysid, 'env')
        env.write(getattr(self, 'ask_' + data['what'])(sysid, data['data']))

    def ask_initial(self, sysid, data):
        sdata = self.sysids[sysid]
        result = {}
        for key in ('player', 'num', 'sysid', 'type', 'coordinates',
                    'fire_speed', 'fire_demage', 'range'):
            result[key] = sdata[key]
        return result

    def ask_nearest_enemy(self, sysid, data):
        sdata = self.sysids[sysid]
        min_length = 1000
        nearest_data = None

        coordinates = sdata['coordinates']
        for enemy_data in self.sysids.values():
            if enemy_data['player'] == sdata['player']:
                continue

            enemy_coordinates = enemy_data['coordinates']
            length = distance_to_point(enemy_coordinates, coordinates)

            if length < min_length:
                min_length = length
                nearest_data = enemy_data

        return {
            'sysid': nearest_data['sysid'],
            'coordinates': nearest_data['coordinates']
        }

    def raise_event(self, target_sysid, key, data):
        try:
            sdata = self.sysids[target_sysid]
        except KeyError:
            return
        sdata['env'].write({
            'action': 'raise',
            'data': data,
            'key': key
        })

    def process_do_subscribe(self, sysid, data):
        env = self.sid(sysid, 'env')
        env.write(getattr(self, 'subs_' + data['what'])(sysid, data['data'], data['key']))

    def subs_unit_in_my_range(self, sysid, data, key):
        sysdata = self.sysids[sysid]
        self.listeners.setdefault('range', []).append(({
            'radius': data['radius'],
            'coordinates': sysdata['coordinates']
        }, sysid, key))
        return {'ok': 'ok'}

    def subs_death_sysid(self, sysid, data, key):
        sysdata = self.sysids[data['sysid']]
        sysdata['listeners'].setdefault('death', []).append((sysid, key))
        return {'ok': 'ok'}

    def process_do_do(self, sysid, data):
        env = self.sid(sysid, 'env')
        check_attr = 'do_check_' + data['what']
        cant_do = None
        if hasattr(self, check_attr):
            cant_do = getattr(self, check_attr)(sysid, data['data'])

        if cant_do is not None:
            env.write(cant_do)
            return

        self.sysids[sysid]['do'] = (data['what'], data['data'])
        env.write({'ok': 'ok'})

    def do_attack(self, sysid, data):
        if data['sysid'] not in self.sysids:
            return # WTF
        target_data = self.sysids[data['sysid']]
        attacker_data = self.sysids[sysid]

        distance_to_target = distance_to_point(target_data['coordinates'],
                                               attacker_data['coordinates'])

        unit_range = attacker_data['range']
        if distance_to_target < unit_range:
            self._shot(sysid, target_data['sysid'])
        else:
            self._move_to(sysid, target_data['coordinates'])

    def _move_to(self, sysid, target_coor):
        data = self.sysids[sysid]
        handler_coor = data['coordinates']
        distance = distance_to_point(handler_coor, target_coor)

        speed = data['speed'] * self.TIME_STEP

        data['coordinates'] = (
            handler_coor[0] + (speed * (target_coor[0] - handler_coor[0]) / distance),
            handler_coor[1] + (speed * (target_coor[1] - handler_coor[1]) / distance))

        self.check_range_listeners(sysid)

    def check_range_listeners(self, sysid):
        # TODO: check this one
        data = self.sysids[sysid]
        for item in self.listeners['range']:
            idata, target_sysid, key = item
            if distance_to_point(idata['coordinates'], data['coordinates']) < idata['radius']:
                self.raise_event(target_sysid, key, {'sysid': sysid})

    def _shot(self, sysid, target_sysid):
        target_data = self.sysids[target_sysid]
        attacker_data = self.sysids[sysid]

        charging = attacker_data.setdefault('charging', 0)
        charging += self.TIME_STEP * attacker_data['fire_speed']
        attacker_data['charging'] = charging
        if charging >= 1:
            target_data['health'] -= attacker_data['fire_demage']
            attacker_data['charging'] -= 1

            if target_data['health'] <= 0:
                self._dead(target_sysid)

    def _dead(self, sysid):
        data = self.sysids.pop(sysid)
        if 'death' in data['listeners']:
            for item in data['listeners']['death']:
                target_sysid, key = item
                self.raise_event(target_sysid, key, {
                    'sysid': data['sysid']
                })






class Referee(RefereeBase):
    ENVIRONMENTS = settings_env.ENVIRONMENTS
    EDITOR_LOAD_ARGS = ('players', 'action', 'env_name')
    HANDLERS = {'fight': FightHandler}
