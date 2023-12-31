import os
import json
import pandas as pd

MODEL_NAMES = ['gpt-3.5-turbo', 'gpt-4', 'llama_13b_chat']


def get_json_result_fns(results_fp):
    results = os.listdir(results_fp)
    results = [r for r in results if r.endswith('.json')]
    results = [r for r in results if r.startswith('output')]
    return results


def parse_sheet_meta(result_fn):

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


def sheet_table_info(result_fn, results_fp):
    with open(os.path.join(results_fp, result_fn)) as f:
        data = json.load(f)
        sheet_data = data['sheet']
    return {
        'input_name':   sheet_data.get('name'), 
        'model_name':   sheet_data.get('model_name'), 
        'run_id':       sheet_data.get('run_id'),
    }


def question_table(result_fn, results_fp):
    with open(os.path.join(results_fp, result_fn)) as f:
        data = json.load(f)
    return pd.DataFrame(data['questions'])


def build_full_table(results_fp, result_fn):
    q_tbl = question_table(result_fn, results_fp)
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