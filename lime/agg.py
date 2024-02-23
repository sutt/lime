import os
import sys
import uuid
import argparse
from typing import Union
from lime.modules.models.state import ConfigLoader
from lime.modules.models.errs import (
    QuietError,
    BaseQuietError,
)
from lime.modules.views.agg.collect import (
    build_data
)
from lime.modules.views.agg.query import (
    format_multi_index,
    input_by_model,
    all_sheets_all_questions,
    sheet_by_model_pct_correct,
    model_input_results,
)

class DefaultSettings(ConfigLoader):
    output_sheet_prefix = None

DefaultSettings._initialize()


def do_aggregate(
    results_dir: str,
    verbose: bool = False,
):
    try:
        data = build_data(results_dir)
    except:
        num_files = len(os.listdir(results_dir))
        msg =  'No output object files found in specified directory.\n'
        msg += f'Found {num_files} files in {results_dir}'
        if num_files > 0:
            msg += f' but none with with output_sheet_prefix='
            msg += f'{DefaultSettings.output_sheet_prefix} as prefix in filenname.'
            msg += f'(This setting can be switched in config)'
        print(msg, file=sys.stderr)
        return
    
    if verbose:
        print(f'questions found: {data.shape[0]}', file=sys.stderr)
        print(f'unique sheets:   {data["input_name"].nunique()}', file=sys.stderr)

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

    print(output)

    return


def setup_parser(argparser):

    argparser.add_argument('input_dir', nargs='?', default=None
                          ,help='Input directory')
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-b', '--debug',         action='store_true')


def main(args):
    
    args = vars(args)

    if args.get('debug'):
        QuietError.debug_mode = True

    input_dir = args.get('input_dir')

    if input_dir is None:
        raise BaseQuietError('Missing Required Arg: `input_dir`')
    
    if not(os.path.isdir(input_dir)):
        raise BaseQuietError(f'Not a Directory: {input_dir}')
    
    do_aggregate(
        results_dir=input_dir,
        verbose=args['verbose'],
    )