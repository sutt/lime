from typing import Union, Any
from .oai_api import (
    submit_prompt, 
    get_completion,
)
from .local_cpp import (
    LocalModel,
    LocalModelCache,
    llama_cpp_loaded,
)

class ModelCacheFactory:
    def __init__(self, b_init=True):
        self.instance = None
        if llama_cpp_loaded and b_init:
            self.instance = LocalModelCache()
    def get(self) -> Union[None, LocalModelCache]:
        return self.instance

def prompt_model(
    model_name: str,
    prompt_sys: str = None,
    prompt_usr: str = None,
    model_cache: Union[None, LocalModelCache] = None,
    verbose : int = 0,
):
    error = None
    if model_name.startswith('gpt'):
        try:
            completion = submit_prompt(
                prompt=(prompt_sys or '') + prompt_usr,
                model_name=model_name,
            )
            answer = get_completion(completion)
        except Exception as e:
            error = e
            answer = None

    elif llama_cpp_loaded:        
        try:
            if ((model_cache is not None) and
                (prompt_sys is not None) and 
                (prompt_usr is not None)
                ):
                model_cache.get(model_name, prompt_sys)
                output = model_cache.eval_question(
                    prompt_usr,
                    verbose=verbose,
                    # **gen_params,

                )
                answer = output.get('text')
            else:
                model = LocalModel(model_name)
                output = model((prompt_sys or '') + prompt_usr)
                answer = LocalModel.get_completion(output)
        except Exception as e:
            error = e
            answer = None
    else:
        error = 'not an openai model, llama_cpp not loaded'
        answer = None

    return answer, error
