import json

FILE_BALANCE = '/opt/balance/balance.json'

with open(FILE_BALANCE) as fh:
    BALANCE = json.load(fh)


def building_display_stats(building, level):
    bb = BALANCE['buildings'][building]
    ret = {}
    ret.update(bb['stats'][level-1]['display'])
    ret['size'] = bb['size']['x']
    ret['role'] = bb['role']
    return ret


def unit_display_stats(unit, level):
    bb = BALANCE['units'][unit]
    ret = {}
    ret.update(bb['stats'][level-1])
    ret['role'] = 'unit'
    return ret


def operation_stats(action, level):
    if not level:
        return None
    return BALANCE['units'][action]['stats'][level-1]


def module_stats(module):
    # TODO: just-for-testing
    if module == 'u.damagePerSecond.lvl1':
        return {
            "type": "tower",
            "chance": "common",
            "damagePerSecond.pr": 10
        }
    elif module == 'u.chargingTime.lvl1':
        return {
            "type": "tower",
            "chance": "common",
            "chargingTime.pr": 10
        }
    elif module == 'u.rocketSpeed.lvl1':
        return {
            "type": "tower",
            "chance": "common",
            "rocketSpeed.pr": 10
        }
    elif module == 'landing.Shift.lvl1':
        return {
            "type": "tower",
            "chance": "common",
            "landingShift": 1
        }
    elif module == 'landing':
        return {
            "type": "unit",
            "chance": "common",
            "landing": 1
        }
    elif module == 'groupProtection':
        return {
            "type": "unit",
            "chance": "common",
            "groupProtect": 1
        }
    elif module == 'heavyProtection':
        return {
            "type": "unit",
            "chance": "common",
            "heavyProtect": 1
        }
    elif module == 'freezeShot':
        return {
            "type": "tower",
            "chance": "common",
            "freezeShot": 1
        }
    elif module == 'pierceShot':
        return {
            "type": "tower",
            "chance": "common",
            "pierceShot": 1
        }
    return BALANCE['modules'][module]
