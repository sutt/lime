import os
import json
import glob
import argparse
from typing import (
    List,
    Dict,
    Any,
)
from lime.common.models.errs import (
    BaseQuietError,
)
from lime.common.models.internal import (
    SheetOutputSchema,
    QuestionOutput,
    HeaderOutput,
)
from lime.common.views.agg.collect import (
    get_json_result_fns,
)

def wrap_md_detail(text: str, label: str = 'meta_data') -> str:
    return f'''
<details>
<summary>{label}:</summary>

{text}
</details>
'''

def format_meta_data(
        meta_data: Dict[str, Any], 
        label: str = '',
    ) -> str:
    output = ''
    for k, v in meta_data.items():
        output += f'- {k}: {v}\n'
    if label != '':
        output = wrap_md_detail(output, label)
    return output

def to_markdown(
        sheet: SheetOutputSchema,
    ) -> str:
        
    output = ''

    output += f'# {sheet.header.sheet_name}\n'
    output += f'**Run ID:** {sheet.header.run_id}\n'
    output += f'**Model name:** {sheet.header.name_model}\n'
    try:
        sys_prompt = sheet.questions[0].question_sys
        output += f'**System Prompt:**\n{sys_prompt}\n'
    except:
        output += f'**System Prompt:**None\n'
    if sheet.header.infer_params is not None:
        output += f'{format_meta_data(sheet.header.infer_params, label="infer_params")}\n'
    
    # TODO add lime version + other props

    for q in sheet.questions:

        output += f'### {q.name}\n'

        if q.meta_data is not None:
            output += f'{format_meta_data(q.meta_data, "meta_data")}\n'

        if q.gen_params is not None:
            output += f'{format_meta_data(q.gen_params, "gen_params")}\n'
        
        output += f'\n**Question:**\n{q.question_usr}\n'
        
        if q.error is not None:
            output += f'\n**Error:**\n{q.error}\n'
        
        output += f'\n**Completion:**\n{q.completion}\n'
        
        if q.ground_truth is not None:
            output += f'\n**Ground Truth:**\n{q.ground_truth}\n'

        if q.grading is not None:
            output += f'\n**Grade:**\n{q.grading.grade_bool}\n'
            # TODO - add other grading props
        
        output += '\n'

    return output


# def do_render(
#         output_sheet: str,
#         output_fn: str,
#     ):
#     output = to_markdown(output_sheet)


def batch_render(fns: List[str]):
    for fn in fns:
        try:    
            with open(fn, 'r') as f:
                output_sheet = SheetOutputSchema.model_validate(json.load(f))
            
            output_md = to_markdown(output_sheet)
            
            with open(fn.replace('.json', '.md'), 'w') as f:
                f.write(output_md)
        except Exception as e:
            print(f'Error rendering {fn}: {e}')


def setup_parser(argparser):

    argparser.add_argument('input_glob', nargs='?', default=None
                          ,help='Input directory')
    

def main(args):
    
    args = vars(args)

    input_glob = args.get('input_glob')

    if input_glob is None:
        raise BaseQuietError('Missing Required Arg: `input_glob`')
    
    if input_glob == '.':
        input_glob = '*'
    
    elif os.path.isdir(input_glob):
        input_glob = os.path.join(input_glob, '*')
    
    if not(glob.glob(input_glob)):
        raise BaseQuietError(f'No files found in: {input_glob}')
    
    result_fns = get_json_result_fns(input_glob)

    batch_render(result_fns)