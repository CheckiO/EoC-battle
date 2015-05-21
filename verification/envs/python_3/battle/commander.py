class PARTY():
    REQUEST_NAME = 'parties'
    MY = "my"
    ENEMY = "enemy"
    ALL = (MY, ENEMY)


class ROLE():
    REQUEST_NAME = "roles"
    CENTER = "center"
    TOWER = "tower"
    UNIT = "unit"
    BUILDING = 'building'
    OBSTACLE = "obstacle"
    ALL = (CENTER, TOWER, UNIT, BUILDING, OBSTACLE)


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
        return self.CLIENT.select(fields=[fields])[0]

    def ask_my_info(self):
        return self.select(
            {
                'field': 'my_info'
            })

    def ask_item_info(self, item_id):
        return self.select(
            {
                'field': 'item_info',
                'data': {
                    "id": item_id
                }
            })

    def ask_items(self, parties=PARTY.ALL, roles=ROLE.ALL):
        return self.select(
            {
                'field': 'items',
                'data': {
                    PARTY.REQUEST_NAME: parties,
                    ROLE.REQUEST_NAME: roles
                }
            })

    def ask_enemy_items(self):
        return self.ask_items(parties=(PARTY.ENEMY,))

    def ask_my_items(self):
        return self.ask_items(parties=(PARTY.MY,))

    def ask_buildings(self):
        return self.ask_items(roles=(ROLE.CENTER, ROLE.BUILDING))

    def ask_towers(self):
        return self.ask_items(roles=(ROLE.TOWER,))

    def ask_center(self):
        centers = self.ask_items(roles=(ROLE.CENTER,))
        return centers[0] if centers else None

    def ask_units(self):
        return self.ask_items(roles=(ROLE.UNIT,))

    def ask_players(self, parties=PARTY.ALL):
        return self.select(
            {
                'field': 'players',
                'data': {
                    PARTY.REQUEST_NAME: parties
                }
            })

    def ask_enemy_players(self):
        return self.ask_players(parties=(PARTY.ENEMY,))

    def ask_nearest_enemy(self):
        return self.select(
            {
                'field': 'nearest_enemy',
                'data': {
                    'id': self.item_id
                }
            })

    def ask_enemy_items_in_my_firing_range(self):
        return self.select(
            {
                'field': 'enemy_items_in_my_firing_range',
                'data': {
                    'id': self.item_id
                }
            })

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
