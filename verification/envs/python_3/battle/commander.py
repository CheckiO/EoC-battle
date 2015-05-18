PARTY = 'party'
PARTY_ALL = 'all'
PARTY_MY = "my"
PARTY_ENEMY = 'enemy'


class Client(object):
    CLIENT = None

    def __init__(self):
        assert self.CLIENT
        self._initial_info = self.ask_my_info()

    @property
    def item_id(self):
        return self._initial_info["id"]

    @property
    def player_id(self):
        return self._initial_info["player_id"]

    @classmethod
    def set_client(cls, client):
        cls.CLIENT = client

    def select(self, fields):
        return self.CLIENT.select(fields=fields)

    def ask_my_info(self):
        return self.select([{
            'field': 'my_info'
        }])[0]

    def ask_item_info(self, item_id):
        return self.select([{
            'field': 'my_info',
            'data': {
                "id": item_id
            }
        }])[0]

    def ask_players(self, party=PARTY_ALL):
        return self.select([{
            'field': 'players',
            'data': {
                "player_id": self.player_id,
                PARTY: party
            }
        }])[0]

    def ask_enemy_players(self):
        return self.ask_players(PARTY_ENEMY)

    def ask_nearest_enemy(self):
        return self.select([{
            'field': 'nearest_enemy',
            'data': {
                'id': self.item_id
            }
        }])[0]

    def ask_enemy_items_in_my_firing_range(self):
        return self.select([{
            'field': 'enemy_items_in_my_firing_range',
            'data': {
                'id': self.item_id
            }
        }])[0]

    def attack_item(self, item_id):
        return self.CLIENT.set_action('attack', {'id': item_id})

    def move_to_point(self, coordinates):
        self.CLIENT.set_action('move', {'coordinates': coordinates})

    def subscribe(self, event, callback, data=None):
        return self.CLIENT.subscribe(event, callback, data)

    def unsubscribe_all(self):
        return self.subscribe('unsubscribe_all', None)

    def subscribe_im_in_area(self, center, radius, callback):
        return self.subscribe('im_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })

    def subscribe_any_item_in_area(self, center, radius, callback):
        return self.subscribe('any_item_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })

    def subscribe_im_stop(self, callback):
        return self.subscribe('im_stop', callback, {})

    def subscribe_im_idle(self, callback):
        return self.subscribe('im_idle', callback, {})

    def subscribe_enemy_in_my_firing_range(self, callback):
        return self.subscribe('enemy_in_my_firing_range', callback)

    def subscribe_the_item_out_my_firing_range(self, item_id, callback):
        return self.subscribe('the_item_out_my_firing_range', callback, {"item_id": item_id})

    def subscribe_the_item_is_dead(self, item_id, callback):
        return self.subscribe('death', callback, {'id': item_id})
