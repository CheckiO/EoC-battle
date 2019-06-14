from tools.balance import module_stats
from tools.terms import FEATURE

class BaseFeature:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def apply(self, item):
        pass

class PrIncreaseStats(BaseFeature):
    stat_names = None

    def apply(self, item):
        for stat_name in self.stat_names:
            stat_value = getattr(item, stat_name)
            setattr(item, stat_name, stat_value + (100 + self.value) * stat_value / 100)

class RateOfFire(PrIncreaseStats):
    stat_names = ['rate_of_fire']

class Speed(PrIncreaseStats):
    stat_names = ['speed']

class FireRange(PrIncreaseStats):
    stat_names = ['firing_range']

class DamagePerShot(PrIncreaseStats):
    stat_names = ['damage_per_shot']

class HitPoints(PrIncreaseStats):
    stat_names = ['hit_points', 'start_hit_points']

FEATURES = {
    'rateOfFire.pr': RateOfFire,
    'speed.pr': Speed,
    'fireRange.pr': FireRange,
    'damagePerShot.pr': DamagePerShot,
    'hitPoints.pr': HitPoints,
    FEATURE.TELEPORT: BaseFeature
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

