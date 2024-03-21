import os
import json
import argparse
from typing import Union
from lime.modules.models.errs import (
    QuietError,
    BaseQuietError,
)
from lime.modules.models.internal import (
    SheetSchema,
    SheetOutputSchema,
)
from lime.modules.controllers.parse import (
    parse_to_obj
)
from lime.modules.grading.base import grade_array

script_dir = os.path.dirname(os.path.abspath(__file__))

def do_grade_sheet(
        output_json_fp: str,
        input_md_fp: Union[None, str] = None,
        input_schema_fp: str = os.path.join(script_dir, 'data', 'md-schema.yaml'),
        overwrite: bool = False,
        verbose: bool = False,
        liberal_grading: bool = False,
) -> None:
    
    with open(output_json_fp, 'r') as f:
        output_obj = SheetOutputSchema.model_validate_json(f.read())
    
    # we've got an input so we'll override the ground_truth in output
    # with the ground_truth from input where applicable
    if input_md_fp is not None:
        
        in_sheet = parse_to_obj(input_md_fp, input_schema_fp)
        
        match_counter = 0
        overwrite_counter = 0

        for _q in in_sheet.questions:
            
            try:
                # question names could have changed, in which case we'll skip
                # updating any ground_truth
                i = [e.name for e in output_obj.questions].index(_q.name)
            except:
                continue
            
            match_counter += 1
            
            if output_obj.questions[i].ground_truth != _q.answer:
                # overwrite the ground truth of output_obj
                # this does not overwrite to disk yet, that comes later
                overwrite_counter += 1
                output_obj.questions[i].ground_truth = _q.answer

        if verbose:
            print(f'ground_truth entries from input: {input_md_fp}')
            print(f'found:  {len(in_sheet.questions)}')
            print(f'matched: {match_counter}')
            print(f'overwritten: {overwrite_counter}')

    # apply the new grading: could be a new grading procedure 
    # and/or updated ground truth(s)
    new_grades = grade_array(
        answers=[e.ground_truth for e in output_obj.questions],
        completions=[e.completion for e in output_obj.questions],
        liberal_grading=liberal_grading,
    )
    
    print(f'orig_grades:   {[e.grading.grade_bool for e in output_obj.questions]}')
    print(f'new_grades:    {new_grades}')

    # overwrite/create the output file and grade file if specified
    if not(overwrite):
    
        print('Script done. To overwrite run with -w flag.')
    
    else:
        for i, e in enumerate(output_obj.questions):
            e.grading.grade_bool = new_grades[i]
            e.grading.grade_style = 'liberal' if liberal_grading else 'fuzzy'
        
        with open(output_json_fp, 'w') as f:
            f.write(output_obj.model_dump_json(indent=2))
        
        if verbose:
            print('Script done. To see change run:')
            print(f'''git diff {output_json_fp.replace('output', '*')}''')

    return


def setup_parser(argparser):

    argparser.add_argument('output_fp', nargs='?', default=None
                          ,help='the output json file to grade')

    argparser.add_argument('-i', '--input_fp',      type=str)
    argparser.add_argument('-w', '--overwrite',     action='store_true')
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-l', '--liberal_grading', action='store_true')
    argparser.add_argument('-b', '--debug',         action='store_true')


def main(args):
    
    args = vars(args)

    if args.get('debug'):
        QuietError.debug_mode = True

    output_json_fp = args.get('output_fp')
    
    if output_json_fp is None:
        raise BaseQuietError('Missing Required Arg: `output_fp`')
    
    if not(os.path.isfile(output_json_fp)):
        raise BaseQuietError(f'FileNotFound: {output_json_fp}')

    grades = do_grade_sheet(
        output_json_fp=output_json_fp,
        input_md_fp=args['input_fp'],        
        overwrite=args['overwrite'],
        verbose=args['verbose'],
        liberal_grading=args['liberal_grading'],
    )