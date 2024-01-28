
import sys


class QuietError(Exception):
    # All who inherit me shall not traceback, but be spoken of cleanly
    # from: https://gist.github.com/jhazelwo/86124774833c6ab8f973323cb9c7e251
    pass

class BaseQuietError(QuietError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class ReqArgMissingError(QuietError):
    def __init__(self, argument_name):
        self.argument_name = argument_name
        super().__init__(self.argument_name)

    def __str__(self):
        return f"Argument `{self.argument_name}` is required."
    
class FileNotFoundError(QuietError):
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__(self.file_path)

    def __str__(self):
        return f"File `{self.file_path}` not found."
    
class NotADirectoryError(QuietError):
    def __init__(self, dir_path):
        self.dir_path = dir_path
        super().__init__(self.dir_path)

    def __str__(self):
        return f"Directory `{self.dir_path}` not found."
    

def quiet_hook(kind, message, traceback):
    if QuietError in kind.__bases__:
        print('{0}: {1}'.format(kind.__name__, message))  # Only print Error Type and Message
    else:
        sys.__excepthook__(kind, message, traceback)  # Print Error Type, Message and Traceback


sys.excepthook = quiet_hook
