from tools.distances import euclidean_distance
from tools.terms import ROLE


class BaseSubItem(object):
    def set_id(self, _id):
        self.id = _id
        self.is_dead = False


class RocketSubItem(BaseSubItem):
    def __init__(self, item, cur_coor, target_coor):
        self.speed = 1.5
        self.explode_radius = 1.5
        self.item = item
        self.cur_coor = cur_coor
        self.target_coor = target_coor

    def explode(self):
        self.is_dead = True

        for item in self.item._fight_handler.fighters.values():
            if item.role != ROLE.UNIT or item == self.item:
                continue

            distance = euclidean_distance(item.coordinates, self.cur_coor)
            if distance > self.explode_radius:
                continue

            damage = (self.explode_radius - distance) * self.item.damage_per_shot
            item.get_shoted(damage)

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
            'is_dead': self.is_dead
        }
