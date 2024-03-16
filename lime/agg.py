import os
import sys
import glob
import pandas as pd
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
    question_by_runid_completion,
    grade_discrepancy_by_runid,
    model_input_results,
)
from lime.modules.views.agg.utils import (
    fmt_text_field,
)

class ExecSettings(ConfigLoader):
    output_sheet_prefix = 'output'

ExecSettings._initialize()


def build_data_wrapper(
    input_glob: str,
    ) -> pd.DataFrame:

    if input_glob == '.':
        input_glob = '*'
    
    elif os.path.isdir(input_glob):
        input_glob = os.path.join(input_glob, '*')
    
    if not(glob.glob(input_glob)):
        raise BaseQuietError(f'No files found in: {input_glob}')

    try:    
        return build_data(input_glob)
    except:
        # not entirely correct: just a guess on what went wrong
        # really we need to return values from the inner funcs of 
        # build_data and get_json_result_fns
        msg =  'No output object files found in specified directory.\n'
        msg += f'Found {len(glob.glob(input_glob))} files in {input_glob}'
        msg += f' but none with with output_sheet_prefix='
        msg += f'{ExecSettings.output_sheet_prefix} as prefix in filenname.'
        msg += f'(This setting can be switched in config)'
        raise BaseQuietError(msg)
        

def build_data_message(
        data: pd.DataFrame,
        verbose: bool,
    ) -> None:
    if verbose:
        print(f'questions found: {data.shape[0]}', file=sys.stderr)
        print(f'unique sheets:   {data["input_name"].nunique()}', file=sys.stderr)


def do_aggregate(
    data: pd.DataFrame,
    ) -> str:

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
        .head(10)
        ).to_markdown(index=False)
    output += '\n\n'

    return output


def do_completions(
    data: pd.DataFrame,
    ) -> str:

    data = fmt_text_field(
        data, 
        'completion', 
        max_width=60,
        max_height=7, 
        max_chars=30,
        replaces=[('\n', '<br>')],
    )
    
    add_index_cols = []

    output  = '''### Questions/IDs: full Completions \n\n'''
    output += format_multi_index(
        question_by_runid_completion(data, add_index_cols=add_index_cols)
        ).to_markdown(index=False)
    output += '\n\n'
    
    return output
    

def do_discrepancies(
    data: pd.DataFrame,
    is_full: bool = False,
    ) -> str:
    
    if is_full:
        
        data = fmt_text_field(
            data, 
            'completion', 
            max_chars=30,
        )

    add_values = ['completion'] if is_full else []

    output  = '''### Model/RunIDs: rows where grade_bool has discrepancy \n\n'''
    output += format_multi_index(
        grade_discrepancy_by_runid(data, add_values=add_values)
    ).to_markdown(index=False)
    output += '\n\n'
    
    return output


def setup_parser(argparser):

    argparser.add_argument('input_glob', nargs='?', default=None
                          ,help='Input directory')
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-b', '--debug',         action='store_true')

    # special report types
    argparser.add_argument('--completions',         action='store_true')
    argparser.add_argument('--discrepancies',       action='store_true')
    argparser.add_argument('--discrepancies-full',  action='store_true', dest='discrepancies-full')


def main(args):
    
    args = vars(args)

    if args.get('debug'):
        QuietError.debug_mode = True

    input_glob = args.get('input_glob')

    if input_glob is None:
        raise BaseQuietError('Missing Required Arg: `input_glob`')
    
    data = build_data_wrapper(input_glob)

    build_data_message(
        data=data,
        verbose=args.get('verbose'),
    )

    # TODO - toggle --md mode vs --terminal mode:
    # changes params to `replaces` + `max_width`
    
    if args.get('completions'):

        s_output = do_completions(
            data=data,
        )
    
    elif args.get('discrepancies'):
        
        s_output = do_discrepancies(
            data=data,
        )
    
    elif args.get('discrepancies-full'):
        
        s_output = do_discrepancies(
            data=data,
            is_full=True,
        )
    
    # default report condition
    else:
        
        s_output = do_aggregate(
            data=data,
        )

    # TODO - may need post-processing
    # s_output = s_output.encode('utf-8') #.decode('utf-8')
    # sys.stdout.buffer.write(s_output)
    
    print(s_output)