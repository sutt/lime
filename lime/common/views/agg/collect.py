import os
import json
import glob
import pandas as pd
from ...models.state import ConfigLoader


class ExecSettings(ConfigLoader):
    output_sheet_prefix = 'output'

ExecSettings._initialize()


def get_json_result_fns(results_fp):
    results = glob.glob(results_fp)
    results = [r for r in results if os.path.isfile(r)]
    results = [r for r in results if r.endswith('.json')]
    results = [r for r in results 
               if os.path.split(r)[1].startswith(ExecSettings.output_sheet_prefix)
               ]
    return results


def expand_object(
    data: pd.DataFrame, 
    column: str, 
    drop_original: bool = True,
    ) -> pd.DataFrame:
    try:
        expanded = data[column].apply(pd.Series)
        if drop_original:
            data = data.drop([column], axis=1)
        return pd.concat([data, expanded], axis=1)
    except Exception as e:
        print(f'Error expanding {column}: {e}')
        return data


def sheet_table_info(result_fn: str):
    with open(result_fn) as f:
        data = json.load(f)
    header_data = data.get('header')
    return {
        'input_name':   header_data.get('sheet_name'), 
        'input_fn':     header_data.get('sheet_fn'), 
        'model_name':   header_data.get('name_model'), 
        'run_id':       header_data.get('run_id'),
    }


def question_table(result_fn: str):
    with open(result_fn) as f:
        data = json.load(f)
    return pd.DataFrame(data['questions'])


def build_full_table(result_fn: str):
    q_tbl = question_table(result_fn)
    q_tbl = expand_object(q_tbl, 'grading')
    q_tbl = expand_object(q_tbl, 'gen_params')
    tbl_info = sheet_table_info(result_fn)
    for col_name, col_val in tbl_info.items():
        q_tbl[col_name] = col_val
    return q_tbl


def build_data(results_fp):
    result_fns = get_json_result_fns(results_fp)
    tbls = []
    for result_fn in result_fns:
        try:
            tbl = build_full_table(result_fn)
            tbls.append(tbl)
        except Exception as e:
            pass
    return pd.concat(tbls)