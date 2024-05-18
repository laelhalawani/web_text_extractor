
from pathlib import Path
_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_URL_CONFIG_FILE_PATH = (_PACKAGE_DIR / "url_configs_default.json").resolve()

UNCONFIGURED_URLS_OUTPUT_FILE = "./unconfigured_urls.json"

ERRORED_URLS_OUTPUT_FILE = "./errored_urls.json"