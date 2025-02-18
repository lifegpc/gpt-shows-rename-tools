import argparse
import openai
import os.path
from typing import List, Optional
import yaml


DEFAULT_EXTS = ['.mp4', '.mkv', '.ass', '.srt']


class Config:
    def __init__(self, args: argparse.Namespace, yaml_config: dict):
        self._args = args
        self._yaml_config = yaml_config

    @property
    def api_key(self) -> str:
        api_key = self._args.api_key if self._args.api_key is not None else self._yaml_config.get('api_key')
        if not api_key:
            raise ValueError("API key is required")
        return api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._args.base_url if self._args.base_url is not None else self._yaml_config.get('base_url', 'https://api.openai.com/v1')

    @property
    def exts(self) -> List[str]:
        if self._args.exts:
            return self._args.exts
        exts = self._yaml_config.get('exts')
        if isinstance(exts, str):
            return exts.split(";")
        if isinstance(exts, list):
            aexts = []
            for ext in exts:
                if isinstance(ext, str):
                    aexts.append(ext)
            return aexts
        return DEFAULT_EXTS

    @property
    def hardlink(self) -> bool:
        return self._args.hardlink

    @property
    def input(self) -> str:
        return self._args.input

    @property
    def no_tmdb(self) -> bool:
        return self._args.no_tmdb

    @property
    def output(self) -> str:
        return self._args.output

    @property
    def proxy(self) -> Optional[str]:
        return self._args.proxy if self._args.proxy is not None else self._yaml_config.get('proxy')

    @property
    def season_number(self) -> Optional[int]:
        return self._args.season_number

    @property
    def series_name(self) -> Optional[str]:
        return self._args.series_name

    @property
    def tmdb_api_key(self) -> Optional[str]:
        return self._args.tmdb_api_key if self._args.tmdb_api_key is not None else self._yaml_config.get('tmdb_api_key')

    @property
    def tmdb_language(self) -> Optional[str]:
        return self._args.tmdb_language if self._args.tmdb_language is not None else self._yaml_config.get('tmdb_language')

    @property
    def tmdb_id(self) -> Optional[int]:
        return self._args.tmdb_id

    @property
    def tvdb_id(self) -> Optional[int]:
        return self._args.tvdb_id

    @property
    def model(self) -> str:
        if self._args.model:
            return self._args.model
        return self._yaml_config.get("model", "gpt-4o")

    @property
    def year(self) -> Optional[int]:
        return self._args.year


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='GPT Shows Rename Tool')
    parser.add_argument('--api-key', type=str, help='API key for the GPT service')
    parser.add_argument('--base-url', type=str, help='Base URL for the GPT service')
    parser.add_argument('-p', '--proxy', type=str, help='Proxy URL (optional)')
    parser.add_argument('-m', '--model', type=str, help='Model to use (default: gpt-4o)')
    parser.add_argument('-c', '--config', type=str, default='./config.yml', help='Path to the configuration file')
    parser.add_argument('-s', '--series-name', type=str, help='Series name (optional)')
    parser.add_argument('-Y', '--year', type=int, help='Year of the series (optional)')
    parser.add_argument('--tmdb-api-key', type=str, help='TMDB API key (optional)')
    parser.add_argument('--tmdb-language', type=str, help='TMDB language (optional)')
    parser.add_argument('-t', '--tmdb-id', type=int, help='TMDB ID (optional)')
    parser.add_argument('-T', '--tvdb-id', type=int, help='TVDB ID (optional)')
    parser.add_argument('-H', '--hardlink', action='store_true', help='Use hardlink instead of symlink.')
    parser.add_argument('-n', '--no-tmdb', action='store_true', help='Do not use TMDB API to obtain data.')
    parser.add_argument('-S', '--season-number', type=int, help='Season number (optional)')
    parser.add_argument('-e', '--exts', action='append', help='File extensions to process (optional)')
    parser.add_argument('input', help='Input directory.')
    parser.add_argument('output', help='Output directory.')
    return parser


def load_config():
    parser = get_arg_parser()
    args = parser.parse_intermixed_args()
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    cfg = Config(args, config)
    openai.base_url = cfg.base_url
    openai.api_key = cfg.api_key
    return cfg
