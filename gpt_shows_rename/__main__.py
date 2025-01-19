from .config import load_config
from .file import gen_input_list, link_files
from .gpt import get_response


cfg = load_config()
files = gen_input_list(cfg.input)
res = get_response(cfg, cfg.input, files, cfg.series_name, cfg.year, cfg.tmdb_id, cfg.tvdb_id)
for f in res.files:
    print(files[f.index], '->', f.name)
input('Continue?')
link_files(cfg.input, files, res, cfg.output, cfg.hardlink)
