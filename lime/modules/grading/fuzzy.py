import re
from typing import Union


def fuzzy_match(
        a: str, 
        b: str, 
        rm_punctuation: bool = True
) -> bool:
    
    a = a.lower().strip()
    b = b.lower().strip()

    if rm_punctuation:
        a = re.sub(r'[^\w\s]', '', a)
        b = re.sub(r'[^\w\s]', '', b)

    return a == b


def fuzzier_match(
        ground_truth: str, 
        completion: str,
        allow_just_letter: bool = False,
        allow_any_letter_style: bool = False,
        choices: Union[None, dict] = None,
) -> bool:
    
    output = {
        'valid': False,
        'choices': None,
        'hard_match': False,
        'soft_match': False,
        'letter_match': False,
    }
        
    if fuzzy_match(ground_truth, completion):
        return True
     
    if completion.find(ground_truth) != -1:
        return True
    
    if allow_just_letter:
        scan_length = 5
        if any([
            fuzzy_match(completion[:i], ground_truth[0]) 
            for i in range(1, scan_length)]
            ):
            return True
    
    return False
