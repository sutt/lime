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

class SheetProgressMsg:
    def __init__(
            self, 
            verbose_level: int = 0,
            **kwargs
        ):
        self.verbose = verbose_level
        self.n_chars = 13

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
            print(f"Completed all {total_questions} questions")
            print(f'completion_errors: {num_errors}')
    
    def pre_prompt(
            self, 
            question_obj: QuestionSchema
        ) -> None:
        if self.verbose > 0:
            s = '{:<{n_chars}}'.format(
                shorten(question_obj.name, self.n_chars), 
                n_chars=self.n_chars
            )
            print(s, end='| ', flush=True)
        if self.verbose > 1:
            s = '{:<{n_chars}}'.format(
                shorten(question_obj.text_usr, self.n_chars), 
                n_chars=self.n_chars
            )
            print(s, end='| ', flush=True)

    def post_prompt(
            self, 
            q_out: QuestionOutput,
        ) -> None:
        if self.verbose > 0:
            s = '{:<{n_chars}}'.format(
                f"grade: {'✅' if q_out.grading.grade_bool else '❌'}", 
                n_chars=self.n_chars
            )
            print(s, end='| ', flush=True)
            s = '{:<{n_chars}}'.format(
                f'{q_out.eval_time:.2f} secs', 
                n_chars=self.n_chars
            )
            print(s, end='| ', flush=True)
            if self.verbose == 1:
                print('', flush=False)
        if self.verbose > 1:
            n_sys = q_out.ntokens.sys or 0
            n_usr = q_out.ntokens.usr or 0
            n_cmp = q_out.ntokens.cmp or 0
            tps = ( n_cmp / q_out.eval_time)
            tps = f'{tps:.1f}' if tps > 0 else 'n/a'
            s = '{:<{n_chars}}'.format(
                 f'{tps} tok/sec', 
                n_chars=self.n_chars
            )
            print(s, end='| ', flush=True)
            print('', flush=False)
            
    
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
            print(f'complete run_id: {output.header.run_id}')

    def pre_sheet(
            self,
            sheet_obj: SheetSchema,
        ) -> None:
        if self.verbose > 0:
            print(f"Processing sheet: {sheet_obj.name}")
            parse_warns = {
                e.name: e.parse_warns
                for e in sheet_obj.questions
                if len(e.parse_warns) > 0
            }
            if len(parse_warns) > 0:
                print(f"Sheet: {sheet_obj.name} has {len(parse_warns)} parse warnings")
        if self.verbose > 1:
            if len(parse_warns) > 0:
                print(json.dumps(parse_warns, indent=2))
    