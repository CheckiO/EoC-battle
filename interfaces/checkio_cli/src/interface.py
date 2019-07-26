import os
import sys
from datetime import datetime
import json
import atexit

from handlers.base import BaseHandler
from server import TCPConsoleServer
from collections import defaultdict

MAP_X = 2
SHOW_MAP = False

MAP_BUILDING = 1

# TODO: out current lap

LOG_DIRNAME = "/root/tmp/"
ERR_LOG_FILE_OPEN = "Cann't open log file for writing - {}"

if not os.path.exists(LOG_DIRNAME):
    os.mkdir(LOG_DIRNAME)


class FightHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir(os.path.dirname(self.user_data['code_path']))
        gg = {}
        exec(self.user_data['code'], gg)
        self.user_data['battle_info'] = gg['PLAYERS']
        if 'MAP_X' in gg:
            global MAP_X
            MAP_X = gg['MAP_X']
        self.ROUTING['battle'] = 'handler_battle'
        if not os.path.exists(LOG_DIRNAME):
            os.mkdir(LOG_DIRNAME)
        log_filename = "battle_log.json"
        try:
            self.log_file = open(os.path.join(LOG_DIRNAME, log_filename), "w")
        except IOError:
            print(ERR_LOG_FILE_OPEN.format(log_filename))
            self.log_file = None
        atexit.register(self.close_log_file)

    def handler_stderr(self, line, request_id, stream_r):
        print('ERROR {}: {}'.format(request_id, line))

    def close_log_file(self):
        if self.log_file:
            self.log_file.close()

    def write_log(self, data):
        if self.log_file:
            self.log_file.write(json.dumps(data))

    def handler_battle(self, data, request_id, stream_r):
        if not data.get("is_stream"):
            print('DONE!')
            self.write_log(data)
            return
        out_map = []
        # temporarily spike (I know about "temporarily" (we have ticket for this))
        map_size = [t + 1 for t in data['map_size']]
        for item in range(map_size[0] * MAP_X):
            out_map.append([None] * (map_size[1] * MAP_X))

        players_groups = defaultdict(list)
        for item in data['fight_items']:
            if 'std' in item and any(item['std'].values()):
                print('{:<10}'.format(item['id']), end='')
                print('-' * 20)
                if item['std']['out']:
                    print(''.join(item['std']['out']))
                if item['std']['err']:
                    print(''.join(item['std']['err']), file=sys.stderr)
            if item.get('type') in ('craft', 'flagman'):
                continue
            players_groups[item['player_id']].append(item)
            coordinates = item['coordinates']
            r_coordinates = (round(coordinates[0] * MAP_X), round(coordinates[1] * MAP_X))
            out_map[r_coordinates[0]][r_coordinates[1]] = item
            size = item.get('size')

            if not size or item.get("state", {}).get("action") == "dead":
                continue
            half_size = round((item['size'] / 2) * MAP_X)
            for xs in range(max(0, r_coordinates[0] - half_size),
                            r_coordinates[0] + half_size + 1):
                for ys in range(max(0, r_coordinates[1] - half_size),
                                r_coordinates[1] + half_size + 1):
                    try:
                        if out_map[xs][ys] is not None:
                            continue
                    except IndexError:
                        continue

                    out_map[xs][ys] = MAP_BUILDING
                print()
        print('-' * 30)
        print('{:<10}'.format(round(data['current_game_time'] * 1.0, 4)), end='')
        print('-' * 20)
        print('-' * 30)
        print('  ', end='')
        if SHOW_MAP:
            for i in range(map_size[0]):
                print('{num:<{size}}'.format(num=i, size=MAP_X * 2), end='')
            print()
            for num, line in enumerate(out_map):
                if num % MAP_X:
                    out_line = '  '
                else:
                    out_line = '{:>2}'.format(num // MAP_X)
                for el in line:
                    if el is None:
                        out_line += '..'
                    elif el == MAP_BUILDING:
                        out_line += '##'
                    else:
                        out_line += self.short_name(el)
                print(out_line)
            craft_positions = [craft["coordinates"][1] for craft in data["craft_items"]]

            craft_line = "  "

            for i in range(len(out_map[0] if out_map else 0)):
                pos = i / MAP_X
                if any(p - 1 < pos < p + 1 for p in craft_positions):
                    craft_line += "^^"
                else:
                    craft_line += "  "
            print(craft_line + "\n" + craft_line)


        for num, player in players_groups.items():

            print('PLAYER {}:'.format(num if num >= 0 else "X"))
            for item in player:
                print('  {sysid}{role}{extras} {hit_points} - {str_state}'.format(
                    sysid=item['id'],
                    role=item['type'],
                    hit_points=item.get('hit_points'),
                    str_state=self.str_state(item.get('state')),
                    extras=str(item.get('extras', '-')),
                ))
                if item.get('subitems'):
                    print('    ', item['subitems'])

        if data.get('flagman'):
            print('FLAGMAN:', data['flagman']['charge'])
            #if item.get('subitems'):
            print('  ', data['flagman']['subitems'])

        if 'winner' in data['status']:
            print('Game Over!!! The Winner is {}'.format(data['status']['winner']['id']))

    def str_state(self, state):
        if state is None:
            return 'NONE'
        if state['action'] in ('idle', 'charge', 'dead'):
            return state['action']
        if state['action'] == 'attack':
            str_action = 'fire to ' + str(state['aid'])
            if 'damaged' in state:
                str_action += ' and damaged ' + ','.join(map(str, state['damaged']))
            if 'killed' in state:
                str_action += ' and killed ' + ','.join(map(str, state['killed']))
            return str_action
        if state['action'] == 'move':
            return 'move from {:.4f}, {:.4f} to {:.4f}, {:.4f}'.format(
                *(state['from'] + state['to'])
            )

    def short_name(self, item):
        player_id = item['id']
        return item['role'][0].upper() + str(player_id) if player_id >= 0 else "XX"


class ServerController(TCPConsoleServer):
    cls_handler = FightHandler
