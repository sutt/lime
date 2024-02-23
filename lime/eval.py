import os, time, uuid, sys
from datetime import datetime
from typing import (
    Union, 
    Any,
)
from lime.modules.controllers.parse import (
    parse_to_obj
)
from lime.modules.models.internal import (
    SheetSchema,
    HeaderOutput,
    QuestionOutput,
    SheetOutputSchema,
    NTokens,
)
from lime.modules.models.utils import (
    get_lime_version,
)
from lime.modules.views.msg.eval import (
    SheetProgressMsg,
    MainProgressMsg,
)
from lime.modules.grading.base import (
    grade_answer,
)
from lime.modules.inference.interface import (
    prompt_model,
    valid_model_name,
    count_tokens,
    extract_gen_params,
    ModelCacheFactory,
)
from lime.modules.models.state import (
    ConfigLoader
)
from lime.modules.models.errs import (
    QuietError,
    BaseQuietError,
)


class ExecSettings(ConfigLoader):
    verbose = 1
    uuid_digits = 4
    model_name = 'gpt-3.5-turbo'
    input_sheet_prefix = 'input'
    output_sheet_prefix = 'output'
    use_prompt_caching = True
    save_tmp_file = False

ExecSettings._initialize()


def eval_sheet(
    sheet_obj: SheetSchema,
    model_name: str,
    run_id: str,
    tmp_output_fn: str = None,
    verbose_level: int = 0,
) -> SheetOutputSchema:

    progress = SheetProgressMsg(verbose_level=verbose_level)
    
    output = SheetOutputSchema(
        header = HeaderOutput(
            sheet_name  = sheet_obj.name,
            sheet_fn    = sheet_obj.sheet_fn,
            run_id      = run_id,
            name_model  = model_name,
            lime_version= get_lime_version(),
            start_time  = datetime.now(),
        ),
        questions = [],
    )
    
    if model_name.startswith('gpt'):
        model_cache = None
        infer_params = {}
    else:
        model_cache = ModelCacheFactory().get()
        local_model = model_cache.get()
        infer_params = local_model.get_all_params()
    
    sheet_gen_params = extract_gen_params(sheet_obj.meta)
    infer_params.update({'gen_params': sheet_gen_params})
    output.header.infer_params = infer_params

    progress.pre_loop(sheet_obj)
    
    for question in sheet_obj.questions:
        
        t0 = time.time()

        ntokens_usr = count_tokens(question.text_usr, model_name)
        ntokens_sys = count_tokens(question.text_sys, model_name)

        gen_params = extract_gen_params(question.meta)

        progress.pre_prompt(question)
        
        completion, error = prompt_model(
            model_name  = model_name,
            prompt_sys  = question.text_sys,
            prompt_usr  = question.text_usr,
            model_cache = model_cache,
            verbose     = verbose_level,
            gen_params  = gen_params,
        )
        
        question_output = QuestionOutput(
            name            = question.name,
            meta_data       = question.meta,
            gen_params      = gen_params,
            ground_truth    = question.answer,
            question_sys    = question.text_sys,
            question_usr    = question.text_usr,
            completion      = completion,
            error           = str(error) if error is not None else None,
            eval_time       = time.time() - t0,
        )

        ntokens_cmp = count_tokens(completion, model_name)

        question_output.ntokens = NTokens(
            usr = ntokens_usr,
            sys = ntokens_sys,
            cmp = ntokens_cmp,
        )
        
        grading_output = grade_answer(
            completion      = completion,
            ground_truth    = question.answer,
        )

        question_output.grading = grading_output
        
        output.questions.append(question_output)

        if tmp_output_fn is not None:
            s = output.model_dump_json(indent=2)
            with open(tmp_output_fn, 'w') as f:
                f.write(s)

        progress.post_prompt(question_output)

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
    parser.add_argument('-v', '--verbose',       action='count', default=0)
    parser.add_argument('-b', '--debug',         action='store_true')
    

def main(args):

    args = vars(args)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.get('debug'):
        QuietError.debug_mode = True

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
        raise BaseException('Required Arg Missing: `input`')

    if sheet_fn is not None and sheets_dir is not None:
        raise BaseQuietError('cant use both -f/--sheet_fn or -d/--sheets_dir args')
        
    if sheet_fn is not None:
        if not os.path.isfile(sheet_fn):
            raise BaseQuietError(f'File Not Found: {sheet_fn}')
        input_dir = "./"
        sheet_fns = [sheet_fn]
        
    if sheets_dir is not None:
        if not(os.path.isdir(sheets_dir)):
            raise BaseQuietError(f'Not A Directory: {sheets_dir}')
        input_dir = sheets_dir
        if input_dir[-1] != '/':
            input_dir += '/'
        sheet_fns = collect_input_sheets(sheets_dir)

    if args['output_dir'] is not None:
        output_dir = args['output_dir']
        if os.path.isdir(output_dir):
            raise BaseQuietError(f'Not A Directory: {output_dir}')
    else: 
        output_dir = input_dir

    input_schema_fn = os.path.join(script_dir, 'data', 'md-schema.yaml')

    model_name      = get_setting(args, 'model_name')
    dry_run         = get_setting(args, 'dry_run', default=False)
    verbose_level   = get_setting(args, 'verbose')
    
    run_id = uuid.uuid4().hex[:ExecSettings.uuid_digits]

    if not valid_model_name(model_name):
        raise BaseQuietError(f'Invalid model_name: {model_name}')
    
    progress = MainProgressMsg(verbose_level=verbose_level)

    progress.pre_loop(sheet_fns=sheet_fns)
        
    for sheet_fn in sheet_fns:
        
        tmp_fn = sheet_fn.replace(input_dir, '')
        tmp_fn = tmp_fn.replace('input', '')
        tmp_fn = tmp_fn.replace('.md', '')
        output_fn = f'output{tmp_fn}-{model_name}-{run_id}'
        output_fp = output_dir + output_fn + '.json'
        
        tmp_output_fp = None
        if ExecSettings.save_tmp_file:
            tmp_output_fp = output_dir + 'tmp.' + output_fn + '.json'
        
        sheet_obj = parse_to_obj(
            sheet_fn,
            input_schema_fn,    
        )

        sheet_obj.sheet_fn = sheet_fn

        progress.pre_sheet(sheet_obj)
        
        if dry_run:
            continue

        try:
            output = eval_sheet(
                sheet_obj=sheet_obj,
                model_name=model_name,
                run_id=run_id,
                tmp_output_fn=tmp_output_fp,
                verbose_level= verbose_level,
            )
        except KeyboardInterrupt:
            print('Keyboard Interrupt.')
            sys.exit(1)
        except Exception as e:
            raise BaseQuietError(f'Error processing sheet: {sheet_fn}: {e}')

        with open(output_fp, 'w') as f:
            f.write(output.model_dump_json(indent=2))

        if (tmp_output_fp is not None) and os.path.isfile(tmp_output_fp):
            try:
                os.remove(tmp_output_fp)
            except Exception as e:
                BaseQuietError(f'Error removing temp file: {tmp_output_fp}: {e}')
    
    progress.post_loop(output)
        