__all__ = ["euclidean_distance", "manhattan_distance"]


def euclidean_distance(point1, point2):
    """
    Calculate Euclidean distance as hypotenuse -- straight line.

    :param point1: Coordinates of the first point
    :param point2: Coordinates of the second point
    :return: the distance as a float or an integer
    """
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


def manhattan_distance(point1, point2):
    """
    Calculate Manhattan distance.

    :param point1: Coordinates of the first point
    :param point2: Coordinates of the second point
    :return: the distance as a float or an integer
    """
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])
