import pandas as pd
from pathlib import Path

class ExcelPromptLoader:

    def __init__(self, folder: Path):
        self.folder = folder

    def load_all(self):
        chunks = []
        for file in self.folder.glob('*.xlsx'):
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                text = f"\nDomain: {row['Domain']}\nDocument: {row['Document']}\nClause: {row['Clause']}\nPrompt: {row['Prompt']}\n".strip()
                chunks.append(text)
        return chunks