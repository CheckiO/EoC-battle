__all__ = ['landing_position_shifts']


def landing_position_shifts(max_length=None):
    if max_length is None:
        max_length = 3

    x_coordinate = - 0.1
    coordinates = [[x_coordinate, 0]]

    positive_coordinate = 0
    negative_coordinate = 0
    while positive_coordinate < max_length:
        positive_coordinate += 0.5
        coordinates.append([x_coordinate, positive_coordinate])
        negative_coordinate -= 0.5
        coordinates.append([x_coordinate, negative_coordinate])

    return coordinates
