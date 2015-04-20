
class Client(object):

    CLIENT = None

    def __init__(self):
        assert self.CLIENT
        self.initials = self.ask_initials()

    @classmethod
    def set_client(cls, client):
        cls.CLIENT = client

    def select(self, fields):
        return self.CLIENT.select(fields=fields)

    def ask_initials(self):
        return self.select([{
            'field': 'initials'
        }])

    def ask_nearest_enemy(self):
        return self.select([{
            'field': 'nearest_enemy',
            'data': {
                'id': self.initials['id']
            }
        }])

    def subscribe(self, event, callback, data=None):
        return self.CLIENT.subscribe(event, callback, data)

    def subscribe_item_in_range(self, callback, coordinates, range_value):
        return self.subscribe('item_in_range', callback, {
            'coordinates': coordinates,
            'range': range_value
        })

    def subscribe_item_in_my_range(self, callback):
        return self.subscribe('item_in_my_range', callback)

    def subscribe_death_item(self, item_id, callback):
        return self.subscribe('death', callback, {'id': item_id})

    def attack_item(self, item_id):
        return self.CLIENT.set_action('attack', {'id': item_id})
