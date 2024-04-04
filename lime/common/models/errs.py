import sys
import traceback

_DEBUG_MODE = False

class NetworkError(Exception):
    pass

class QuietError(Exception):
    # from: https://gist.github.com/jhazelwo/86124774833c6ab8f973323cb9c7e251
    debug_mode = _DEBUG_MODE
    # modify this to True to print full traceback

class BaseQuietError(QuietError):
    def __init__(self, message, orig_traceback=None):
        self.message = message
        self.orig_traceback = orig_traceback
        super().__init__(self.message)

    def __str__(self):
        msg =  f'{self.message}'
        # this doesn't seem needed right now, already prints it out if you do...
        # BaseQuietError(f'Error creating infer_obj: {str(e)}', traceback.format_exc())
        # if QuietError.debug_mode:
        #     msg += f'\n\nOriginal Traceback:\n{self.orig_traceback}'
        return msg
        

def quiet_hook(kind, message, traceback):
    if QuietError in kind.__bases__:
        if getattr(QuietError, 'debug_mode') ==  False:
            # Short Err: print Error Type and Message
            msg = str(message) + ' (add --debug for full traceback)'
            print('{0}: {1}'.format(kind.__name__, msg))  
        else:
            # Full Error: print Type, Message and Traceback
            sys.__excepthook__(kind, message, traceback)
    else:
        # Full Error: default behavior
        sys.__excepthook__(kind, message, traceback)

sys.excepthook = quiet_hook
