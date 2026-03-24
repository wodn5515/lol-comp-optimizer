import asyncio
import logging
import time
from collections import deque
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

from domain.ports.external.riot_api_port import RiotApiPort

ASIA_BASE = "https://asia.api.riotgames.com"
KR_BASE = "https://kr.api.riotgames.com"


class SlidingWindowRateLimiter:
    """Sliding window rate limiter with two windows:
    - 1-second window: max 18 requests (margin from 20 limit)
    - 2-minute window: max 95 requests (margin from 100 limit)
    """

    def __init__(
        self,
        short_window_max: int = 18,
        short_window_seconds: float = 1.0,
        long_window_max: int = 95,
        long_window_seconds: float = 120.0,
    ) -> None:
        self._short_max = short_window_max
        self._short_window = short_window_seconds
        self._long_max = long_window_max
        self._long_window = long_window_seconds
        self._short_timestamps: deque[float] = deque()
        self._long_timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    def _clean_window(self, timestamps: deque[float], window_seconds: float) -> None:
        now = time.monotonic()
        while timestamps and (now - timestamps[0]) >= window_seconds:
            timestamps.popleft()

    async def wait_if_needed(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self._clean_window(self._short_timestamps, self._short_window)
                self._clean_window(self._long_timestamps, self._long_window)

                short_ok = len(self._short_timestamps) < self._short_max
                long_ok = len(self._long_timestamps) < self._long_max

                if short_ok and long_ok:
                    self._short_timestamps.append(now)
                    self._long_timestamps.append(now)
                    return

                # Calculate how long to wait
                wait_time = 0.0
                if not short_ok and self._short_timestamps:
                    wait_time = max(
                        wait_time,
                        self._short_window - (now - self._short_timestamps[0]) + 0.01,
                    )
                if not long_ok and self._long_timestamps:
                    wait_time = max(
                        wait_time,
                        self._long_window - (now - self._long_timestamps[0]) + 0.01,
                    )

                if wait_time > 0:
                    await asyncio.sleep(wait_time)


class RiotApiClient(RiotApiPort):
    """Riot API HTTP client with rate limiting.

    - Account-v1, Match-v5 -> asia.api.riotgames.com
    - Summoner-v4, League-v4, Mastery-v4 -> kr.api.riotgames.com
    """

    def __init__(self, rate_limiter: SlidingWindowRateLimiter | None = None) -> None:
        self._client = httpx.AsyncClient(timeout=15.0)
        self._rate_limiter = rate_limiter or SlidingWindowRateLimiter()

    async def _request(
        self, base_url: str, path: str, api_key: str
    ) -> httpx.Response:
        await self._rate_limiter.wait_if_needed()
        headers = {"X-Riot-Token": api_key}
        url = f"{base_url}{path}"
        resp = await self._client.get(url, headers=headers)

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "1"))
            await asyncio.sleep(retry_after)
            return await self._request(base_url, path, api_key)

        return resp

    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str, api_key: str
    ) -> dict | None:
        encoded_name = quote(game_name, safe='')
        encoded_tag = quote(tag_line, safe='')
        resp = await self._request(
            ASIA_BASE,
            f"/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}",
            api_key,
        )
        if resp.status_code == 200:
            return resp.json()
        return None

    async def get_summoner_by_puuid(
        self, puuid: str, api_key: str
    ) -> dict | None:
        resp = await self._request(
            KR_BASE,
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}",
            api_key,
        )
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Summoner response keys: {list(data.keys())}")
            return data
        logger.warning(f"Summoner API returned {resp.status_code}: {resp.text[:200]}")
        return None

    async def get_league_entries(
        self, summoner_id: str, api_key: str
    ) -> list[dict]:
        resp = await self._request(
            KR_BASE,
            f"/lol/league/v4/entries/by-summoner/{summoner_id}",
            api_key,
        )
        if resp.status_code == 200:
            return resp.json()
        return []

    async def get_match_ids(
        self, puuid: str, count: int, queue: int | None, api_key: str,
        match_type: str | None = None,
    ) -> list[str]:
        params = f"count={count}"
        if match_type:
            params += f"&type={match_type}"
        elif queue:
            params += f"&queue={queue}"
        resp = await self._request(
            ASIA_BASE,
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids?{params}",
            api_key,
        )
        if resp.status_code == 200:
            return resp.json()
        return []

    async def get_match_detail(
        self, match_id: str, api_key: str
    ) -> dict | None:
        resp = await self._request(
            ASIA_BASE,
            f"/lol/match/v5/matches/{match_id}",
            api_key,
        )
        if resp.status_code == 200:
            return resp.json()
        return None

    async def get_champion_masteries(
        self, puuid: str, top: int, api_key: str
    ) -> list[dict]:
        resp = await self._request(
            KR_BASE,
            f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count={top}",
            api_key,
        )
        if resp.status_code == 200:
            return resp.json()
        return []

    async def close(self) -> None:
        await self._client.aclose()
