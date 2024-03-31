from httpx import get

from .SAsync import *
from .acm import Acm
from .client import Client
from .lib.exception import CheckExceptions
from .local import Local

version = "2.6.0"
newest = get("https://pypi.org/pypi/samino/json").json()["info"]["version"]

if version != newest:
    print(f"\033[1;31;33mSAmino New Version!: {newest} (Your Using {version})\033[1;36;33m\nJoin our discord server: \"https://discord.gg/s7qacU5YNX\"\nTtelegram Channel: \"https://t.me/amino_execution\"\033[1;0m")
