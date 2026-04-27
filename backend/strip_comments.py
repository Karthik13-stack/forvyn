import ast
import os

def strip_comments_and_docstrings(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        src = f.read()
        
    try:
        tree = ast.parse(src)
        
        # Remove docstrings
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
                continue
            if not len(node.body):
                continue
            if not isinstance(node.body[0], ast.Expr):
                continue
            if not hasattr(node.body[0], 'value') or not hasattr(node.body[0].value, 'value'):
                continue
            if isinstance(node.body[0].value.value, str):
                node.body.pop(0)

        new_src = ast.unparse(tree)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print(f"Stripped: {filepath}")
    except Exception as e:
        print(f"Skipped {filepath}: {e}")

if __name__ == "__main__":
    for root, _, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                strip_comments_and_docstrings(os.path.join(root, file))
