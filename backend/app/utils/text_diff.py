import difflib

def diff(old, new):
    return '\n'.join(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm=''))