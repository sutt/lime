import sys, json
from typing import Any, List, Union
from lime.common.models.internal import (
    QuestionSchema,
    SheetSchema,
    QuestionOutput,
    SheetOutputSchema,
)

def shorten(s: str, n_chars: int) -> str:
    return s if len(s) <= n_chars else s[:n_chars - 3] + '...'

def grid_fmt(
        s: str,
        just_chars: Union[str, None] = None,
        max_chars: Union[int, None] = None,
    ) -> str:
    if just_chars is not None:
        s = '{:<{n_chars}}'.format(s, n_chars=just_chars)
    if max_chars is not None:
        s = s[:max_chars]
    return s

class SheetProgressMsg:
    def __init__(
            self, 
            verbose_level: int = 0,
            **kwargs
        ):
        self.verbose = verbose_level
        self.n_chars = 13

    @staticmethod
    def _grid_fmt_gen(
            just_chars: Union[int, None] = None,
            max_chars:  Union[int, None] = None,
            ) -> callable:
        def wrapper(s: str) -> str:
            return grid_fmt(s, just_chars=just_chars, max_chars=max_chars)
        return wrapper

    def pre_loop(
            self,
            sheet_obj: SheetSchema,
        ) -> None:
        if self.verbose > 0: 
            print(f"Found {len(sheet_obj.questions)} questions")
    
    def post_loop(
            self,
            output_obj: SheetOutputSchema,
        ) -> None:
        if self.verbose > 0:
            total_questions = len(output_obj.questions)
            num_errors = len([
                e for e in output_obj.questions 
                if e.error is not None
            ])
            s =  f'Completed {total_questions} questions |'
            s += f' {num_errors} errors | '
            print(s)
    
    def pre_prompt(
            self, 
            question_obj: QuestionSchema
        ) -> None:
        if self.verbose == 0:
            return
        fmt = self._grid_fmt_gen(
                    just_chars = self.n_chars, 
                    max_chars =  self.n_chars if self.verbose == 1 else None,
        )
        sep = '| '
        s = ''
        if self.verbose > 0:
            s += fmt(question_obj.name)
            s += sep
        if self.verbose > 1 and question_obj.text_usr is not None:
            s += fmt(question_obj.text_usr)
            s += sep
        print(s, end='', flush=True)

    def post_prompt(
            self, 
            q_out: QuestionOutput,
        ) -> None:
        
        if self.verbose == 0:
            return
        
        fmt = self._grid_fmt_gen(
                    just_chars = self.n_chars, 
                    max_chars =  self.n_chars if self.verbose == 1 else None,
        )    
        sep = '| '
        
        if q_out.ground_truth is None:
            grade_symbol = '➖'
        
        elif (  (q_out.error is not None) or
                (q_out.grading is None) or
                (q_out.completion is None)
            ):
            grade_symbol = '⚠️'
            
        
        elif q_out.grading.grade_bool:
            grade_symbol = '✅'
        
        else:
            grade_symbol = '❌'
        
        n_chars = self.n_chars if self.verbose == 1 else None
            
        s = ''
        s += fmt(f'grade: {grade_symbol}')
        s += sep
        s += fmt(f'{q_out.eval_time:.2f} secs')
        s += sep
        if q_out.error is not None:
            s += fmt(f'err: {q_out.error}')
            s += sep
        if False:
            tps = ( (q_out.ntokens.cmp or 0) / q_out.eval_time)
            tps = f'{tps:.1f}' if tps > 0 else 'n/a'
            s += fmt(f'tps: {tps}')
            s += sep

        print(s, end='\n', flush=False)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class MainProgressMsg:
    def __init__(
            self, 
            verbose_level: int = 0,
            **kwargs
        ):
        self.verbose = verbose_level
        
    def infer_init(self, infer_obj: Any, check_valid: bool) -> None:
        if self.verbose > 0:
            msg =  f'Model_name: {infer_obj.model_name} | '
            msg += f'Model type: {infer_obj.__class__.__name__} | '
            msg += f'is_valid: {check_valid}'
            print(msg)
        if self.verbose > 1:
            # TODO - get extra info here
            pass

    def pre_loop(
            self,
            sheet_fns: List[str],
        ) -> None:
        if self.verbose > 0: 
            print(f"Found {len(sheet_fns)} sheets")
        if self.verbose > 1:
            print(sheet_fns)
    
    def post_loop(
            self,
            output: Union[SheetOutputSchema, None],
        ) -> None:
        if output is None: return
        if self.verbose > 0:
            print(f'run_id: {output.header.run_id}')

    def pre_sheet(
            self,
            sheet_obj: SheetSchema,
        ) -> None:
        if self.verbose > 0:
            print(f"Processing: {sheet_obj.name} ... ", end='', flush=True)
            parse_warns = {
                e.name: e.parse_warns
                for e in sheet_obj.questions
                if len(e.parse_warns) > 0
            }
            if len(parse_warns) > 0:
                print(f" | {len(parse_warns)} parse warnings")
        if self.verbose > 1:
            if len(parse_warns) > 0:
                print(json.dumps(parse_warns, indent=2))
    