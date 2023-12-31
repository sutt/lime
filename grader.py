import json
import argparse
from typing import Union
from modules.parse import parse_wrapper
from main import grade_array

def do_grade_sheet(
        output_json_fp: str,
        input_md_fp: Union[None, str] = None,
        input_schema_fp: str = 'data/md-schema.yaml',
        overwrite: bool = False,
        verbose: bool = False,
        liberal_grading: bool = False,
):
    
    # always get the open the output file, this will be re-graded
    with open(output_json_fp, 'r') as f:
        output_obj = json.loads(f.read())
    
    output_questions = output_obj['questions']
    output_question_names = [e.get('name') for e in output_questions]
    output_question_grades = [e.get('grade') for e in output_questions]

    # we've got an input so we'll override the ground_truth in output
    # with the ground_truth from input where applicable
    if input_md_fp is not None:
        
        # note: input_question object is different from output_question object
        input_json_doc = parse_wrapper(
            fn=input_md_fp,
            md_schema_fn=input_schema_fp,
        )

        input_questions = [e for e in input_json_doc if e['type'] == 'question']

        match_counter = 0
        overwrite_counter = 0

        for _q in input_questions:
            
            try:
                output_index = output_question_names.index(_q['name'])
            except: continue
            match_counter += 1
            
            output_gt = output_questions[output_index]['ground_truth']
            input_gt = [e for e in _q['sub_sections'] if e['type'] == 'answer'][0]['answer_clean']
            if output_gt == input_gt: continue
            overwrite_counter += 1
            
            output_questions[output_index]['ground_truth'] = input_gt

        if verbose:
            print(f'ground_truth entries from input: {input_md_fp}')
            print(f'found:  {len(input_questions)}')
            print(f'matched: {match_counter}')
            print(f'overwritten: {overwrite_counter}')

    # now, regrade the output object
    new_grades = grade_array(
        answers=[e['ground_truth'] for e in output_obj['questions']],
        completions=[e['completion'] for e in output_obj['questions']],
        liberal_grading=liberal_grading,
    )

    if verbose:
        print(f'orig_grades:   {output_question_grades}')
        print(f'new_grades:    {new_grades}')

    # overwrite/create the output file and grade file if specified
    if not(overwrite):
        print('Script done. To overwrite run with -w flag.')
    else:
        for i, e in enumerate(output_obj['questions']):
            e['ground_truth'] = output_questions[i]['ground_truth']
            e['grade'] = new_grades[i]
        with open(output_json_fp, 'w') as f:
            json.dump(output_obj, f, indent=2)
        # TODO - this replace is brittle as it could include 
        #  other instance of target string in filepath string but
        #  we only want to replace in filename
        grade_json_fn = output_json_fp.replace('output', 'grade')
        with open(grade_json_fn, 'w') as f:
            json.dump(new_grades, f, indent=2)

        if verbose:
            print('Script done. To see change run:')
            print(f'''git diff {output_json_fp.replace('output', '*')}''')
            print('To reset changes run:')
            print(f'''git checkout --{output_json_fp.replace('output', '*')}''')

    return new_grades


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-o', '--output_fp',     type=str)
    argparser.add_argument('-i', '--input_fp',      type=str)
    argparser.add_argument('-w', '--overwrite',     action='store_true')
    argparser.add_argument('-v', '--verbose',       action='store_true')
    argparser.add_argument('-l', '--liberal_grading', action='store_true')
    args = argparser.parse_args()
    args = vars(args)

    output_json_fp = args['output_fp']
    
    if output_json_fp is None:
        raise ValueError('-o / --output_fn is required')

    grades = do_grade_sheet(
        output_json_fp=output_json_fp,
        input_md_fp=args['input_fp'],        
        overwrite=args['overwrite'],
        verbose=args['verbose'],
        liberal_grading=args['liberal_grading'],
    )