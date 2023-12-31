import os, sys, time, json, argparse, uuid
from typing import Union
from modules.parse import parse_wrapper
from modules.grading import fuzzier_match
from modules.oai_api import submit_prompt, get_completion
from modules.local_llm_api import LocalModel
from modules.output import output_json, output_markdown


gen_params = {
    'max_tokens':200,
    'temperature':0.7,
}

def prompt_model(
  prompt: str,
  model_name: str,      
):
    error = None
    if model_name.startswith('gpt'):
        try:
            completion = submit_prompt(
                prompt=prompt,
                model_name=model_name,
                max_tokens=gen_params['max_tokens'],
                temperature=gen_params['temperature'],
            )
            answer = get_completion(completion)
        except Exception as e:
            error = e
            answer = None

    else:        
        try:
            # TODO - cache a loaded model
            model = LocalModel(model_name)
            output = model(prompt)
            answer = LocalModel.get_completion(output)
        except Exception as e:
            error = e
            answer = None

    return answer, error

def grade_sheet(
    json_doc: list,
    output_obj: dict,    
) -> list:
    
    all_questions = [q for q in json_doc if q['type'] == 'question']
    
    def extract_answer(question_obj):
        try:
            return [
                e for e in question_obj['sub_sections'] 
                if e['type'] == 'answer'
            ][0]['answer_clean']
        except Exception as e:
            return None
    
    all_answers = [extract_answer(q) for q in all_questions]

    all_completions = [e['completion'] for e in output_obj['questions']]
    
    # TODO - handle this better
    assert len(all_answers) == len(all_completions)
    
    return grade_array(all_answers, all_completions, liberal_grading=False)


def grade_array(
        answers: list,
        completions: list,  
        liberal_grading: bool = False,
) -> list:
    
    grades = []

    for answer, completion in zip(answers, completions):
        if answer is None:
            grade = None
        else:
            grade = fuzzier_match(
                ground_truth=answer, 
                completion=completion,
                allow_just_letter=liberal_grading,
            )
        grades.append(grade)

    return grades



def eval_sheet(
    input_md_fn: str,
    input_schema_fn: str,
    model_name: str,
    output_md_fn: str,
    run_id: Union[None, str] = None,
    output_json_fn: Union[None, str] = None,
    output_grade_fn: Union[None, str] = None,
    tic: Union[None, float] = None,
    verbose_level: int = 0,
) -> list:
    
    json_doc = parse_wrapper(
        fn=input_md_fn,
        md_schema_fn=input_schema_fn,
    )
    
    output = {}
    sheet_header = [e for e in json_doc if e['type'] == 'sheet']
    
    if len(sheet_header) > 0:
        
        header = sheet_header[0]
        header['run_id'] = run_id
        header['model_name'] = model_name
        meta = [e for e in header['sub_sections'] if e['type'] == 'meta']
        if len(meta) > 0:
            meta = meta[0]['data']
        else:
            meta = None
        header['meta_data'] = meta
        sheet_question = [e for e in header['sub_sections'] if e['type'] == 'question']
        if len(sheet_question) > 0:
            header['question'] = sheet_question[0]['text']
        
        # finally put this info into output object
        output['sheet'] = header

    output_questions = []
    all_questions = [q for q in json_doc if q['type'] == 'question']
    
    if verbose_level > 0: print(f"Found {len(all_questions)} questions")
    
    err_counter = 0
    for question in all_questions:

        try:
            t0 = time.time()
            completion = None 
            error = None
            name = question.get('name')
            meta = [e for e in question['sub_sections'] if e['type'] == 'meta']
            if len(meta) > 0:
                meta = meta[0]['data']
            else:
                meta = None
            question_text = [
                e for e in question['sub_sections'] 
                if e['type'] == 'question'
            ][0]['text']
            assert question is not None
            try:
                ground_truth = [
                    e for e in question['sub_sections'] 
                    if e['type'] == 'answer'
                ][0]['answer_clean']
            except Exception as e:
                ground_truth = None
        except Exception as e:
            if verbose_level > 0: print(e)
            err_counter += 1
            continue
        
        if verbose_level > 0: 
            print(f"Processing question: {name}")
        if verbose_level > 1:
            print(f"question: {question}")

        completion, error = prompt_model(
            prompt=question_text,
            model_name=model_name,
        )
        
        if (error is not None) and (verbose_level > 0): 
            print(f"error on generation: {error}")
        
        output_questions.append({
            'name': name,
            'meta_data': meta,
            'ground_truth': ground_truth,
            'question': question_text,
            'completion': completion,
            'error': error,
            'model_name': model_name,
            'eval_time': time.time() - t0,
        })

        if verbose_level > 0: 
            print(f"complete in: {round(time.time() - t0, 1)}")
        
        if tic is not None:
            time.sleep(tic)

    output['questions'] = output_questions

    if verbose_level > 0:
        num_errors = len([e for e in output_questions if e['error'] is not None])
        print(f'completed all questions...')
        print(f'total completion requests: {len(output_questions)},')
        print(f'parse_errors: {err_counter}')
        print(f'completion_errors: {num_errors}')

    if output_grade_fn is not None:
        try:
            grades = grade_sheet(
                json_doc=json_doc,
                output_obj=output,
            )
            
            output_json(output_grade_fn, grades)
            
            if (len(grades) > 0) and (grades.count(None) < len(grades)):
                for output_item, grade  in zip(output['questions'], grades):
                    output_item['grade'] = grade

        except Exception as e:
            print(f'grading failed, skipping...{e}')

    if output_json_fn is not None:
        output_json(output_json_fn, output)
    
    if output_md_fn is not None:
        output_markdown(output_md_fn, output)

    return output


def collect_input_sheets(
    sheets_dir: str,
    fn_keyword: Union[None, str] = 'input',
    fn_ext: str = '.md',
    fn_exclude_keyword: Union[None, str] = None,
) -> list:
    fns = os.listdir(sheets_dir)
    fns = [e for e in fns if e.endswith(fn_ext)]
    if fn_keyword is not None:
        fns = [e for e in fns if fn_keyword in e]
    if fn_exclude_keyword is not None:
        fns = [e for e in fns if fn_exclude_keyword not in e]
    if sheets_dir.endswith('/') is False:
        sheets_dir += '/'
    fns = [sheets_dir + e for e in fns]
    return fns


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    
    # One of these two required
    argparser.add_argument('-f', '--sheet_fn',      type=str)
    argparser.add_argument('-d', '--sheets_dir',    type=str)
    # Optional arguments
    argparser.add_argument('-s', '--schema_fn',     type=str)
    argparser.add_argument('-m', '--model_name',    type=str)
    argparser.add_argument('-o', '--output_dir',    type=str)
    argparser.add_argument('-j', '--output_json',   action='store_true')
    argparser.add_argument('-y', '--dry_run',       action='store_true')
    argparser.add_argument('-u', '--uuid_digits',   type=int, default=0)
    argparser.add_argument('-v', '--verbose',       type=int, default=0)
    
    args = argparser.parse_args()
    args = vars(args)

    # add defaults / override with cli args
    sheet_fn = args['sheet_fn']
    sheets_dir = args['sheets_dir']

    # validation
    if sheet_fn is None and sheets_dir is None:
        raise Exception('-f/--sheet_fn or -d/--sheets_dir arg required')

    if sheet_fn is not None and sheets_dir is not None:
        raise Exception('cant use both -f/--sheet_fn or -d/--sheets_dir args')
        
    if sheet_fn is not None:
        assert os.path.isfile(sheet_fn), f'file not found: {sheet_fn}'
        
    if sheets_dir is not None:
        assert os.path.isdir(sheets_dir), f'dir not found: {sheets_dir}'

    if sheet_fn is not None:
        input_dir = os.path.dirname(sheet_fn) + '/'
    elif sheets_dir is not None:
        input_dir = sheets_dir
        if input_dir[-1] != '/':
            input_dir += '/'

    # defaults / cli parsing
    if args['schema_fn'] is not None:
        input_schema_fn = args['schema_fn']
    elif os.listdir(input_dir).count('md-schema.yaml') > 0:
        input_schema_fn = input_dir + 'md-schema.yaml'
    else:
        input_schema_fn = './data/md-schema.yaml'

    if args['model_name']:
        model_name = args['model_name']
    else:
        model_name = 'gpt-3.5-turbo'

    if args['output_dir'] is not None:
        output_dir = args['output_dir']
    else: 
        output_dir = input_dir

    tic =  1.0

    verbose_level = args['verbose']

    if args['uuid_digits'] > 0:
        run_id = uuid.uuid4().hex[:args["uuid_digits"]]
        uuid_fn = f'-{run_id}'
    else:
        run_id = None
        uuid_fn = ''

    # setup args and call eval_sheet
    eval_args = {
        'input_schema_fn':input_schema_fn,
        'model_name':     model_name,
        'tic':            tic,
        'verbose_level':  verbose_level,
        'run_id':         run_id,
        # TODO - add concat output boolean
    }
    
    if verbose_level > 0: 
        print('starting eval script...')
        print(json.dumps(eval_args, indent=4))

    if sheets_dir is not None:
        sheet_fns = collect_input_sheets(sheets_dir)
    else:
        sheet_fns = [sheet_fn]

    for sheet_fn in sheet_fns:
        
        tmp_fn = sheet_fn.replace(input_dir, '')
        tmp_fn = tmp_fn.replace('input', '')
        tmp_fn = tmp_fn.replace('.md', '')

        output_fn = f'output{tmp_fn}-{model_name}{uuid_fn}'
        
        output_md_fn   = output_dir + output_fn + '.md'
        
        if args['output_json']:
            output_json_fn = output_dir + output_fn + '.json' 
        else:
            output_json_fn = None

        output_grade_fn = output_dir + f'grade{tmp_fn}-{model_name}{uuid_fn}.json'

        dry_run = False
        if args['dry_run']:
            dry_run = True

        sheet_args = {
            'input_md_fn':    sheet_fn,
            'output_md_fn':   output_md_fn,
            'output_json_fn': output_json_fn,
            'output_grade_fn':output_grade_fn,
        }

        eval_args.update(sheet_args)

        if verbose_level > 0: 
            print('starting eval function...')
            print(json.dumps(sheet_args, indent=4))

        if dry_run:
            continue

        # call main function
        output = eval_sheet(
            **eval_args
        )
    
    if verbose_level > 0:
        print('script done.')