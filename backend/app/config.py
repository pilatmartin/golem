import os

from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(verbose=True)


@dataclass(frozen=True)
class AppConfig:
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    def __post_init__(self):
        missing = [name.upper() for name, value in self.__dict__.items() if value in (None, "")]
        if missing:
            raise ValueError(f"Missing environment variable(s): {', '.join(missing)}")

    @classmethod
    def from_env(cls, env_file: str | None = ".env") -> "AppConfig":
        """
        Load environment variables from a .env file.

        Args:
            env_file (str, optional): The path to the .env file. Defaults to ".env".
        Raises:
            ValueError: If required environment variables are missing.
        Returns:
            AppConfig: An instance of AppConfig containing the environment variables.
        """

        load_dotenv(env_file, verbose=True)
        return cls(
            database_url=os.environ.get("DATABASE_URL"),
            secret_key=os.environ.get("SECRET_KEY"),
            algorithm=os.environ.get("ALGORITHM"),
            access_token_expire_minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")),
        )


app_config = AppConfig.from_env()
