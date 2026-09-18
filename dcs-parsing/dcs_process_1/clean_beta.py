"""Clean module: stdlib only, no pins involved."""
import json


def load(path):
    with open(path) as fh:
        return json.load(fh)
