import sys
sys.path.append('../')
import os, json, time
from modules.parse import parse_wrapper
from main import collect_input_sheets


def test_section_parse_1():

    doc_obj = parse_wrapper(
        './data/input-one.md',
        '../data/md-schema.yaml',
    )
    print(json.dumps(doc_obj, indent=2))
    # assert False
        
    questions = [e for e in doc_obj if e['type'] == 'question']
    sheets = [e for e in doc_obj if e['type'] == 'sheet']
    q0_text = [e for e in questions[0]['sub_sections'] if e['type'] == 'question'][0]['text']
    q1_subsection_types = [e['type'] for e in questions[1]['sub_sections']]

    Q0_TEXT = "Q: What did the early bird get?\nA:\n\n"

    assert len(questions) == 2
    assert len(sheets) == 1

    assert questions[0]['name'] == 'Question-One-1'

    assert q0_text == Q0_TEXT

    assert len(q1_subsection_types) == 2
    assert len([e for e in q1_subsection_types if e in ('meta', 'question')])


def test_section_parse_2():
    '''
        testing a compressed markdown with no spaces
        between sections for proper parsing
    '''
    doc_obj = parse_wrapper(
        './data/input-three.md',
        '../data/md-schema.yaml',
    )
        
    questions = [e for e in doc_obj if e['type'] == 'question']
    sheets = [e for e in doc_obj if e['type'] == 'sheet']
    q0_text = [e for e in questions[0]['sub_sections'] if e['type'] == 'question'][0]['text']
    q0_meta = [e for e in questions[0]['sub_sections'] if e['type'] == 'meta'][0]['data']
    q1_subsection_types = [e['type'] for e in questions[1]['sub_sections']]
    
    assert len(sheets) == 1
    assert len(questions) == 2
    assert questions[0]['name'] == 'Q-1'
    assert questions[1]['name'] == 'Q-2'

    Q_SYSTEM_TEXT = """In the following, answer the multiple choice question or complete the saying and nothing else.\n"""

    Q0_TEXT = """Q: What did the early bird get?\nA) The bill\nB) The beer\nC) The worm\n"""


    # make sure the last line of the question is here
    assert q0_text == Q_SYSTEM_TEXT + Q0_TEXT

    Q0_META = {
        "answer_type": "multiple-choice",
        "answer_suggested_length": "15",  # overrides sheet level setting of 10
    }

    assert Q0_META == q0_meta
    
    Q1_SUBSECTIONS = ('meta', 'question', 'answer')
    
    assert all([e for e in q1_subsection_types if e in Q1_SUBSECTIONS ])


def test_meta_kv_parse_1():
    
    doc_obj = parse_wrapper(
        './data/input-one.md',
        '../data/md-schema.yaml',
    )
    
    def get_meta_data(question_obj):
        return [e for e in question_obj['sub_sections'] if e['type'] == 'meta'][0]['data']
    
    questions = [e for e in doc_obj if e['type'] == 'question']
    q0_meta = get_meta_data(questions[0])
    q1_meta = get_meta_data(questions[1])

    assert q0_meta.get('answer_suggested_length') == "50"
    assert q1_meta.get('answer_suggested_length') == "22"
    assert q0_meta.get('answer_type') == "multiple-choice"
    

def test_last_char_parse_1():

    doc_obj = parse_wrapper(
        './data/input-two.md',
        '../data/md-schema.yaml',
    )
    # print(json.dumps(doc_obj, indent=2))
    # assert False
        
    questions = [e for e in doc_obj if e['type'] == 'question']

    q0_text = [e for e in questions[0]['sub_sections'] if e['type'] == 'question'][0]['text']
    q1_text = [e for e in questions[1]['sub_sections'] if e['type'] == 'question'][0]['text']
    q2_text = [e for e in questions[2]['sub_sections'] if e['type'] == 'question'][0]['text']

    Q0_TEXT = "Q: What did the early bird get?\nA: "
    assert q0_text == Q0_TEXT
    
    Q1_TEXT = "Q: What did the early bird get?\nA: \n\n"
    assert q1_text == Q1_TEXT
    
    Q2_TEXT = "Q: What did the early bird get?\nA: \n"
    assert q2_text == Q2_TEXT



def test_collect_input_sheets_1():
    
    sheets_dir = './data/dir-one'

    input_sheets = collect_input_sheets(
        sheets_dir=sheets_dir,
    )
    
    assert len(input_sheets) == 2
    assert './data/dir-one/input-two.md' in input_sheets
    assert './data/dir-one/input-one.md' in input_sheets



def test_parse_system_prompt():
    '''
        verify a `#### question` section in sheet cascades to 
        each question on the sheet, what's usually called a "system prompt"
    '''
    
    doc_obj = parse_wrapper(
        './data/dir-two/input-one.md',
        '../data/md-schema.yaml',
    )
        
    questions = [e for e in doc_obj if e['type'] == 'question']
    
    q0_text = [e for e in questions[0]['sub_sections'] if e['type'] == 'question'][0]['text']

    SHEET_QUESTION = """In the following, answer the multiple choice question or complete the saying and nothing else. Use commonsense and traditional folk wisdom to answer the question.\n"""
    
    Q0_TEXT = """Q: What did the early bird get?\nA) The bill\nB) The beer\nC) The worm\n"""

    assert q0_text == SHEET_QUESTION + Q0_TEXT
    
