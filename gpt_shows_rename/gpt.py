import json
import openai
import httpx
from pydantic import BaseModel
from typing import List
from .config import Config


SYSTEM_PROMPT = '''You are an assistant, and your goal is to help users rename file names according to the following rules. The user will provide an input directory and a list of files in JSONL format. You will output the new location for each file after renaming based on the file list.
You will rename files based on the information extracted from the input directory and the file list. Prioritize using the information specified by the user. If no specific information is provided by the user, use the information extracted from the inputs mentioned above. 
The format for the highest-level directory is `Series Name (Year)`, which may optionally include a TMDB ID or TVDB ID, for example, `Series Name (Year) [tmdbid-1234]`.
The second-level directory format is `Season XX`. If there is not enough information, use `Season 01` by default. Special episodes, such as OVA, can use `Season 00`. Other movies, such as Bonus, should use `extras`. Trailers for episodes should be same as the episode.
The format for files in the third level is `SXXEXX Episode Name`. If multiple episodes are merged, use the following format: `SXXEXX-EXX Episode Name1/Episode Name2`. The episode name is optional. `SXXEXX` must be empty if file is in `extras` folder. If video is a trailer, add `.trailer` to name. For trailers, it is not necessary to replace the episode number with a small one.
The output file names must be relative path.
The output file names must retain parts of subtitle files, such as `.sc`, that indicate the language.'''


class File(BaseModel):
    index: int
    name: str


class Files(BaseModel):
    files: List[File]


def gen_files_list(files: List[str]):
    prompt = '''Here are file list:
```jsonl'''
    ind = 0
    for f in files:
        prompt += '\n' + json.dumps({"index": ind, "name": f}, ensure_ascii=False, separators=(',', ':'))
        ind += 1
    prompt += '\n```'
    return prompt


def get_response(cfg: Config, inp: str, files: List[str],
                 series_name: str = None, year: int = None, tmdb_id: int = None,
                 tvdb_id: int = None) -> Files:
    prompt = f'The input directory is `{inp}`.'
    if series_name:
        prompt += f'\nThe series name is `{series_name}`.'
    if year:
        prompt += f'\nThe year of series is `{year}`.'
    if tmdb_id:
        prompt += f'\nThe TMDB ID is `{tmdb_id}`.'
    if tvdb_id:
        prompt += f'\nThe TVDB ID is `{tvdb_id}`.'
    prompt += '\n' + gen_files_list(files)
    http_client = httpx.Client(proxy=cfg.proxy)
    client = openai.Client(api_key=cfg.api_key, base_url=cfg.base_url, http_client=http_client)
    res = client.beta.chat.completions.parse(
        model=cfg.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=Files,
    )
    mes = res.choices[0].message
    if mes.refusal:
        raise ValueError(f"Model refused to answer: {mes.refusal}")
    return mes.parsed
