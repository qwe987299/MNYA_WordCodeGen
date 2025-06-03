import os
import re


def sub2txt(file_paths, output_dir):
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-16 le') as f:
            text = f.read()
        text = re.sub(r'\s\n[0-9][0-9][0-9]', '', text)
        text = re.sub(r'\s\n[0-9][0-9]', '', text)
        text = re.sub(r'\s\n[0-9]', '', text)
        text = re.sub(r',[0-9][0-9][0-9] --> .*\n', ' ', text)
        text = re.sub(r',[0-9][0-9] --> .*\n', ' ', text)
        text = re.sub(r',[0-9] --> .*\n', ' ', text)
        text = text.split('\n', 1)[1]
        text = '00:00:00 片頭\n' + text
        output_filename = os.path.splitext(filename)[0] + '.txt'
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
