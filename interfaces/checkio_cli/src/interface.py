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

    def handler_custom(self, data, request_id, stream_r):

        out_map = []
        for item in range(data['map_size'][0] * MAP_X):
            out_map.append([None] * (data['map_size'][1] * MAP_X))

        players_groups = [[], []]
        for item in data['units']:
            players_groups[item['player']].append(item)
            coordinates = item['coordinates']
            r_coordinates = (round(coordinates[0] * MAP_X), round(coordinates[1] * MAP_X))
            out_map[r_coordinates[0]][r_coordinates[1]] = item
            if 'size' in item:
                size = round(item['size'] * MAP_X)
                for xs in range(r_coordinates[0] - size, r_coordinates[0] + size + 1):
                    if xs < 0:
                        continue
                    for ys in range(r_coordinates[1] - size, r_coordinates[1] + size + 1):
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
        print('{:<10}'.format(round(data['cur_time']*1.0, 4)), end='')
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
                print('  {sysid}{type} {health} - {str_actual}'.format(
                    sysid=item['sysid'],
                    type=item['type'],
                    health=item['health'],
                    str_actual=self.str_actual(item['actual'])
                ))
        if 'winner' in data['status']:
            print('Game Over!!! The Winner is {}'.format(data['status']['winner']))

    def str_actual(self, actual):
        if actual['do'] == 'stand':
            return 'stand'
        if actual['do'] == 'charging':
            return 'charging'
        if actual['do'] == 'fire':
            str_do = 'fire to ' + str(actual['tosysid'])
            if 'damaged' in actual:
                str_do += ' and damaged ' + ','.join(map(str, actual['damaged']))
            if 'killed' in actual:
                str_do += ' and killed ' + ','.join(map(str, actual['killed']))
            return str_do
        if actual['do'] == 'move':
            return 'move from {:.4f}, {:.4f} to {:.4f}, {:.4f}'.format(
                *(actual['from']+actual['to'])
            )

    def short_name(self, item):
        out_line = ''
        if item['type'] == 'defender':
            out_line += 'D'
        else:
            out_line += 'U'
        out_line += str(item['player'])
        return out_line


class ServerController(TCPConsoleServer):
    cls_handler = FightHandler
