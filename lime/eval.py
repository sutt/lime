import os, sys, time, json, argparse, uuid
from typing import Union, Any
from lime.modules.controllers.parse import parse_wrapper
from lime.modules.grading.base import (
    grade_sheet,
)
from lime.modules.inference.interface import (
    prompt_model,
    ModelCacheFactory,
)
from lime.modules.views.output import (
    output_json, 
    output_markdown,
)
from lime.modules.models.state import ConfigLoader
from lime.modules.models.errs import (
    BaseQuietError,
    ReqArgMissingError,
    FileNotFoundError,
    NotADirectoryError,
)


class ExecSettings(ConfigLoader):
    verbose = 1
    uuid_digits = 4
    model_name = 'gpt-3.5-turbo'
    input_sheet_prefix = 'input'
    output_sheet_prefix = 'output'
    use_prompt_caching = True

ExecSettings._initialize()


def get_setting(args: dict, key: str, default: Any = None):
    if args.get(key) is not None:
        return args[key]
    else:
        try: 
            return getattr(ExecSettings, key)
        except Exception as e: 
            return default


def eval_sheet(
    input_md_fn: str,
    input_schema_fn: str,
    model_name: str,
    output_md_fn: str,
    output_json_fn: str,
    run_id: Union[None, str] = None,
    output_grade_fn: Union[None, str] = None,
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

    # hack for now
    model_cache = ModelCacheFactory(
        b_init=not(model_name.startswith('gpt'))
    )
    
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
            question_section = [e for e in question['sub_sections'] if e['type'] == 'question'][0]
            question_text = question_section['text']
            question_usr = question_section['text_usr']
            question_sys = question_section['text_sys']
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
            prompt_sys=question_sys,
            prompt_usr=question_usr,
            model_cache=model_cache.get(),
            verbose=verbose_level,
        )
        
        if (error is not None) and (verbose_level > 0): 
            print(f"error on generation: {error}")
        
        output_questions.append({
            'name': name,
            'meta_data': meta,
            'ground_truth': ground_truth,
            'question': question_text,
            'question_usr': question_usr,
            'question_sys': question_sys,
            'completion': completion,
            'error': str(error) if error is not None else None,
            'model_name': model_name,
            'eval_time': time.time() - t0,
        })

        if verbose_level > 0: 
            print(f"complete in: {round(time.time() - t0, 1)}")

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


def setup_parser(parser):
    
    # optional input file/dir arg
    parser.add_argument('input', nargs='?', default=None
                        ,help='Input file or directory')
    # If not above, one of these two required
    parser.add_argument('-f', '--sheet_fn',      type=str)
    parser.add_argument('-d', '--sheets_dir',    type=str)
    # Optional arguments, will overwrite config loaded defaults
    parser.add_argument('-s', '--schema_fn',     type=str)
    parser.add_argument('-m', '--model_name',    type=str)
    parser.add_argument('-o', '--output_dir',    type=str)
    parser.add_argument('-y', '--dry_run',       action='store_true')
    parser.add_argument('-u', '--uuid_digits',   type=int)
    parser.add_argument('-v', '--verbose',       action='count', default=0)
    

def main(args):

    args = vars(args)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if the positional argument 'input' is provided
    input_path = args.get('input')
    
    if input_path:
        if os.path.isfile(input_path):
            args['sheet_fn'] = input_path
        elif os.path.isdir(input_path):
            args['sheets_dir'] = input_path
        else:
            raise BaseQuietError(f'Input path does not exist: {input_path}')

    # add defaults / override with cli args
    sheet_fn = args['sheet_fn']
    sheets_dir = args['sheets_dir']

    # validation
    if sheet_fn is None and sheets_dir is None:
        raise ReqArgMissingError('input')

    if sheet_fn is not None and sheets_dir is not None:
        raise BaseQuietError('cant use both -f/--sheet_fn or -d/--sheets_dir args')
        
    if sheet_fn is not None:
        if not os.path.isfile(sheet_fn):
            raise FileNotFoundError(sheet_fn)
        input_dir = "./"
        sheet_fns = [sheet_fn]
        
    if sheets_dir is not None:
        if not(os.path.isdir(sheets_dir)):
            raise NotADirectoryError(sheets_dir)
        input_dir = sheets_dir
        if input_dir[-1] != '/':
            input_dir += '/'
        sheet_fns = collect_input_sheets(sheets_dir)

    # defaults / cli parsing
    if args['schema_fn'] is not None:
        input_schema_fn = args['schema_fn']
    elif os.listdir(input_dir).count('md-schema.yaml') > 0:
        input_schema_fn = input_dir + 'md-schema.yaml'
    else:
        input_schema_fn = os.path.join(script_dir, 'data', 'md-schema.yaml')

    model_name = get_setting(args, 'model_name')

    if args['output_dir'] is not None:
        output_dir = args['output_dir']
    else: 
        output_dir = input_dir

    verbose_level =  get_setting(args, 'verbose')
 
    if get_setting(args, 'uuid_digits') > 0:
        run_id = uuid.uuid4().hex[:get_setting(args, 'uuid_digits')]
        uuid_fn = f'-{run_id}'
    else:
        run_id = None
        uuid_fn = ''

    # setup args and call eval_sheet
    eval_args = {
        'input_schema_fn':input_schema_fn,
        'model_name':     model_name,
        'verbose_level':  verbose_level,
        'run_id':         run_id,
    }
        
    dry_run = get_setting(args, 'dry_run', default=False)

    if verbose_level > 0: 
        print('starting eval script...')
        print(json.dumps(eval_args, indent=4))

    # main loop
    for sheet_fn in sheet_fns:
        
        tmp_fn = sheet_fn.replace(input_dir, '')
        tmp_fn = tmp_fn.replace('input', '')
        tmp_fn = tmp_fn.replace('.md', '')

        output_fn = f'output{tmp_fn}-{model_name}{uuid_fn}'
        
        output_md_fn   = output_dir + output_fn + '.md'
        
        output_json_fn = output_dir + output_fn + '.json' 

        output_grade_fn = output_dir + f'grade{tmp_fn}-{model_name}{uuid_fn}.json'

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