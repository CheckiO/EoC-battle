from battle.tools import euclidean_distance


def enemy(client, item):
    return client.my_info['player_id'] != item['player_id'] and item['player_id'] != -1


def my(client, item):
    return client.my_info['player_id'] == item['player_id']


def roles(roles_list):
    def _filter(client, item):
        return item['role'] in roles_list
    return _filter


def in_my_range(client, item):
    if not client.my_info.get('coordinates') or not item.get('coordinates'):
        return False
        
    distance = euclidean_distance(item['coordinates'], client.my_info['coordinates'])
    return distance - item['size'] / 2 <= client.my_info['firing_range']
