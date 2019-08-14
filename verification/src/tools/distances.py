__all__ = ["euclidean_distance", "manhattan_distance", "in_correct"]


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


def in_correct_distance(event_item, receiver, desired_distance):
    if desired_distance > receiver.firing_range:
        return False
    distance_to_enemy = euclidean_distance(receiver.coordinates, event_item.coordinates) - event_item.size / 2
    if distance_to_enemy > desired_distance:
        return False
    return True


def in_correct_percentage(event_item, receiver, desired_percentage):
    hit_success_percentage = 0
    distance_to_enemy = euclidean_distance(receiver.coordinates, event_item.coordinates) - event_item.size / 2
    if distance_to_enemy > receiver.firing_range:
        return False

    if receiver.firing_range_always_hit is None:
        if distance_to_enemy <= receiver.firing_range:
            hit_success_percentage = 100
    else:
        if distance_to_enemy <= receiver.firing_range_always_hit:
            hit_success_percentage = 100
        elif distance_to_enemy <= receiver.firing_range:
            normalized_full_distance = receiver.firing_range - receiver.firing_range_always_hit
            normalized_enemy_distance = distance_to_enemy - receiver.firing_range_always_hit
            hit_success_percentage = 100 - int(
                (normalized_enemy_distance * (100 - receiver.start_chance)) / normalized_full_distance)
            print(hit_success_percentage)

    return hit_success_percentage >= desired_percentage


def in_correct(event_item, receiver, event_data):
    if receiver.firing_range is None:
        return False

    if receiver.player_id == event_item.player_id:
        return False

    if event_data is not None:
        if 'distance' in event_data and event_data['distance'] is not None:
            return in_correct_distance(event_item, receiver, event_data['distance'])
        elif 'percentage' in event_data and event_data['percentage'] is not None:
            return in_correct_percentage(event_item, receiver, event_data['percentage'])
    return in_correct_distance(event_item, receiver, receiver.firing_range)
