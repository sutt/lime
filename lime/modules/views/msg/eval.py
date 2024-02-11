import sys, json
from typing import Any, List
from lime.modules.models.internal import (
    QuestionSchema,
    SheetSchema,
    QuestionOutput,
    SheetOutputSchema,
)

class SheetProgressMsg:
    def __init__(
            self, 
            verbose_level: int = 0,
            **kwargs
        ):
        self.verbose = verbose_level

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
            # TODO - add parse errors
    
    def pre_prompt(
            self, 
            question_obj: QuestionSchema
        ) -> None:
        if self.verbose > 0:
            print(f"Processing question: {question_obj.name}")
            # TODO - flush this to make everything one line when terse
        if self.verbose > 1:
            max_chars = 40
            s = question_obj.text_usr
            if len(s) > max_chars:
                s = s[:max_chars] + "..."
            print(f"Question text: {s}")
    def post_prompt(
            self, 
            question_output: QuestionOutput,
        ) -> None:
        if self.verbose > 0:
            print(f'complete in: {question_output.eval_time:.2f}')
            print(f'grade={question_output.grading.grade_bool}')
            
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class MainProgressMsg:
    def __init__(
            self, 
            verbose_level: int = 0,
            **kwargs
        ):
        self.verbose = verbose_level

    def pre_loop(
            self,
            sheet_fns: List[str],
        ) -> None:
        if self.verbose > 0: 
            print(f"Found {len(sheet_fns)} sheets")
        if self.verbose > 1:
            print(sheet_fns)
    
    def post_loop(
            self
        ) -> None:
        if self.verbose > 0:
            print('script done.')

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
    