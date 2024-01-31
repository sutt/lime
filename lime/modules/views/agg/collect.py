import os
import json
import pandas as pd
from ...models.state import ConfigLoader

MODEL_NAMES = ['gpt-3.5-turbo', 'gpt-4', 'llama_13b_chat']


class DefaultSettings(ConfigLoader):
    output_sheet_prefix = 'output'

DefaultSettings._initialize()

def get_json_result_fns(results_fp):
    results = os.listdir(results_fp)
    results = [r for r in results if r.endswith('.json')]
    results = [r for r in results 
               if r.startswith(DefaultSettings.output_sheet_prefix)
               ]
    return results


def parse_sheet_meta(result_fn):
    '''currently deprecated and not used'''

    result_fn = result_fn.lower()
    result_fn = result_fn[:result_fn.find('.json')]
    run_id = result_fn.split('-')[-1]

    result_fn = '-'.join((result_fn.split('-')[:-1]))
    model_name = 'unknown'
    for _name in MODEL_NAMES:
        if _name in result_fn:
            model_name = _name
            result_fn = result_fn.replace(_name, '')

    input_name = result_fn.replace('output-', '')
    if input_name.endswith('-'):
        input_name = input_name[:-1]

    return {
        'input_name':   input_name, 
        'model_name':   model_name, 
        'run_id':       run_id,
    }

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


def sheet_table_info(result_fn, results_fp):
    with open(os.path.join(results_fp, result_fn)) as f:
        data = json.load(f)
    header_data = data.get('header')
    return {
        'input_name':   header_data.get('sheet_name'), 
        'input_fn':     header_data.get('sheet_fn'), 
        'model_name':   header_data.get('name_model'), 
        'run_id':       header_data.get('run_id'),
    }


def question_table(result_fn, results_fp):
    with open(os.path.join(results_fp, result_fn)) as f:
        data = json.load(f)
    return pd.DataFrame(data['questions'])


def build_full_table(results_fp, result_fn):
    q_tbl = question_table(result_fn, results_fp)
    q_tbl = expand_object(q_tbl, 'grading')
    tbl_info = sheet_table_info(result_fn, results_fp)
    for col_name, col_val in tbl_info.items():
        q_tbl[col_name] = col_val
    return q_tbl


def build_data(results_fp):
    result_fns = get_json_result_fns(results_fp)
    tbls = []
    for result_fn in result_fns:
        tbls.append(build_full_table(results_fp, result_fn))
    return pd.concat(tbls)