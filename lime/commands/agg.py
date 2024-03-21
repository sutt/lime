import os
import sys
import glob
import pandas as pd
from typing import Union
from lime.common.models.state import ConfigLoader
from lime.common.models.errs import (
    QuietError,
    BaseQuietError,
)
from lime.common.views.agg.collect import (
    build_data
)
from lime.common.views.agg.query import (
    format_multi_index,
    input_by_model,
    all_sheets_all_questions,
    sheet_by_model_pct_correct,
    question_by_runid_completion,
    grade_discrepancy_by_runid,
    model_input_results,
)
from lime.common.views.agg.utils import (
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


def do_summarize(
    data: pd.DataFrame,
    md_style: bool = False,
    no_format: bool = False,
    ) -> str:

    output = ''
    
    output += '''### Leaderboard: `{input_sheet, model}` on `pct_correct`\n\n'''
    output += format_multi_index(
        sheet_by_model_pct_correct(data)
        ,md_style=md_style
        ).to_markdown(index=False)
    output += '\n\n'

    output += '''### Runs: `{input_sheet, model}` on number of `run_id`'s\n\n'''
    output += input_by_model(data).to_markdown(index=False)
    output += '\n\n'

    output += '''### All Questions: list of all question names by sheet\n\n'''
    tmp_df = all_sheets_all_questions(data)
    if (not(md_style) and not(no_format)):
        tmp_df = tmp_df.head(10)
    output += format_multi_index(
        tmp_df
        ,md_style=md_style
        ).to_markdown(index=False)
    output += '\n\n'

    return output


def do_completions(
    data: pd.DataFrame,
    md_style: bool = False,
    no_format: bool = False,
    ) -> str:

    if not(no_format):

        data = fmt_text_field(
            data, 
            'completion', 
            max_width=60 if md_style else 30,
            max_height=7 if md_style else 3, 
            max_chars=300 if md_style else 30,
            replaces=[('\n', '<br>')] if md_style else [],
        )
    
    add_index_cols = []

    output  = '''### Questions/IDs: full Completions \n\n'''
    output += format_multi_index(
        question_by_runid_completion(data, add_index_cols=add_index_cols)
        ,md_style=md_style
        ).to_markdown(index=False)
    output += '\n\n'
    
    return output
    

def do_discrepancies(
    data: pd.DataFrame,
    md_style: bool = False,
    is_full: bool = False,
    ) -> str:
    
    if is_full:
        
        data = fmt_text_field(
            data, 
            'completion', 
            max_chars=300 if md_style else 20,
        )

    add_values = ['completion'] if is_full else []

    output  = '''### Model/RunIDs: rows where grade_bool has discrepancy \n\n'''
    output += format_multi_index(
        grade_discrepancy_by_runid(data, add_values=add_values)
        ,md_style=md_style
    ).to_markdown(index=False)
    output += '\n\n'
    
    return output


def setup_parser(argparser):

    argparser.add_argument('input_glob', nargs='?', default=None
                          ,help='Input directory')
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-b', '--debug',         action='store_true')

    # styling options
    argparser.add_argument('--md',                  action='store_true')
    argparser.add_argument('--terminal',            action='store_true')
    argparser.add_argument('--no-format',           action='store_true', dest='no-format')

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

    # could add a dry-run here to just view how the data is sliced up

    # default is to style to optimize print to terminal
    # if we detect redirect then we want to style for markdown
    # or allow explicit args to override the default
    md_style = False
    if (
        (not(sys.stdout.isatty()) and not args.get('terminal'))
         or args.get('md')
        ):
        md_style = True
        # TODO - add a warning here 
        # TODO - this doesn't catch pipe-to-less on windows...
        # ... so workaround is to add the --terminal when piping to less. 
        # but the following works for linux:
        # elif sys.stdout.seekable(): print("output to a file.") # e.g. python cmd.py > file.txt   
        # else: print("output to another command.") # e.g. python cmd.py | less
    
    no_format = args.get('no-format')

    # perform the requested report

    if args.get('completions'):

        s_output = do_completions(
            data=data,
            md_style=md_style,
        )
    
    elif args.get('discrepancies'):
        
        s_output = do_discrepancies(
            data=data,
            md_style=md_style,
        )
    
    elif args.get('discrepancies-full'):
        
        s_output = do_discrepancies(
            data=data,
            md_style=md_style,
            is_full=True,
        )
    
    # default report condition
    else:
        
        s_output = do_summarize(
            data=data,
            md_style=md_style,
        )

    # TODO - may need post-processing
    # s_output = s_output.encode('utf-8') #.decode('utf-8')
    # sys.stdout.buffer.write(s_output)
    
    print(s_output)