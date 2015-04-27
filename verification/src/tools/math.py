
def distance_to_point(point1, point2):
    '''
        point1 and point2 are list of two values X and Y for two dimension coordinate
    '''
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
