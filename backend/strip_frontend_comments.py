import os
import re

def remove_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    
        content = re.sub(r'(?<!:)//.*', '', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Stripped: {file_path}")
    except Exception as e:
        print(f"Skipped {file_path}: {e}")

if os.path.exists('frontend'):
    for root, dirs, files in os.walk('frontend'):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.next' in dirs:
            dirs.remove('.next')
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.css')):
                remove_comments(os.path.join(root, file))
