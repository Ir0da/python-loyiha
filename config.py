import os

BASE_URL = os.getenv("HEMIS_STUDENT_URL", "https://student.iiau.uz")
# TEKSHIRING: o'qituvchilar HEMIS manzili boshqa bo'lishi mumkin
TEACHER_BASE_URL = os.getenv("HEMIS_TEACHER_URL", "https://hemis.iiau.uz")

DB_NAME = "database.db"
LANGUAGE = "uz-UZ"
REQUEST_TIMEOUT = 20
MAX_CONCURRENCY = 8   # bir vaqtda ketadigan maksimal so'rovlar
CACHE_TTL = 120       # soniya


def need(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} topilmadi.\n"
            f'PowerShell: $env:{name}="TOKEN"'
        )
    return value