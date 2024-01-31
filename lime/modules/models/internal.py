import json
from pydantic import (
    BaseModel
)
from typing import (
    Optional, 
    Union, 
    List,
    Dict,
    Any,
)

# TODO - subsection types

class MdSheetSection(BaseModel):
    type: str
    name: str
    sub_sections: list

class MdQuestionSection(BaseModel):
    type: str
    name: str
    sub_sections: list

class MdDocument(BaseModel):
    sections: List[Union[MdSheetSection, MdQuestionSection]]

class QuestionSchema(BaseModel):
    name: str
    meta: Dict[str, str]
    text_usr: str
    text_sys: Optional[str] = None
    answer: Optional[str] = None

class SheetSchema(BaseModel):
    name: str
    meta: Dict[str, str]
    text: str
    questions: List[QuestionSchema]

    @classmethod
    def from_mddoc(cls, doc: MdDocument):
        
        sheet_header = [e for e in doc.sections if e.type == 'sheet']
        sheet_header = sheet_header[0] if len(sheet_header) > 0 else None
        
        sheet_meta = {}
        sheet_text = None
        sheet_name = None
        if sheet_header is not None:
            _name = sheet_header.name
            _meta = [e for e in sheet_header.sub_sections if e['type'] == 'meta']
            _meta = _meta[0]['data'] if len(_meta) > 0 else {}
            _text = [e for e in sheet_header.sub_sections if e['type'] == 'question']
            _text = _text[0]['text'] if len(_text) > 0 else None
            sheet_meta = _meta
            sheet_text = _text
            sheet_name = _name

        questions = [e for e in doc.sections if isinstance(e, MdQuestionSection)]

        question_schemas = []
        for question in questions:
            question_name = question.name
            question_meta = [e for e in question.sub_sections if e['type'] == 'meta']
            question_meta = question_meta[0]['data'] if len(question_meta) > 0 else {}
            question_text_usr = [e for e in question.sub_sections if e['type'] == 'question']
            question_text_usr = question_text_usr[0]['text'] if len(question_text_usr) > 0 else None
            question_test_sys = sheet_text
            question_answer = [e for e in question.sub_sections if e['type'] == 'answer']
            question_answer = question_answer[0]['answer_clean'] if len(question_answer) > 0 else None
            # TODO - add validation: e.g unique question name, test_usr must be present, etc
            question_schemas.append(
                QuestionSchema(
                    name=question_name,
                    meta=question_meta,
                    text_usr=question_text_usr,
                    text_sys=question_test_sys,
                    answer=question_answer
                )
            )

        return cls(
            name=sheet_name or '',
            meta=sheet_meta or {},
            text=sheet_text or '',
            questions=question_schemas or [],
        )


class HeaderOutput(BaseModel):
    sheet_name: str
    sheet_fn: str
    run_id: str
    name_model: str

class GradingOutput(BaseModel):
    grade_style:    str            = 'default'
    grade_bool:     Optional[bool] = None
    grade_metric:   Optional[Any]  = None
    grade_error:    Optional[str]  = None
    grade_detail:   Optional[Any]  = None  # This will hold objects, e.g for logprobs style

class QuestionOutput(BaseModel):
    name: str
    meta_data: Dict[str, str]  # TODO - parseInt if applicable
    ground_truth: str
    question: str
    question_usr: str
    question_sys: str
    completion: str
    error: Optional[str] = None
    eval_time: float
    grading: Optional[GradingOutput] = None

class SheetOutputSchema(BaseModel):
    header: HeaderOutput
    questions: List[QuestionOutput]