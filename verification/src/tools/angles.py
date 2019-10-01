__all__ = ['angle_between_center_vision_and_enemy', 'angle_to_enemy', 'shortest_distance_between_angles']

import math


def vector_length(vector):
    """
    Calculate Length of vector

    :param vector: Vector
    :return: Length of vector
    """
    return (vector[0] ** 2 + vector[1] ** 2) ** 0.5


def normalized_vector(vector):
    """
    Calculate Normalized vector

    :param vector: Vector
    :return: Normalized vector
    """
    length = vector_length(vector)
    return vector[0] / length, vector[1] / length


def normalized_angle(angle):
    return (-1) * (angle + 90) % 360


def shortest_distance_between_angles(new_angle, current_angle):
    """
    Calculate Difference Between angles on a circle

    :param new_angle: New angle of turn
    :param current_angle: Current angle of turn
    :return: the difference between turns in degrees
    """
    return int((new_angle - current_angle + 540) % 360 - 180)


def angle_to_enemy(coordinates, enemy_coordinates):
    """
    Calculate angle to the center of the object's vision

    :param coordinates: Coordinates of object
    :param enemy_coordinates: Coordinates of enemy
    :return: angle to the center of the object's vision
    """

    angle_vector = (enemy_coordinates[0] - coordinates[0], enemy_coordinates[1] - coordinates[1])
    angle = math.degrees(math.atan2((-1) * angle_vector[0], angle_vector[1]))
    if angle < 0:
        angle = 360 + angle
    return normalized_angle(angle)


def angle_between_center_vision_and_enemy(coordinates, angle, enemy_coordinates):
    """
    Calculate angle between the center of the object's vision and the enemy.

    :param coordinates: Coordinates of object
    :param angle: Angle of object's vision
    :param enemy_coordinates: Coordinates of enemy
    :return: angle between the center of the object's vision and the enemy
    """
    angle = normalized_angle(angle)
    angle_radians = math.radians(angle)
    angle_vector = [coordinates[0] - math.sin(angle_radians), coordinates[1] + math.cos(angle_radians)]

    path_angle_vector = [angle_vector[0] - coordinates[0], angle_vector[1] - coordinates[1]]
    normalized_path_angle_vector = normalized_vector(path_angle_vector)

    path_enemy_vector = [enemy_coordinates[0] - coordinates[0], enemy_coordinates[1] - coordinates[1]]
    normalized_path_enemy_vector = normalized_vector(path_enemy_vector)

    dot = (normalized_path_angle_vector[0] * normalized_path_enemy_vector[0] +
           normalized_path_angle_vector[1] * normalized_path_enemy_vector[1])
    angle = math.degrees(math.acos(dot))
    return angle
