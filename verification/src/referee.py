from checkio_referee import RefereeBase

import settings_env
from environment import BattleEnvironmentsController

from fight_handler import FightHandler







class Referee(RefereeBase):
    ENVIRONMENTS = settings_env.ENVIRONMENTS
    EDITOR_LOAD_ARGS = ('battle_info', 'action')
    HANDLERS = {
        'battle': FightHandler
    }

    @property
    def environments_controller(self):
        if not hasattr(self, '_environments_controller'):
            setattr(self, '_environments_controller', BattleEnvironmentsController(
                self.ENVIRONMENTS))
        return getattr(self, '_environments_controller')
