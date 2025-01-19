import os
import os.path
from typing import List
from .gpt import Files


EXTS = ['.mp4', '.mkv', '.ass', '.srt']


def gen_input_list(dir: str, prefix: str = None) -> List[str]:
    if prefix is None:
        prefix = dir
    re = []
    for f in os.listdir(dir):
        if f.startswith('.'):
            continue
        path = os.path.join(dir, f)
        if os.path.isdir(path):
            data = gen_input_list(path, prefix=prefix)
            re += data
        else:
            exts = os.path.splitext(f)[1]
            if exts not in EXTS:
                continue
            p = os.path.relpath(path, prefix)
            re.append(p)
    re.sort()
    return re


def link_files(input: str, files: List[str], data: Files, output: str, hardlink: bool = False):
    for f in data.files:
        target = os.path.join(output, f.name)
        src = os.path.join(input, files[f.index])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if hardlink:
            os.link(src, target)
        else:
            os.symlink(src, target)
