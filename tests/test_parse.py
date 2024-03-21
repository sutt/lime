import os, sys
import pytest
from lime.common.models.internal import (
    SheetSchema,
    QuestionSchema,
)
from lime.common.controllers.parse import (
    parse_to_obj,
)
from lime.commands.eval import (
    collect_input_sheets
)

def test_parse_to_obj_1():
    '''
        basic functionality + test of EVAL-ENDCHAR behavior
    '''

    input_md = './tests/data/input-two.md'
    input_schema = './lime/data/md-schema.yaml'

    obj = parse_to_obj(input_md, input_schema)

    # Basic tests that should always hold
    assert obj.name == 'Sheet-One'
    assert len(obj.questions) == 3
    assert obj.questions[0].name == 'Question-One-1'
    assert obj.questions[1].name == 'Question-One-2'

    # Test types
    assert isinstance(obj, SheetSchema)
    assert isinstance(obj.questions[0], QuestionSchema)

    # This isn't assigned in parse, but in eval_sheet proc 
    assert obj.sheet_fn is None

    # We'll look at EVAL-ENDCHAR behavior to chop trailing whitespace
    assert obj.questions[0].text_usr == 'Q: What did the early bird get?\nA: '
    assert obj.questions[1].text_usr == 'Q: What did the early bird get?\nA: \n\n'
    assert obj.questions[2].text_usr == 'Q: What did the early bird get?\nA: \n'
    
def test_parse_to_obj_2():
    '''
        test on a compressed sheet + some extra characteristics
        not present in test_parse_to_obj_1.
    '''

    input_md = './tests/data/input-three.md'
    input_schema = './lime/data/md-schema.yaml'

    obj = parse_to_obj(input_md, input_schema)

    # Basic tests that should always hold
    assert obj.name == 'Sheet-Three'
    assert len(obj.questions) == 2
    assert obj.questions[0].name == 'Q-1'
    assert obj.questions[1].name == 'Q-2'

    # Test types
    assert isinstance(obj, SheetSchema)
    assert isinstance(obj.questions[0], QuestionSchema)

    # Check sheet level text prompt
    TEXT_SYS = '''In the following, answer the multiple choice question or complete the saying and nothing else.\n'''
    assert obj.text == TEXT_SYS
    assert obj.questions[0].text_sys == TEXT_SYS
    assert obj.questions[1].text_sys == TEXT_SYS

    # Check a variety of properties on this sheet
    TEXT_USR_0 = '''Q: What did the early bird get?\nA) The bill\nB) The beer\nC) The worm\n'''
    assert obj.questions[0].text_usr == TEXT_USR_0
    assert obj.questions[0].answer == 'C) The worm'
    assert obj.questions[0].meta.get('answer_suggested_length') == '15'  # override sheet-level meta
    assert obj.questions[1].meta.get('answer_suggested_length') == '10'  # should be set from sheet-level meta
    
    

def test_collect_input_sheets_1():
    '''
        test that we only collect sheets with prefix `input`
        TODO - change the setting
    '''
    
    sheets_dir = './tests/data/dir-one'

    input_sheets = collect_input_sheets(
        sheets_dir=sheets_dir,
    )
    
    assert len(input_sheets) == 2
    assert './tests/data/dir-one/input-two.md' in input_sheets
    assert './tests/data/dir-one/input-one.md' in input_sheets

def test_parse_warns_1():

    input_md = './tests/data/input-four.md'
    input_schema = './lime/data/md-schema.yaml'

    obj = parse_to_obj(input_md, input_schema)

    # Basic tests that should always hold
    assert obj.name == 'Sheet-Four'
    assert len(obj.questions) == 3

    # Test that this dupliate name appends a unique `_1` suffix
    assert obj.questions[1].name == 'Q-2'
    assert obj.questions[2].name == 'Q-2_1'
    assert obj.questions[2].parse_warns[0] == 'question name `Q-2` is not unique'

    # Since this question has no question section, it should throw a warn
    assert obj.questions[1].text_usr == '' # not too wed to this behavior
    assert obj.questions[1].parse_warns[0] == 'text_usr is None'

def test_meta_cascade_1():

    input_md = './tests/data/input-five.md'
    input_schema = './lime/data/md-schema.yaml'

    obj = parse_to_obj(input_md, input_schema)

    # Basic tests that should always hold
    assert obj.name == 'Sheet-Five'
    assert len(obj.questions) == 2

    obj.questions[1].meta.get('answer_suggested_length') == '10'  # should be set from sheet-level meta
    obj.questions[0].meta.get('answer_suggested_length') == '15'  # should be overridden by question-level meta
