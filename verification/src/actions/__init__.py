from .center import CenterActions
from .defence import DefenceActions, DefenceRocketActions
from .unit import UnitActions, CraftActions, FlagActions, MineActions
from .building import BuildingActions
from .obstacle import ObstacleActions
from tools import ROLE, DEF_TYPE

ACTIONS = {
    ROLE.UNIT: UnitActions,
    ROLE.TOWER: {
        DEF_TYPE.SENTRY: DefenceActions,
        DEF_TYPE.MACHINE: DefenceActions,
        DEF_TYPE.ROCKET: DefenceRocketActions
    },
    ROLE.CENTER: CenterActions,
    ROLE.BUILDING: BuildingActions,
    ROLE.OBSTACLE: ObstacleActions,
    ROLE.CRAFT: CraftActions,
    ROLE.FLAGMAN: FlagActions,
    ROLE.MINE: MineActions,
}


class ItemActions(object):

    @staticmethod
    def get_factory(item, fight_handler):
        unit_role = item.role
        action_class = ACTIONS[unit_role]
        if isinstance(action_class, dict):
            action_class = action_class[item.item_type]
        return action_class(item, fight_handler)
