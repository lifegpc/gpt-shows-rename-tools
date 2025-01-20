from .config import load_config
from .file import gen_input_list, link_files
from .gpt import get_response
from .tmdb import TmdbClient
import asyncio


async def main():
    cfg = load_config()
    files = gen_input_list(cfg.input, cfg.exts)
    tmdb_data = None
    if cfg.tmdb_id and not cfg.no_tmdb:
        if not cfg.tmdb_api_key:
            print('WARN: TMDB API key is not set, skip TMDB data integration')
        else:
            tmdb = TmdbClient(cfg)
            tmdb_data = await tmdb.get_tmdb_data(cfg.tmdb_id, cfg.season_number)
    res = await get_response(cfg, cfg.input, files, cfg.series_name, cfg.year, cfg.tmdb_id, cfg.tvdb_id, tmdb_data, cfg.season_number)
    for f in res.files:
        print(files[f.index], '->', f.name)
    input('Continue?')
    link_files(cfg.input, files, res, cfg.output, cfg.hardlink)


asyncio.run(main())
