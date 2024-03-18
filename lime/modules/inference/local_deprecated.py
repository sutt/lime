class ChatTemplate:
    template = '''{{{SYS}}}{{{USR}}}'''
    default_templating_tag_left =  '''{{{'''
    default_templating_tag_right = '''}}}'''
    default_sys_tag = 'SYS'
    default_usr_tag = 'USR'
    left = None
    right = None
    
    @classmethod
    def wrap_prompt(
            cls,
            prompt: str = None,
            sys_prompt: str = None,
            usr_prompt: str = None,
        ) -> str: 
        pass

class DefaultModelChatTemplates:
    llama_7b = {
        
    }
    mistral_hf_7b = {
        'full': '',
        'left': '',
        'right': '',
    }

