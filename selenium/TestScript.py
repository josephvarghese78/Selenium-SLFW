import json
import config as cfg

def loadtest(file):
    try:
        with open(f"./{file}", 'r') as f:
            cfg.testScript = json.load(f)
    except:
        pass