__all__ = ["euclidean_distance", "manhattan_distance"]


def euclidean_distance(point1, point2):
    """
        point1 and point2 are list of two values X and Y for two dimension coordinate
    """
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


def manhattan_distance(point1, point2):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])
