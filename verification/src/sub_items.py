from tools.distances import euclidean_distance
from tools.terms import ROLE, OPERATION


class BaseSubItem(object):
    def set_id(self, _id):
        self.id = _id
        self.is_dead = False


class RocketSubItem(BaseSubItem):
    type = 'rocket'
    def __init__(self, item, cur_coor, target_coor):
        self.speed = 1.5
        self.explode_radius = 1.5
        self.item = item
        self.cur_coor = cur_coor
        self.target_coor = target_coor
        self.damage_per_shot = self.item.total_damage

    def explode(self):
        self.is_dead = True
        for item in self.item._fight_handler.fighters.values():
            if item.player_id == self.item.player_id or not item.coordinates:
                continue

            distance = euclidean_distance(item.coordinates, self.cur_coor)
            if distance > self.explode_radius:
                continue

            damage = (self.explode_radius - distance) * self.damage_per_shot / self.explode_radius
            item.get_shot(damage)

    def do_frame_action(self):
        distance = euclidean_distance(self.cur_coor, self.target_coor)
        if distance <= self.speed:
            self.cur_coor = self.target_coor
            self.explode()
            return

        def calc_single_coor(cur, target):
            return (target - cur) * self.speed / distance + cur

        self.cur_coor = [
            calc_single_coor(self.cur_coor[0], self.target_coor[0]),
            calc_single_coor(self.cur_coor[1], self.target_coor[1])
        ]

    def output(self):
        return {
            'id': self.id,
            'coordinates': self.cur_coor,
            'is_dead': self.is_dead,
            'type': self.type
        }

class VerticalRocketSubItem(RocketSubItem):
    type = 'vert_rocket'
    def __init__(self, item, target_coor):
        operation = item.get_operation(OPERATION.ROCKET)
        self.timer = operation['timer']
        self.explode_radius = operation['radius']
        self.damage_per_shot = operation['damage']
        self.item = item
        self.cur_coor = target_coor
        self.target_coor = target_coor

    def do_frame_action(self):
        self.timer -= self.item._fight_handler.GAME_FRAME_TIME
        if self.timer <= 0:
            self.explode()

    def output(self):
        ret = super().output()
        ret['timer'] = self.timer
        return ret

class BaseTimeExtras:
    extra_damage = 0

    is_dead = False

    def __init__(self, power, timer):
        self.power = power
        self.timer = timer

    def do_frame_action(self, item):
        self.act(item)
        self.timer -= item._fight_handler.GAME_FRAME_TIME
        if self.timer<= 0:
            self.is_dead = True

    def act(item):
        pass

    def output(self):
        return {
            'type': self.type,
            'power': self.power,
            'timer': self.timer,
        }

class HealExtras(BaseTimeExtras):
    type = 'heal'

    def act(self, item):
        item.restore_health(self.power * item._fight_handler.GAME_FRAME_TIME)

class HealSubItem(BaseSubItem):
    type = 'heal'
    is_support = True
    def __init__(self, item, coor):
        operation = item.get_operation(OPERATION.HEAL)
        self.item = item
        self.timer = operation['time']
        self.radius = operation['radius']
        self.power = operation.get('power')
        self.coor = coor

    def output(self):
        return {
            'id': self.id,
            'coordinates': self.coor,
            'is_dead': self.is_dead,
            'type': self.type,
            'timer': self.timer
        }

    def act(self, item, power):
        item.add_extras(HealExtras(power, 0.3))

    def do_frame_action(self):
        for item in self.item._fight_handler.fighters.values():
            if not item.coordinates or (
                item.player_id == self.item.player_id and
                not self.is_support
            ) or (
                item.player_id != self.item.player_id and
                self.is_support
            ):
                continue

            distance = euclidean_distance(item.coordinates, self.coor)
            if distance > self.radius:
                continue

            self.act(item, self.power)

        self.timer -= self.item._fight_handler.GAME_FRAME_TIME
        if self.timer <= 0:
            self.is_dead = True


class PowerExtras(BaseTimeExtras):
    type = 'power'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_damage = self.power


class PowerSubItem(HealSubItem):
    type = 'power'

    def act(self, item, power):
        item.add_extras(PowerExtras(power, 0.3))


