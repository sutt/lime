import os

def build_config_text(
    style : str,
) -> str:
    '''
        Build a config text based on style
    '''

    read_fn = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        '..', 
        '..',
        'data', 
        'config_model', 
        'template.yaml'
    )

    with open(read_fn, 'r') as f:
        template = f.read()

    lines, output_lines = template.split('\n'), []

    # add header
    header_sep = '# ====='
    header_sep_index = [
        i for i, line in enumerate(lines) 
        if header_sep in line
    ]
    header_sep_index = header_sep_index[0] + 1 if len (header_sep_index) >= 1 else 0
    output_lines += lines[:header_sep_index]

    # add lines based on a) whether it's a comment b) style
    for line in lines[header_sep_index:]:
        # keep whitespace
        if line.strip() == '':
            output_lines += [line]
        # for comments, keep them based on style
        elif line.strip().startswith('#'):
            if style == 'base':
                pass
            elif style == 'full':
                output_lines += [line]
            elif style == 'bare':
                pass
        # add non-comment line, unless its bare
        else:
            if style != 'bare':
                output_lines += [line]

    output_text = '\n'.join(output_lines)
    
    return output_text