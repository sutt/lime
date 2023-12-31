import json

# TODO - add eval_time to details
# TODO - add answer to details

def wrap_md_detail(output):
    return f'''
<details>
<summary>meta_data:</summary>

{output}
</details>
'''


def format_meta_data(meta_data, md_detail=True):
    output = ''
    for k, v in meta_data.items():
        output += f'- {k}: {v}\n'
    if md_detail:
        output = wrap_md_detail(output)
    return output


def output_json(output_fn: str, output: dict):
    with open(output_fn, 'w') as f:
        json.dump(output, f, indent=2)


def output_markdown(output_fn: str, output: dict):
    
    with open(output_fn, 'w') as f:
        
        sheet = output.get('sheet')
        if sheet is not None:
            
            sheet_name = sheet.get('name')
            run_id = sheet.get('run_id')
            model_name = sheet.get('model_name')
            sheet_meta_data = sheet.get('meta_data')
            sheet_question = sheet.get('question', 'No system prompt.')

            f.write(f'# {sheet_name}\n')
            f.write(f'**Run ID:** {run_id}\n')
            f.write(f'**Model name:** {model_name}\n')
            f.write(f'**System Prompt:**\n{sheet_question}\n')
            f.write(f'**Meta Data:**\n')
            f.write(f'{format_meta_data(sheet_meta_data, md_detail=False)}\n')

        for e in output['questions']:
            
            name = e.get('name')
            question = e.get('question')
            completion = e.get('completion')
            ground_truth = e.get('ground_truth')
            error = e.get('error')
            sheet_meta_data = e.get('meta_data')
            grade = e.get('grade')

            f.write(f'### {name}\n')

            if sheet_meta_data is not None:
                f.write(f'{format_meta_data(sheet_meta_data)}\n')
            
            f.write(f'\n**Question:**\n{question}\n')
            
            if error is not None:
                f.write(f'\n**Error:**\n{error}\n')
            
            if error is None:
                f.write(f'\n**Completion:**\n{completion}\n')
            
            if ground_truth is not None:
                f.write(f'\n**Ground Truth:**\n{ground_truth}\n')

            if grade is not None:
                f.write(f'\n**Grade:**\n{grade}\n')
            
            f.write('\n')


if __name__ == '__main__':
    out = format_meta_data({'a': 1, 'b': 2}, md_detail=False)
    print(out)