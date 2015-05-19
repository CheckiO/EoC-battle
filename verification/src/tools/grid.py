__all__ = ["fill_square", "find_route", "straighten_route", "grid_to_graph"]

from heapq import heappop, heappush
from .distances import euclidean_distance
from itertools import product
from fractions import Fraction
from collections import defaultdict

SQRT_2 = round(2 ** 0.5, 3)
HEURISTIC = euclidean_distance

DIRS = (
    (-1, 0, 1),
    (1, 0, 1),
    (0, 1, 1),
    (0, -1, 1),
    # (-1, 1, SQRT_2),
    # (1, -1, SQRT_2),
    # (-1, -1, SQRT_2),
    # (1, 1, SQRT_2),
)


def fill_square(matrix: list, row: int, column: int, size: int, fill_element=1) -> list:
    """
    Fill square area of the matrix with the given element.
    !!! This method is not a pure function and change a given matrix.

    :param matrix: A matrix where area are filling
    :param row: top-left corner row
    :param column: top-left corner column
    :param size: size of area for filling
    :param fill_element: An element which will be inserted
    :return: The changed matrix
    """
    row, column = round(row), round(column)
    height, width = len(matrix), len(matrix[0]) if matrix else 0
    for i in range(max(row, 0), min(row + size, height)):
        for j in range(max(column, 0), min(column + size, width)):
            matrix[i][j] = fill_element
    return matrix


def grid_to_graph(grid):
    """
    Transform a grid of a map to the graph

    :param grid: A matrix of the map
    :return: The graph as a dict where keys are tuples of coordinates and
    values are a sequence of neighbours.
    """
    height, width = len(grid), len(grid[0]) if grid else 0
    graph = defaultdict(tuple)
    for i, row in enumerate(grid):
        for j, el in enumerate(row):
            south_flag = east_flag = west_flag = False
            if not el:
                continue
            if i < height - 1 and grid[i + 1][j]:
                graph[(i, j)] += ((i + 1, j, 1),)
                graph[(i + 1, j)] += ((i, j, 1),)
                south_flag = True
            if j < width - 1 and grid[i][j + 1]:
                graph[(i, j)] += ((i, j + 1, 1),)
                graph[(i, j + 1)] += ((i, j, 1),)
                east_flag = True
            if j > 0 and grid[i][j - 1]:
                west_flag = True
            if south_flag and east_flag and grid[i + 1][j + 1]:
                graph[(i, j)] += ((i + 1, j + 1, SQRT_2),)
                graph[(i + 1, j + 1)] += ((i, j, SQRT_2),)
            if south_flag and west_flag and grid[i + 1][j - 1]:
                graph[(i, j)] += ((i + 1, j - 1, SQRT_2),)
                graph[(i + 1, j - 1)] += ((i, j, SQRT_2),)
    return graph


def get_neighbours(grid: list, cell: tuple):
    x, y = cell
    max_x, max_y = len(grid), len(grid[0]) if grid else 0
    result = []
    for dx, dy, cost in DIRS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < max_x and 0 <= ny < max_y and grid[nx][ny]:
            result.append(((nx, ny), cost))
    return result


def find_possible_end(grid, goal):
    result = set()
    radius = 1
    while not result:
        for dx, dy in product(range(-radius, radius + 1), repeat=2):
            nx, ny = goal[0] + dx, goal[1] + dy
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and grid[nx][ny]:
                result.add((nx, ny))
        radius += 1
    return result


def find_route(grid, graph, start_cell, end_cell):
    """
    Find a route in a grid with A* search.
    If end cell are not available then search a path to near positions.

    :param grid: a matrix to search
    :param start_cell: start position
    :param end_cell: goal cell
    :return: A route as a tuple of coordinates.
    """
    heap = []
    start_cell = tuple(start_cell)
    end_cell = tuple(end_cell)
    if not grid[end_cell[0]][end_cell[1]]:
        goals = find_possible_end(grid, end_cell)
    else:
        goals = {tuple(end_cell)}
    # priority, distance, path, cell
    heappush(heap, (0, 0, (start_cell,), start_cell))
    visited = set()
    count = 0
    while heap:
        _, distance, path, current = heappop(heap)
        count += 1
        if current in visited:
            continue
        visited.add(current)
        if current in goals:
            return path
        for nx, ny, cost in graph[current]:
            neighbour = (nx, ny)
            if neighbour in visited:
                continue
            priority = distance + HEURISTIC((nx, ny), end_cell)
            heappush(heap, (priority, distance + cost, path + (neighbour,), neighbour))
    return ()


def straighten_route(grid, route):
    """
    With visibility algorithm detect which part can be straighten

    Precondition:
    In the route all adjacent elements are visible each other


    :param grid: A matrix with the map
    :param route: a route in the map between two cells
    :return: the straightened route
    """

    def binary_straighten(left, right):
        if left == right or cell_visibility(grid, route[left], route[right]):
            return [route[left], route[right]]
        middle = (left + right) // 2
        return binary_straighten(left, middle)[:-1] + binary_straighten(middle, right)

    route = binary_straighten(0, len(route) - 1)
    to_index = 2
    result = [route[0]]
    while to_index < len(route):
        if not cell_visibility(grid, result[-1], route[to_index]):
            result.append(route[to_index - 1])
        to_index += 1
    result.append(route[-1])
    return result


def cell_visibility(grid, start, end):
    """
    Check visibility between cells
    Using http://lifc.univ-fcomte.fr/home/~ededu/projects/bresenham/ algorithm

    :param grid: A matrix with the map
    :param start: First cell
    :param end: Second cell
    :return:
    """
    sx, sy = start[0] + Fraction(1, 2), start[1] + Fraction(1, 2)
    ex, ey = end[0] + Fraction(1, 2), end[1] + Fraction(1, 2)
    steps_x = int(abs(ex - sx)) * 2
    steps_y = int(abs(ey - sy)) * 2
    # TODO: this is not DRY
    if ex - sx:
        dx = ((ex - sx) / abs(ex - sx)) * Fraction(1, 2)
        dy = Fraction(ey - sy, 2 * (abs(ex - sx)))
        for i in range(1, steps_x):
            tx = sx + i * dx
            ty = sy + i * dy
            if not grid[int(tx)][int(ty)]:
                return False
            if i % 2 and not grid[int(tx) - 1][int(ty)]:
                return False
            if tx == int(tx) and ty == int(ty) and not grid[int(tx) - 1][int(ty) - 1]:
                return False
    if ey - sy:
        dy = ((ey - sy) / abs(ey - sy)) * Fraction(1, 2)
        dx = Fraction(ex - sx, 2 * (abs(ey - sy)))
        for i in range(1, steps_y):
            tx = sx + i * dx
            ty = sy + i * dy
            if not grid[int(tx)][int(ty)]:
                return False
            if i % 2 and not grid[int(tx)][int(ty) - 1]:
                return False
    return True
