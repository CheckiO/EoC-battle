import os

from handlers.base import BaseHandler
from server import TCPConsoleServer

MAP_X = 2

MAP_BUILDING = 1

# TODO: out current lap


class FightHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.chdir(os.path.dirname(self.user_data['code_path']))
        gg = {}
        exec(self.user_data['code'], gg)
        self.user_data['code'] = gg['PLAYERS']
        if 'MAP_X' in gg:
            global MAP_X
            MAP_X = gg['MAP_X']
        self.ROUTING['custom'] = 'handler_custom'

    def handler_stderr(self, line, request_id, stream_r):
        print('ERROR {}: {}'.format(request_id, line))

    def handler_custom(self, data, request_id, stream_r):

        out_map = []
        for item in range(data['map_size'][0] * MAP_X):
            out_map.append([None] * (data['map_size'][1] * MAP_X))

        players_groups = [[], []]
        for item in data['units']:
            players_groups[item['player']['id']].append(item)
            coordinates = item['coordinates']
            r_coordinates = (round(coordinates[0] * MAP_X), round(coordinates[1] * MAP_X))
            out_map[r_coordinates[0]][r_coordinates[1]] = item
            size = item.get('size')
            if not size:
                continue
            half_size = round((item['size'] / 2) * MAP_X)
            for xs in range(r_coordinates[0] - half_size, r_coordinates[0] + half_size + 1):
                if xs < 0:
                    continue
                for ys in range(r_coordinates[1] - half_size, r_coordinates[1] + half_size + 1):
                    if ys < 0:
                        continue
                    try:
                        if out_map[xs][ys] is not None:
                            continue
                    except IndexError:
                        continue

                    out_map[xs][ys] = MAP_BUILDING

        print()
        print('-'*30)
        print('{:<10}'.format(round(data['current_game_time']*1.0, 4)), end='')
        print('-'*20)
        print('-'*30)
        print('  ', end='')
        for i in range(data['map_size'][0]):
            print('{num:<{size}}'.format(num=i, size=MAP_X*2), end='')
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

        for num, player in enumerate(players_groups):
            print('PLAYER {}:'.format(num + 1))
            for item in player:
                print('  {sysid}{type} {health} - {str_state}'.format(
                    sysid=item['id'],
                    type=item['type'],
                    health=item['health'],
                    str_state=self.str_state(item['state'])
                ))
        if 'winner' in data['status']:
            print('Game Over!!! The Winner is {}'.format(data['status']['winner']['id']))

    def str_state(self, state):
        if state['action'] in ('stand', 'charging', 'dead'):
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
                *(state['from']+state['to'])
            )

    def short_name(self, item):
        return item['type'][0].upper() + str(item['player']['id'])


class ServerController(TCPConsoleServer):
    cls_handler = FightHandler
