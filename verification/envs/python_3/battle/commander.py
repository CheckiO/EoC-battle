
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
        }])[0]

    def ask_nearest_enemy(self):
        return self.select([{
            'field': 'nearest_enemy',
            'data': {
                'id': self.initials['id']
            }
        }])[0]

    def ask_enemy_items_in_my_firing_range(self):
        return self.select([{
            'field': 'enemy_items_in_my_firing_range',
            'data': {
                'id': self.initials['id']
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

    def subscribe_enemy_in_my_firing_range(self, callback):
        return self.subscribe('enemy_in_my_firing_range', callback)

    def subscribe_the_item_out_my_firing_range(self, item_id, callback):
        return self.subscribe('the_item_out_my_firing_range', callback, {"item_id": item_id})

    def subscribe_the_item_is_dead(self, item_id, callback):
        return self.subscribe('death', callback, {'id': item_id})

