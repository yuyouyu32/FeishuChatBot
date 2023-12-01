import pandas as pd
import ahocorasick_rs

#!/usr/bin/env python3.8
class Obj(dict):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [Obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Obj(b) if isinstance(b, dict) else b)

def dict_2_obj(d: dict):
    return Obj(d)


def insert_dataframe_to_tree_rs(df: pd.DataFrame):
    all_dirty_word = []
    for column in df.columns:
        data = df[column].dropna().values
        all_dirty_word.extend(list(map(str, data)))
            
    actree = ahocorasick_rs.AhoCorasick(all_dirty_word)
    return actree

DirtyWord = pd.read_excel('/mnt_data/dirty_word/DirtyWord.xlsx')
ActreeDirty = insert_dataframe_to_tree_rs(DirtyWord)

