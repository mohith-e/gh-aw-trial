"""Clean module: valid on 3.9, imports a pinned third-party package."""
import pandas as pd


def total(rows):
    return pd.DataFrame(rows).sum().to_dict()
