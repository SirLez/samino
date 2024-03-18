import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text()

setup(
    name="samino",
    version="2.5.8",
    url="https://github.com/SirLez/SAmino",
    download_url="https://github.com/SirLez/SAmino/archive/refs/heads/main.zip",
    description="Amino Bots with python!",
    long_description=README,
    long_description_content_type="text/markdown",
    author="SirLez",
    author_email="botsirlez@gmail.com",
    license="MIT",
    keywords=[
        "api",
        "python",
        "python3",
        "python3.x",
        "SirLez",
        "Bovonos",
        "Amino",
        "samino",
        "samino py"
        "S-Amino",
        "samino",
        "samino",
        "samino-bot",
        "samino-bots",
        "samino-bot",
        "ndc",
        "narvii.apps",
        "aminoapps",
        "samino-py",
        "samino",
        "samino-bot",
        "narvii",
    ],
    include_package_data=True,
    install_requires=[
        "JSON_minify",
        "setuptools",
        "httpx",
        "websocket-client==1.3.1",
        "websockets",
        "ujson",
        "aiohttp"
    ],
    setup_requires=["wheel"],
    packages=find_packages(),
)
