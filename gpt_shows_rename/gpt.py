import json
import openai
import httpx
from pydantic import BaseModel
from typing import Dict, List
from .config import Config


SYSTEM_PROMPT = '''You are an assistant, and your goal is to help users rename file names according to the following rules. The user will provide an input directory and a list of files in JSONL format. You will output the new location for each file after renaming based on the file list.
You will rename files based on the information extracted from the input directory and the file list. Prioritize using the information specified by the user. If no specific information is provided by the user, use the information extracted from the inputs mentioned above.  If user provide TMDB data, use the information from TMDB data first.
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


class TmdbData(BaseModel):
    series_info: dict
    seasons_info: Dict[int, dict]


def gen_files_list(files: List[str]):
    prompt = '''Here are file list:
```jsonl'''
    ind = 0
    for f in files:
        prompt += '\n' + json.dumps({"index": ind, "name": f}, ensure_ascii=False, separators=(',', ':'))
        ind += 1
    prompt += '\n```'
    return prompt


def gen_tmdb_data(tmdb_data: TmdbData):
    prompt = '''Here are series info from TMDB:
```json'''
    prompt += '\n' + json.dumps(tmdb_data.series_info, ensure_ascii=False, separators=(',', ':'))
    prompt += '\n```'
    for season_number, season_info in tmdb_data.seasons_info.items():
        prompt += f'\nHere are season {season_number} info from TMDB:'
        prompt += '\n```json'
        prompt += '\n' + json.dumps(season_info, ensure_ascii=False, separators=(',', ':'))
        prompt += '\n```'
    return prompt


SUPPORTED_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06", "gpt-4o-2024-11-20", "gpt-4o-mini-2024-07-18"]


def is_support_structed_output(model: str):
    if model.startswith('ft:'):
        models = model.split(':')
        if len(models) < 2:
            return False
        model = models[1]
    return model in SUPPORTED_MODELS


def parse_result(result: str):
    lines = result.splitlines()
    files = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("```"):
            continue
        try:
            files.append(File(**json.loads(line)))
        except Exception:
            raise ValueError(f"Failed to parse message: {line}")
    return Files(files=files)


async def get_response(cfg: Config, inp: str, files: List[str],
                       series_name: str = None, year: int = None, tmdb_id: int = None,
                       tvdb_id: int = None, tmdb_data: TmdbData = None) -> Files:
    prompt = f'The input directory is `{inp}`.'
    if tmdb_data:
        prompt += '\n' + gen_tmdb_data(tmdb_data)
    prompt += '\n' + gen_files_list(files)
    if series_name:
        prompt += f'\nThe series name is `{series_name}`.'
    if year:
        prompt += f'\nThe year of series is `{year}`.'
    if tmdb_id:
        prompt += f'\nThe TMDB ID is `{tmdb_id}`.'
    if tvdb_id:
        prompt += f'\nThe TVDB ID is `{tvdb_id}`.'
    input(prompt)
    http_client = httpx.AsyncClient(proxy=cfg.proxy)
    client = openai.AsyncClient(api_key=cfg.api_key, base_url=cfg.base_url, http_client=http_client)
    if is_support_structed_output(cfg.model):
        result = None
        mes = ''
        refusal = ''
        async with client.beta.chat.completions.stream(
            model=cfg.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=Files,
        ) as stream:
            async for event in stream:
                if event.type == "content.delta":
                    mes += event.delta
                    print(event.delta, end='', flush=True)
                    if event.parsed:
                        result = event.parsed
                elif event.type == "refusal.delta":
                    refusal += event.delta
                    print(event.delta, end='', flush=True)
        print('', flush=True)
        if refusal:
            raise ValueError(f"Model refused to answer: {refusal}")
        if not result:
            raise ValueError(f"Unhandle Error: {mes}")
        result = Files(**result)
        return result
    else:
        res = await client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + "\nThe format of the returned result is consistent with the input file list."},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        mes = ''
        async for chunk in res:
            if chunk.choices:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    data = choice.delta.content
                    mes += data
                    print(data, end='', flush=True)
        print(flush=True)
        return parse_result(mes)
