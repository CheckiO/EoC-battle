from .center import CenterActions
from .defence import DefenceSentryActions, DefenceMachineActions, DefenceRocketActions
from .unit import CraftActions, FlagActions, MineActions, InfantryBotActions, HeavyBotActions, RocketBotActions
from .building import BuildingActions
from .obstacle import ObstacleActions
from tools import ROLE, DEF_TYPE, ATTACK_TYPE


ACTIONS = {
    ROLE.UNIT: {
        ATTACK_TYPE.INFANTRY: InfantryBotActions,
        ATTACK_TYPE.HEAVY: HeavyBotActions,
        ATTACK_TYPE.ROCKET_BOT: RocketBotActions
    },
    ROLE.TOWER: {
        DEF_TYPE.SENTRY: DefenceSentryActions,
        DEF_TYPE.MACHINE: DefenceMachineActions,
        DEF_TYPE.ROCKET_GUN: DefenceRocketActions
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
