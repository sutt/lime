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
from datetime import datetime


class MdSheetSection(BaseModel):
    type:           str
    name:           str
    sub_sections:   list

class MdQuestionSection(BaseModel):
    type:           str
    name:           str
    sub_sections:   list

class MdDocument(BaseModel):
    header:         Optional[MdSheetSection]
    questions:      List[MdQuestionSection]

class QuestionSchema(BaseModel):
    name:           str
    parse_warns:    List[str] = []
    meta:           Dict[str, str] = {}
    text_usr:       Optional[str] = None
    text_sys:       Optional[str] = None
    answer:         Optional[str] = None

class HeaderOutput(BaseModel):
    sheet_name:     str
    sheet_fn:       Optional[str]  = None
    run_id:         str
    name_model:     str
    start_time:     datetime
    lime_version:   str            = 'unknown'
    infer_params:   Dict[str, Any] = {}

class GradingOutput(BaseModel):
    grade_style:    str            = 'default'
    grade_bool:     Optional[bool] = None
    grade_error:    Optional[str]  = None
    grade_metric:   Optional[Any]  = None
    grade_detail:   Optional[Any]  = None

class NTokens(BaseModel):
    usr:            Optional[int]  = None
    sys:            Optional[int]  = None
    cmp:            Optional[int]  = None

class QuestionOutput(BaseModel):
    name:           str
    meta_data:      Dict[str, str]
    gen_params:     Dict[str, Any] = {}
    ground_truth:   Optional[str] = None
    question_usr:   Optional[str] = None
    question_sys:   Optional[str] = None
    completion:     Optional[str] = None
    error:          Optional[str] = None
    eval_time:      float
    grading:        Optional[GradingOutput] = None
    ntokens_usr:    Optional[int] = None
    ntokens:        Optional[NTokens] = None

class SheetOutputSchema(BaseModel):
    header:         HeaderOutput
    questions:      List[QuestionOutput]

class SheetSchema(BaseModel):
    name:           str
    meta:           Dict[str, str]
    sheet_fn:       Optional[str] = None
    text:           str
    questions:      List[QuestionSchema]

    @classmethod
    def from_mddoc(cls, doc: MdDocument):
        
        sheet_header = doc.header
        
        sheet_meta = {}
        sheet_text = None
        sheet_name = None
        if sheet_header is not None:
            _name = sheet_header.name
            _meta = [e for e in sheet_header.sub_sections if e['type'] == 'meta']
            _meta = _meta[0]['data'] if len(_meta) > 0 else {}
            _text = [e for e in sheet_header.sub_sections if e['type'] == 'question']
            _text = _text[0]['clean'] if len(_text) > 0 else None
            sheet_meta = _meta
            sheet_text = _text
            sheet_name = _name

        questions = doc.questions

        question_schemas = []
        for question in questions:
            question_name = question.name
            question_meta = [e for e in question.sub_sections if e['type'] == 'meta']
            question_meta = question_meta[0]['data'] if len(question_meta) > 0 else {}
            question_text_usr = [e for e in question.sub_sections if e['type'] == 'question']
            question_text_usr = question_text_usr[0]['text_usr'] if len(question_text_usr) > 0 else None
            question_test_sys = sheet_text
            question_answer = [e for e in question.sub_sections if e['type'] == 'answer']
            question_answer = question_answer[0]['answer_clean'] if len(question_answer) > 0 else None
            parse_warns = []
            if question_text_usr is None:
                question_text_usr = ''
                parse_warns.append('text_usr is None')
            if question_name in [q.name for q in question_schemas]:
                parse_warns.append(f'question name `{question_name}` is not unique')
                question_name = f"{question_name}_1"
            question_schemas.append(
                QuestionSchema(
                    name=question_name,
                    meta=question_meta,
                    text_usr=question_text_usr,
                    text_sys=question_test_sys,
                    answer=question_answer,
                    parse_warns=parse_warns.copy()
                )
            )

        return cls(
            name=sheet_name or '',
            meta=sheet_meta or {},
            text=sheet_text or '',
            questions=question_schemas or [],
        )
