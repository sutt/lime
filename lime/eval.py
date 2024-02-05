import os, time, json, uuid
from typing import Union, Any
from lime.modules.controllers.parse import (
    parse_to_obj
)
from lime.modules.models.internal import (
    SheetSchema,
    HeaderOutput,
    QuestionOutput,
    SheetOutputSchema,
)
from lime.modules.views.msg.eval import (
    ProgressMsg
)
from lime.modules.grading.base import (
    grade_answer,
)
from lime.modules.inference.interface import (
    prompt_model,
    valid_model_name,
    ModelCacheFactory,
)
from lime.modules.views.output import (
    output_json,
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


def eval_sheet(
    sheet_obj: SheetSchema,
    model_name: str,
    run_id: str,
    output_json_fn: str,
    verbose_level: int = 0,
) -> list:

    progress = ProgressMsg(verbose_level=verbose_level)
    
    output = SheetOutputSchema(
        header = HeaderOutput(
            sheet_name=sheet_obj.name,
            # sheet_fn=input_md_fn,
            run_id=run_id,
            name_model=model_name,
        ),
        questions = [],
    )
    
    model_cache = ModelCacheFactory(
        b_init=not(model_name.startswith('gpt'))
    )

    progress.pre_loop(sheet_obj)
    
    for question in sheet_obj.questions:
        
        t0 = time.time()
        completion = None 
        error = None

        progress.pre_prompt(question)
                
        completion, error = prompt_model(
            model_name  = model_name,
            prompt_sys  = question.text_sys,
            prompt_usr  = question.text_usr,
            model_cache = model_cache.get(),
            verbose     = verbose_level,
        )
        
        question_output = QuestionOutput(
            name            = question.name,
            meta_data       = question.meta,
            ground_truth    = question.answer,
            question_sys    = question.text_sys,
            question_usr    = question.text_usr,
            completion      = completion,
            error           = str(error) if error is not None else None,
            eval_time       = time.time() - t0,
        )
        
        grading_output = grade_answer(
            completion      = completion,
            ground_truth    = question.answer,
        )

        question_output.grading = grading_output
        
        output.questions.append(question_output)

        # TODO - save temporarily to disk

        progress.post_prompt(question_output)

        # end loop

    # TODO - erase temp files
        
    output_json(output_json_fn, output.model_dump())

    progress.post_loop(output)

    return output


def get_setting(args: dict, key: str, default: Any = None):
    if args.get(key) is not None:
        return args[key]
    else:
        try: 
            return getattr(ExecSettings, key)
        except Exception as e: 
            return default
        

def collect_input_sheets(
    sheets_dir: str,
    fn_keyword: Union[None, str] = 'input',  #TODO - from Configs
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

    if args['output_dir'] is not None:
        output_dir = args['output_dir']
        if os.path.isdir(output_dir):
            raise NotADirectoryError(f'-o {output_dir} not a directory.')
    else: 
        output_dir = input_dir

    input_schema_fn = os.path.join(script_dir, 'data', 'md-schema.yaml')

    model_name      = get_setting(args, 'model_name')
    uuid_digits     = get_setting(args, 'uuid_digits')
    dry_run         = get_setting(args, 'dry_run', default=False)
    verbose_level   = get_setting(args, 'verbose')
    
    run_id = uuid.uuid4().hex[:uuid_digits]

    is_valid = valid_model_name(model_name)
    if not is_valid:
        raise BaseQuietError(f'Invalid model_name: {model_name}')
        
    for sheet_fn in sheet_fns:
        
        tmp_fn = sheet_fn.replace(input_dir, '')
        tmp_fn = tmp_fn.replace('input', '')
        tmp_fn = tmp_fn.replace('.md', '')
        output_fn = f'output{tmp_fn}-{model_name}-{run_id}'
        output_json_fn = output_dir + output_fn + '.json' 

        if dry_run:
            continue
        
        sheet_obj = parse_to_obj(
            sheet_fn,
            input_schema_fn,    
        )
        
        output = eval_sheet(
            sheet_obj=sheet_obj,
            model_name=model_name,
            run_id=run_id,
            output_json_fn= output_json_fn,
            verbose_level= verbose_level,
        )
    
    if verbose_level > 0:
        print('script done.')