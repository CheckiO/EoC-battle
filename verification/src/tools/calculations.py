__all__ = ["in_firing_range"]

from .distances import euclidean_distance


def in_firing_range_by_distance(event_item, receiver, desired_distance):
    if desired_distance > receiver.firing_range:
        return False
    distance_to_enemy = euclidean_distance(receiver.coordinates, event_item.coordinates) - event_item.size / 2
    if distance_to_enemy > desired_distance:
        return False
    return True


def in_firing_range_by_percentage(event_item, receiver, desired_percentage):
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


def in_firing_range(event_item, receiver, event_data):
    if receiver.firing_range is None:
        return False

    if receiver.player_id == event_item.player_id:
        return False

    if event_data is not None:
        if 'distance' in event_data and event_data['distance'] is not None:
            return in_firing_range_by_distance(event_item, receiver, event_data['distance'])
        elif 'percentage' in event_data and event_data['percentage'] is not None:
            return in_firing_range_by_percentage(event_item, receiver, event_data['percentage'])
    return in_firing_range_by_distance(event_item, receiver, receiver.firing_range)
