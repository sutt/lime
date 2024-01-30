import os
import pandas as pd
import json
from .collect import build_data


def format_multi_index(df):
    '''
        used for printing multi-index dataframes to markdown
    '''
    if len(df.columns) == 0:
        return pd.DataFrame(df.index.to_list(), columns=df.index.names)
    else:
        left = pd.DataFrame(df.index.to_list(), columns=df.index.names)
        right = df.reset_index(drop=True)
        return pd.concat([left, right], axis=1)


def input_by_model(data):
    return (
        data.groupby(['input_name', 'model_name'])
        .agg({'run_id': 'nunique'})
        .reset_index()
        .sort_values('run_id', ascending=False)
    )


def all_sheets_all_questions(data):
    tmp = (
        data.groupby(['input_name', 'name'])
        .agg({'name': 'count'})
        .drop(columns=['name'])
    )
    return tmp


def sheet_by_model_pct_correct(data):
    tmp = (
        data.groupby(['input_name', 'model_name'])
        .agg({'name': 'count', 'grade': 'mean'}) 
        .rename(columns={'name': 'num_questions', 'grade': 'pct_correct'})
        .sort_values(['input_name', 'pct_correct'], ascending=False)
    )
    tmp['pct_correct'] = (
        pd.to_numeric(tmp['pct_correct'], errors='coerce')
        .round(2)
    )
    return tmp


def model_input_results(
    data,
    model_name,
    input_name,
    run_id = None, # if None, use first run_id
):

    a = (data['model_name'] == model_name)
    b = (data['input_name'] == input_name)

    run_ids = data[a & b]['run_id'].unique()
    if run_id is None:
        run_id = run_ids[0]
    c = (data['run_id'] == run_id)

    num_questions = data[a & b & c].shape[0]

    slice_wrong = data[a & b & c & (data['grade'] == 0)]
    num_wrong = slice_wrong.shape[0]
    questions_wrong_name = slice_wrong['name'].tolist()

    return {
        'num_questions': num_questions,
        'num_wrong': num_wrong,
        'questions_wrong_name': questions_wrong_name,
    }
