import json
import config as cfg

def loadOR(orepo):
    try:
        file=orepo["file"]
        cfg.or_file = file
        with open(f"./{file}", 'r') as f:
            cfg.or_data = json.load(f)
    except:
        pass

def saveOR():
    with open(f"./{cfg.or_file}", 'w') as f:
        json.dump(cfg.or_data, f, indent=4)