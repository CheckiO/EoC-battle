from battle import ROLE, PARTY


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

    def ask(self, fields):
        return self.CLIENT.select(fields=[fields])[0]
    select = ask

    def ask_my_info(self):
        return self.ask(
            {
                'field': 'my_info'
            })

    def ask_item_info(self, item_id):
        return self.ask(
            {
                'field': 'item_info',
                'data': {
                    "id": item_id
                }
            })

    def ask_items(self, parties=PARTY.ALL, roles=ROLE.ALL):
        return self.ask(
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
        return self.ask(
            {
                'field': 'players',
                'data': {
                    PARTY.REQUEST_NAME: parties
                }
            })

    def ask_enemy_players(self):
        return self.ask_players(parties=(PARTY.ENEMY,))

    def ask_nearest_enemy(self):
        return self.ask(
            {
                'field': 'nearest_enemy',
                'data': {
                    'id': self.item_id
                }
            })

    def ask_my_range_enemy_items(self):
        return self.ask(
            {
                'field': 'enemy_items_in_my_firing_range',
                'data': {
                    'id': self.item_id
                }
            })
    ask_enemy_items_in_my_firing_range = ask_my_range_enemy_items

    def do(self, action, data):
        return self.CLIENT.set_action(action, data)

    def do_attack(self, item_id):
        return self.do('attack', {'id': item_id})
    attack_item = do_attack

    def do_move(self, coordinates):
        return self.do('move', {'coordinates': coordinates})
    move_to_point = do_move

    def when(self, event, callback, data=None):
        return self.CLIENT.subscribe(event, callback, data)
    subscribe = when

    def unsubscribe_all(self):
        return self.when('unsubscribe_all', None)

    def when_in_area(self, center, radius, callback):
        return self.when('im_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })
    subscribe_im_in_area = when_in_area

    def when_item_in_area(self, center, radius, callback):
        return self.when('any_item_in_area', callback, {
            'coordinates': center,
            'radius': radius
        })
    subscribe_any_item_in_area = when_item_in_area

    def when_stop(self, callback):
        return self.when('im_stop', callback, {})
    subscribe_im_stop = when_stop

    def when_idle(self, callback):
        return self.when('im_idle', callback, {})
    subscribe_im_idle = when_idle

    def when_enemy_in_range(self, callback):
        return self.when('enemy_in_my_firing_range', callback)
    subscribe_enemy_in_my_firing_range = when_enemy_in_range

    def when_enemy_out_range(self, item_id, callback):
        return self.when('the_item_out_my_firing_range', callback, {"item_id": item_id})
    subscribe_the_item_out_my_firing_range = when_enemy_out_range

    def when_item_destroyed(self, item_id, callback):
        return self.when('death', callback, {'id': item_id})
    subscribe_the_item_is_dead = when_item_destroyed
