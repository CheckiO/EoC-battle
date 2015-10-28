from .terms import OUTPUT as O
from copy import deepcopy

CUT_FROM_BUILDING = 1

# Try to keep it even
FIELD_SIZE = 40


class KEY():
    SIZE = "size"
    TYPE = "type"
    POSITION = "position"
    STATUS = "status"
    HIT_POINTS = "hit_points"
    BUILDINGS = "buildings"
    UNITS = "units"
    OBSTACLES = "obstacles"

# Types
STATIC = "static"
MOBILE = "mobile"

# Statuses
IDLE = "idle"
MOVE = "move"


class Grid():
    RINGS = tuple(tuple((x, y) for x in range(-k, k + 1) for y in range(-k, k + 1) if
                        abs(x) == k or abs(y) == k)
                  for k in range(10))

    SCALE = 2
    CELL_SHIFT = 0.5 / SCALE

    def __init__(self, rows, columns=None):
        columns = columns or rows
        self.__init_size = rows, columns
        self.height = self.scale(rows)
        self.width = self.scale(columns)
        self._grid = [[0 for _ in range(self.width)] for __ in range(self.height)]

    @classmethod
    def scale(cls, n):
        return round(n * cls.SCALE)

    @classmethod
    def unscale_shift(cls, n):
        return n / cls.SCALE + cls.CELL_SHIFT

    @classmethod
    def scale_shift(cls, n):
        return round((n - cls.CELL_SHIFT) * cls.SCALE)

    @classmethod
    def align(cls, n):
        pass

    def fill_square_zone(self, left_top, size, fill=1):
        x, y = map(self.scale, left_top, )
        scale_size = self.scale(size)
        for i in range(x, x + scale_size):
            for j in range(y, y + scale_size):
                self._grid[i][j] = fill

    def fill_unit(self, position, fill=1):
        x, y = map(self.scale_shift, position)
        self._grid[x][y] = fill

    def copy(self):
        copy_field = Grid(*self.__init_size)
        copy_field._grid = [row[:] for row in self._grid]
        return copy_field

    def is_filled(self, position):
        x, y = map(self.scale_shift, position)
        return bool(self._grid[x][y])

    def fill_nearest_free_cell(self, position, fill=1):
        x, y = map(self.scale_shift, position)
        for ring in self.RINGS:
            for dx, dy in ring:
                nx, ny = dx + x, dy + y
                if 0 <= nx < self.height and 0 <= ny < self.width and not self._grid[nx][ny]:
                    self._grid[nx][ny] = 1
                    return self.unscale_shift(nx), self.unscale_shift(ny)
        return position


def is_unit_stand(state):
    return state[KEY.STATUS] != MOVE


def buildings_init_state(log):
    buildings = {}
    for b in log[O.INITIAL_CATEGORY][O.BUILDINGS]:
        buildings[b[O.ID]] = {
            KEY.SIZE: b[O.SIZE] - CUT_FROM_BUILDING,
            KEY.POSITION: [b[O.TILE_POSITION][0] + CUT_FROM_BUILDING / 2,
                           b[O.TILE_POSITION][0] + CUT_FROM_BUILDING / 2]}
    return buildings


def units_init_state(log):
    units = {}
    for u in log[O.INITIAL_CATEGORY][O.UNITS]:
        units[u[O.ID]] = {KEY.POSITION: u[O.TILE_POSITION], KEY.STATUS: IDLE}
    return units


def unit_dispersion(log):
    # Now we can change "log" as we want
    log = deepcopy(log)

    buildings = buildings_init_state(log)
    units = units_init_state(log)

    # Create a grid with permanent elements
    init_field = Grid(FIELD_SIZE)
    for ob in log[O.INITIAL_CATEGORY][O.OBSTACLES]:
        init_field.fill_square_zone(ob[O.TILE_POSITION], ob[O.SIZE])

    for frame in log[O.FRAME_CATEGORY]:
        prev_units = deepcopy(units)
        field = init_field.copy()
        moving_units, stopped_units = [], []
        for item in frame:
            item_id = item[O.ID]
            if item_id in buildings and item[O.HIT_POINTS_PERCENTAGE]:
                b = buildings[item_id]
                field.fill_square_zone(b[KEY.POSITION], b[KEY.SIZE])
            if item_id in units:
                units[item_id][KEY.STATUS] = item[O.ITEM_STATUS]
                if not item[O.HIT_POINTS_PERCENTAGE]:
                    continue
                if is_unit_stand(units[item_id]):
                    if is_unit_stand(prev_units[item_id]):
                        field.fill_unit(units[item_id][KEY.POSITION])
                        item[O.TILE_POSITION] = prev_units[item_id][KEY.POSITION]
                    else:
                        stopped_units.append(item)
                else:
                    moving_units.append(item)

        for item in stopped_units:
            item_real_position = item[O.TILE_POSITION]
            item_id = item[O.ID]
            units[item_id][KEY.POSITION] = field.fill_nearest_free_cell(item_real_position)
            item[O.TILE_POSITION] = units[item_id][KEY.POSITION]

        for item in moving_units:
            units[item[O.ID]][KEY.POSITION] = item[O.TILE_POSITION]

    return log
#
# if __name__ == "__main__":
#     import json
#     data = json.load(open("./test.json"))
#     new_data = unit_dispersion(data)
#     json.dump(new_data, open("./res.json", "w"))
#     for o, n in zip(data["frames"], new_data["frames"]):
#         for x, y in zip(o, n):
#             if x != y:
#                 print("-----------")
#                 print(x)
#                 print(y)