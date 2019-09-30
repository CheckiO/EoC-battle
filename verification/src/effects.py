from tools.terms import EFFECT, FEATURE


class BaseEffect(object):
    type = None
    is_dead = False

    def __init__(self, timer, power):
        self.timer = timer
        self.power = power

    def output(self):
        return {
            'type': self.type,
            'timer': self.timer,
            'power': self.power,
            'is_dead': self.is_dead,
        }

    def apply_effect(self, item):
        pass

    def discard_effect(self, item):
        pass

    def do_frame_action(self, item):
        self.apply_effect(item)

        self.timer -= item._fight_handler.GAME_FRAME_TIME

        if self.timer <= 0:
            self.is_dead = True


class FrozenEffect(BaseEffect):
    type = EFFECT.FREEZE

    def apply_effect(self, item):
        item.speed = (100 - self.power) * item.original_speed / 100

    def discard_effect(self, item):
        item.speed = item.original_speed


FEATURE_EFFECTS = {
    FEATURE.FREEZE_SHOT: [FrozenEffect],
}


def gen_effects(features):
    TIMER = 2
    POWER = 10

    ret = []
    for feature in features:
        if feature.name not in FEATURE_EFFECTS:
            continue
        for effect in FEATURE_EFFECTS[feature.name]:
            ret.append(effect(TIMER, POWER))
    return ret