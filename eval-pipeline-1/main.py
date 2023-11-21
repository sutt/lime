import os, sys, time, json, argparse, uuid
from typing import Union
from modules.parse import parse_wrapper
from modules.oai_api import submit_prompt, get_completion
from modules.output import output_json, output_markdown


gen_params = {
    'max_tokens':200,
    'temperature':0.7,
}


def eval_sheet(
    input_md_fn: str,
    input_schema_fn: str,
    model_name: str,
    output_md_fn: str,
    output_json_fn: Union[None, str] = None,
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
        output['sheet'] = sheet_header[0]

    output_questions = []
    all_questions = [q for q in json_doc if q['type'] == 'question']
    
    if verbose_level > 0: print(f"Found {len(all_questions)} questions")
    
    for question in all_questions:

        try:
            t0 = time.time()
            answer = None 
            error = None
            name = question.get('name')
            meta = [e for e in question['sub_sections'] if e['type'] == 'meta']
            if len(meta) > 0:
                meta = meta[0]['data']
            else:
                meta = None
            question = [
                e for e in question['sub_sections'] 
                if e['type'] == 'question'
            ][0]['text']
            assert question is not None
        except Exception as e:
            print(e)
            continue
        
        if verbose_level > 0: 
            print(f"Processing question: {name}")
        if verbose_level > 1:
            print(f"question: {question}")
    
        try:
            completion = submit_prompt(
                prompt=question,
                model_name=model_name,
                max_tokens=gen_params['max_tokens'],
                temperature=gen_params['temperature'],
            )
            answer = get_completion(completion)

        except Exception as e:
            error = e
            if verbose_level > 0: 
                print(f"error on generation: {e}")
        
        output_questions.append({
            'name': name,
            'meta_data': meta,
            'question': question,
            'answer': answer,
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
        print(f'total: {len(output_questions)}, errors: {num_errors}')

    if output_json_fn is not None:
        output_json(output_json_fn, output)
    
    if output_md_fn is not None:
        output_markdown(output_md_fn, output)

    return output


def collect_input_sheets(
    sheets_dir: str,
) -> list:
    return []


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
    argparser.add_argument('-u', '--uuid_digits',   type=int, default=0)
    argparser.add_argument('-v', '--verbose',       type=int, default=0)
    
    args = argparser.parse_args()
    args = vars(args)

    # add defaults / override with cli args
    if args['sheet_fn'] is None:
        raise Exception('-f/--sheet_fn or -d/--sheets_dir arg required')
        
    sheet_fn = args['sheet_fn']

    input_dir = os.path.dirname(sheet_fn) + '/'

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

    output_fn = f'output-{model_name}-{uuid.uuid4().hex[:args["uuid_digits"]]}'
    
    output_md_fn   = output_dir + output_fn + '.md'
    
    if args['output_json']:
        output_json_fn = output_dir + output_fn + '.json' 
    else:
        output_json_fn = None
    
    tic =  1.0
    verbose_level = args['verbose']

    # setup args and call eval_sheet
    main_args = {
        'input_md_fn':    sheet_fn,
        'input_schema_fn':input_schema_fn,
        'model_name':     model_name,
        'output_md_fn':   output_md_fn,
        'output_json_fn': output_json_fn,
        'tic':            tic,
        'verbose_level':  verbose_level,
    }

    if verbose_level > 0: 
        print('starting eval script...')
        print(json.dumps(main_args, indent=4))

    output = eval_sheet(
        **main_args
    )
    
    if verbose_level > 0:
        # TODO - log where the output is
        print('script done.')