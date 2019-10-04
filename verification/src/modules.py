from tools.balance import module_stats
from tools.terms import FEATURE


class BaseFeature(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def apply(self, item):
        pass


class ChangeStatsBaseFeature(object):
    IS_POSITIVE = True

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def apply(self, item):
        pass


class IncreaseStats(ChangeStatsBaseFeature):
    stat_names = None

    def apply(self, item):
        for stat_name in self.stat_names:
            if not hasattr(item, stat_name):
                return
            stat_value = getattr(item, stat_name)
            if self.IS_POSITIVE:
                new_value = self.value + stat_value
            else:
                new_value = self.value - stat_value
            setattr(item, stat_name, new_value)


class PrIncreaseStats(ChangeStatsBaseFeature):
    stat_names = None

    def apply(self, item):
        for stat_name in self.stat_names:
            if not hasattr(item, stat_name):
                return
            stat_value = getattr(item, stat_name)
            if self.IS_POSITIVE:
                new_value = (100 + self.value) * stat_value / 100
            else:
                new_value = (100 - self.value) * stat_value / 100
            setattr(item, stat_name, new_value)


class Speed(PrIncreaseStats):
    stat_names = ['speed']


class RocketSpeed(PrIncreaseStats):
    stat_names = ['rocket_speed']


class ChargingTime(PrIncreaseStats):
    IS_POSITIVE = False
    stat_names = ['charging_time']


class FiringRange(PrIncreaseStats):
    stat_names = ['firing_range']


class DamagePerSecond(PrIncreaseStats):
    stat_names = ['damage_per_second']


class DamagePerShot(PrIncreaseStats):
    stat_names = ['damage_per_shot']


class HitPoints(PrIncreaseStats):
    stat_names = ['hit_points', 'start_hit_points']


class LandingShift(IncreaseStats):
    stat_names = ['landing_shift']


FEATURES = {
    'speed.pr': Speed,
    'rocketSpeed.pr': RocketSpeed,
    'fireRange.pr': FiringRange,
    'chargingTime.pr': ChargingTime,
    'damagePerSecond.pr': DamagePerSecond,
    'damagePerShot.pr': DamagePerShot,
    'hitPoints.pr': HitPoints,
    'landingShift': LandingShift,

    FEATURE.LANDING: BaseFeature,
    FEATURE.TELEPORT: BaseFeature,
    FEATURE.FREEZE_SHOT: BaseFeature,
    FEATURE.PIERCE_SHOT: BaseFeature,
    FEATURE.GROUP_PROTECT: BaseFeature,
    FEATURE.HEAVY_PROTECT: BaseFeature,
}


def gen_features(modules):
    ret = []
    for module in modules:
        for f_name, f_value in module_stats(module).items():
            if f_name not in FEATURES:
                continue
            ret.append(FEATURES[f_name](f_name, f_value))
    return ret


def map_features(features, func_name, *args, **kwargs):
    if not features:
        return []
    for feature in features:
        getattr(feature, func_name)(*args, **kwargs)

        
def has_feature(features, name):
    return any(map(lambda a: a.name == name, features))
