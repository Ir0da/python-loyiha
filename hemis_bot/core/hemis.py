import asyncio
import time

import aiohttp

from .config import CACHE_TTL, LANGUAGE, MAX_CONCURRENCY, REQUEST_TIMEOUT
from .utils import extract_list, page_count


class TokenExpired(Exception):
    pass


class ApiError(Exception):
    pass


_session = None
_sem = asyncio.Semaphore(MAX_CONCURRENCY)
_cache = {}


def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            connector=aiohttp.TCPConnector(limit=20, ttl_dns_cache=300),
        )
    return _session


async def close_session():
    if _session is not None and not _session.closed:
        await _session.close()


def clear_cache(token):
    for key in [k for k in _cache if k[2] == token]:
        del _cache[key]


def _prune():
    now = time.monotonic()
    for key in [k for k, v in _cache.items() if v[0] < now]:
        del _cache[key]


async def get_json(base_url, path, token, params=None, ttl=CACHE_TTL):
    params = {"l": LANGUAGE, **(params or {})}
    key = (base_url, path, token, tuple(sorted(params.items())))

    hit = _cache.get(key)
    if ttl and hit and hit[0] > time.monotonic():
        return hit[1]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with _sem:
        try:
            async with get_session().get(
                f"{base_url}{path}", params=params, headers=headers
            ) as resp:
                if resp.status == 401:
                    raise TokenExpired()
                if resp.status != 200:
                    raise ApiError(f"HTTP {resp.status} ({path})")
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            raise ApiError(f"Serverga ulanishda xatolik: {e}")

    if ttl:
        if len(_cache) > 1000:
            _prune()
        _cache[key] = (time.monotonic() + ttl, data)
    return data


async def get_all(base_url, path, token, params=None, ttl=CACHE_TTL):
    """Ro'yxatni oladi. Sahifalar bo'lsa, qolganlarini parallel yuklaydi."""
    params = params or {}
    first = await get_json(base_url, path, token, params, ttl)
    items = list(extract_list(first))

    pages = page_count(first)
    if pages > 1:
        rest = await asyncio.gather(
            *(
                get_json(base_url, path, token, {**params, "page": p}, ttl)
                for p in range(2, pages + 1)
            )
        )
        for payload in rest:
            items.extend(extract_list(payload))
    return items


async def login(base_url, login_name, password):
    try:
        async with get_session().post(
            f"{base_url}/rest/v1/auth/login",
            json={"login": login_name, "password": password},
        ) as resp:
            data = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        raise ApiError(f"Serverga ulanishda xatolik: {e}")

    if not isinstance(data, dict):
        raise ApiError("Serverdan noto'g'ri javob keldi.")

    inner = data.get("data")
    token = inner.get("token") if isinstance(inner, dict) else None
    return token or data.get("token")