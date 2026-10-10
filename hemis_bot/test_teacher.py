import asyncio
import getpass
import json

from core.config import TEACHER_BASE_URL
from core.hemis import close_session, get_json, login
from teacher.api import PATHS


async def main():
    print("Manzil:", TEACHER_BASE_URL)
    user = input("HEMIS login: ")
    password = getpass.getpass("Parol (ko'rinmaydi): ")

    token = await login(TEACHER_BASE_URL, user, password)
    print("Token olindi:", bool(token))
    if not token:
        await close_session()
        return

    for name, path in PATHS.items():
        try:
            data = await get_json(TEACHER_BASE_URL, path, token, ttl=0)
            text = json.dumps(data, ensure_ascii=False)
            print(f"[OK]   {name}: {path} -> {text[:200]}")
        except Exception as e:
            print(f"[XATO] {name}: {path} -> {e}")

    await close_session()


asyncio.run(main())