import os, sys, json, time
from unittest import mock
sys.path.append('../')

from modules.grading import fuzzier_match

def test_fuzzier_match_1():
    '''
        test basic functionality
    '''
    # Perfect match
    ground_truth = 'hello world'
    completion = 'hello world'
    assert fuzzier_match(ground_truth, completion) == True

    # Case mis-match
    ground_truth = 'Hello World'
    completion = 'hello world'
    assert fuzzier_match(ground_truth, completion) == True

    # Whitespace
    ground_truth = 'Hello World'
    completion = 'hello world\n'
    assert fuzzier_match(ground_truth, completion) == True

    # Whitespace
    ground_truth = 'Hello World\n'
    completion = 'hello world'
    assert fuzzier_match(ground_truth, completion) == True

    # Whitespace
    ground_truth = 'Hello World\n'
    completion = '  \nhello world \n'
    assert fuzzier_match(ground_truth, completion) == True

    # Actually different spelling
    ground_truth = 'hello World'
    completion = 'hell world'
    assert fuzzier_match(ground_truth, completion) == False
    

def test_fuzzier_match_prefix_1():
    
    ground_truth = """A) True"""
    completion = """Sure here's my answer!\n\nA) True"""
    assert fuzzier_match(ground_truth, completion) == True

    ground_truth = """A) True"""
    completion = """Sure here's my answer!\n\nB) False"""
    assert fuzzier_match(ground_truth, completion) == False


def test_fuzzier_match_prefix_suffix_1():
    
    ground_truth = """A) True"""
    completion = """Sure here's my answer!\n\nA) True\n\nHope this helps!"""
    assert fuzzier_match(ground_truth, completion) == True

    ground_truth = """A) True"""
    completion = """Sure here's my answer!\n\nB) False\n\nHope this helps!"""
    assert fuzzier_match(ground_truth, completion) == False


def test_fuzzier_match_punctuation_1():
    
    ground_truth = """A) Lemur."""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion) == True

    ground_truth = """A) Lemur."""
    completion = """A.) Lemur"""
    assert fuzzier_match(ground_truth, completion) == True

    ground_truth = """A) Lemur."""
    completion = """A. Lemur"""
    assert fuzzier_match(ground_truth, completion) == True

    ground_truth = """A) Lemur."""
    completion = """A) Devil."""
    assert fuzzier_match(ground_truth, completion) == False

    # Not working yet
    # ground_truth = """A) Lemur."""
    # completion = """Sure here's my answer!\n\nA) Lemur\n\nHope this helps!"""
    # assert fuzzier_match(ground_truth, completion) == True


def test_fuzzier_match_partial_1():
    
    
    # No match when allow_just_letter=False
    ground_truth = """A) Lemur (Madagascar)"""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=False) == False

    # Same example matches when turning this on
    ground_truth = """A) Lemur (Madagascar)"""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    # Even  a simple letter will work
    ground_truth = """A"""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    # Can be overly liberal when completion hallucinates
    ground_truth = """A) Lemur (Madagascar)"""
    completion = """A) Devil"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True


def test_fuzzier_match_partial_2():
    '''
        Look at whitespsace and other artifacts in the completion/groundtruth 
        for fuzzy matching still working. Also look at false positive matches.
    '''
    
    ground_truth = """A"""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    ground_truth = """A"""
    completion = """  A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    ground_truth = """A \n"""
    completion = """A\nend answer"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    # Can be overly liberal #1
    ground_truth = """A"""
    completion = """Answer unknown"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    # Can be overly liberal #2
    ground_truth = """B"""
    completion = """ aBcd """
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == True

    # Ground Truth left trim is sensitive
    ground_truth = """(A)"""
    completion = """A) Lemur"""
    assert fuzzier_match(ground_truth, completion, allow_just_letter=True) == False


if __name__ == '__main__':
    pass