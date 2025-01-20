import httpx
from .config import Config
from .gpt import TmdbData


class TmdbClient:
    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._client = httpx.AsyncClient(proxy=cfg.proxy, base_url='https://api.themoviedb.org', headers={'Authorization': f'Bearer {cfg.tmdb_api_key}'})

    async def get_series_info(self, tmdb_id: int):
        return (await self._client.get(f'/3/tv/{tmdb_id}', params=self.get_params())).json()

    async def get_series_episodes(self, tmdb_id: int, season_number: int):
        return (await self._client.get(f'/3/tv/{tmdb_id}/season/{season_number}', params=self.get_params())).json()

    def get_params(self):
        params = {}
        language = self._cfg.tmdb_language
        if language:
            params['language'] = language
        return params

    async def get_tmdb_data(self, tmdb_id: int, season_number: int = None) -> TmdbData:
        series_info = await self.get_series_info(tmdb_id)
        seasons_info = {}
        for season in series_info["seasons"]:
            nseason_number = season["season_number"]
            if season_number is not None and nseason_number != 0 and nseason_number != season_number:
                continue
            seasons_info[nseason_number] = await self.get_series_episodes(tmdb_id, nseason_number)
        return TmdbData(series_info=series_info, seasons_info=seasons_info)
