# import list typing
import pandas as pd
# from types import List


def fmt_text_field(
        df: pd.DataFrame, 
        col_name: str,
        replaces: list = [],  #TODO - fix this type
        max_width: int = None,
        max_height: int = None,
        max_chars: int = None,
    ) -> pd.DataFrame:
    if df.dtypes.get(col_name) != 'object':
        Warning(f'Column {col_name} is not an object type')
        return df
    texts = df[col_name]
    if max_width:
        texts = texts.str.wrap(max_width)
    if max_height:
        try: texts = texts.map(lambda x: '\n'.join(x.split('\n')[:max_height]))
        except: pass
    if max_chars:
        try: texts = texts.map(lambda x: x[:max_chars] + '...' if len(x) > max_chars else '')
        except: pass
    for replace in replaces:
        target, replacement = replace
        try: texts = texts.str.replace(target, replacement, regex=False)
        except: pass
    df[col_name] = texts
    return df
        