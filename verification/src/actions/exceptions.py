class ActionError(Exception):
    pass


class ActionValidateError(ActionError):
    pass

class ActionSkip(Exception):
    pass
