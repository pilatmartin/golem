import os

from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(verbose=True)


@dataclass(frozen=True)
class AppConfig:
    database_url: str = os.environ.get("DATABASE_URL")


app_config = AppConfig()
