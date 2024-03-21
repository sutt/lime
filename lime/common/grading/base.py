from typing import List, Dict, Any
from lime.common.models.internal import (
    QuestionOutput,
    GradingOutput,
)
from .fuzzy import (
    fuzzier_match,
)

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
        if answer is None or completion is None:
            grade = None
        else:
            grade = fuzzier_match(
                ground_truth=answer, 
                completion=completion,
                allow_just_letter=liberal_grading,
            )
        grades.append(grade)

    return grades

def grade_answer(
    completion: str,
    ground_truth: str,
) -> GradingOutput: 
    grade_bool = None
    error = None
    if ( (completion is not None) and 
         (ground_truth is not None)
        ):
        try:
            grade_bool = fuzzier_match(
                ground_truth=ground_truth, 
                completion=completion,
            )
        except Exception as e:
            error = str(e)
    return GradingOutput(
        grade_style='fuzzy',
        grade_bool=grade_bool,
        grade_error=error,
    )