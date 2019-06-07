import json

FILE_BALANCE = '/opt/balance/balance.json'

with open(FILE_BALANCE) as fh:
    BALANCE = json.load(fh)

def building_display_stats(building, level):
    bb = BALANCE['buildings'][building]
    ret = {}
    ret.update(bb['stats'][level-1]['display'])
    ret['size'] = bb['size']['x']
    ret['rule'] = bb['rule']
    return ret

def unit_display_stats(unit, level):
    bb = BALANCE['units'][unit]
    ret = {}
    ret.update(bb['stats'][level-1])
    ret['rule'] = 'unit'
    return ret