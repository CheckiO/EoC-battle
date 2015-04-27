from .center import CenterActions
from .defence import DefenceActions
from .unit import UnitActions


class ItemActions(object):

    @staticmethod
    def get_factory(item, fight_handler):
        unit_type = item.type
        return {
            'unit': UnitActions,
            'defender': DefenceActions,
            'center': CenterActions,
        }[unit_type](item, fight_handler)
