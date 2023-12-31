import os
import uuid
import argparse
from typing import Union
from modules.agg.collect import (
    build_data
)
from modules.agg.query import (
    format_multi_index,
    input_by_model,
    all_sheets_all_questions,
    sheet_by_model_pct_correct,
    model_input_results,
)

def do_aggregate(
    results_dir: str,
    output_fp: Union[None, str] = None,
    verbose: bool = False,
):
    data = build_data(results_dir)

    if verbose:
        print(f'questions found: {data.shape[0]}')
        print(f'unique sheets:   {data["input_name"].nunique()}')

    output = ''
    
    output += '''### Leaderboard: `{input_sheet, model}` on `pct_correct`\n\n'''
    output += format_multi_index(
        sheet_by_model_pct_correct(data)
        ).to_markdown(index=False)
    output += '\n\n'

    output += '''### Runs: `{input_sheet, model}` on number of `run_id`'s\n\n'''
    output += input_by_model(data).to_markdown(index=False)
    output += '\n\n'

    output += '''### All Questions: list of all question names by sheet\n\n'''
    output += format_multi_index(
        all_sheets_all_questions(data)
        ).to_markdown(index=False)
    output += '\n\n'

    if output_fp is None:
        print('--dryrun enabled; printing to stdout...\n')
        print(output)
    else:
        with open(output_fp, 'w') as f:
            f.write(output)
        if verbose:
            print(f'wrote to {output_fp}')
    
    return




if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input_dir',     type=str)
    argparser.add_argument('-o', '--output_fp',     type=str)
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-d', '--dryrun',        action='store_true')
    args = argparser.parse_args()
    args = vars(args)

    input_dir = args['input_dir']
    
    if input_dir is None:
        raise ValueError('-i / --input_dir is required')
    
    output_dir = args['output_fp']
    
    if output_dir is None and not(args['dryrun']):
        output_fn = f'agg-{uuid.uuid4().hex[:4]}.md'
        output_dir = os.path.join(input_dir, output_fn)
    
    do_aggregate(
        results_dir=input_dir,
        output_fp=output_dir,
        verbose=args['verbose'],
    )