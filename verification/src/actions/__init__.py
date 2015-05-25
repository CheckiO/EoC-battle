from .center import CenterActions
from .defence import DefenceActions
from .unit import UnitActions
from .building import BuildingActions
from .obstacle import ObstacleActions
from tools import ROLE

class ItemActions(object):

    @staticmethod
    def get_factory(item, fight_handler):
        unit_role = item.role
        return {
            ROLE.UNIT: UnitActions,
            ROLE.TOWER: DefenceActions,
            ROLE.CENTER: CenterActions,
            ROLE.BUILDING: BuildingActions,
            ROLE.OBSTACLE: ObstacleActions
        }[unit_role](item, fight_handler)
