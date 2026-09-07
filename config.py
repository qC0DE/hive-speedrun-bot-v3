# -*- coding: utf-8 -*-
import json
import logging
import os
import requests

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("config")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# 基本設定・環境変数（シークレット・ローカルパス）
# ------------------------------------------------------------
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
DEV_GUILD_ID = os.environ.get("DEV_GUILD_ID", "")

CACHE_DIR = os.environ.get("CACHE_DIR", os.path.join(BASE_DIR, "cache"))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(BASE_DIR, "fonts"))
FONT_MOJANGLES = os.path.join(FONT_DIR, "Mojangles.ttf")
FONT_UNIFONT = os.path.join(FONT_DIR, "Unifont.ttf")

LOCAL_CONFIG_CACHE = os.path.join(CACHE_DIR, "remote_config_backup.json")

# GitHubのURL（通常URLでもRaw URLでも対応可能）
REMOTE_CONFIG_URL = os.environ.get(
    "REMOTE_CONFIG_URL",
    "https://raw.githubusercontent.com/qC0DE/speedrun-bot-config/main/config.json",
)

# ------------------------------------------------------------
# 固定デフォルト値（UIレイアウトなど）
# ------------------------------------------------------------
BOT_NAME = "Hive Speedrun Leaderboard"
BOT_VERSION = "2.1.0"
BOT_ACTIVITY_TEXT = "/speedrun | Gravity Leaderboard by Yytanuki | Super thanks: lyger | Hosted by qC0DE"

DEFAULT_BACKGROUND_URL = "https://i.imgur.com/1gY2pA4.png"
GAME_NAME = "The Hive"
GAME_ID = "hive"
CATEGORY_NAME = "Gravity"
JP_COUNTRY_CODE = "JP"
CACHE_TTL_MINUTES = 60

IMAGE_WIDTH = 1010
ROW_HEIGHT = 68
HEADER_HEIGHT = 170
FOOTER_HEIGHT = 30
PADDING = 14
ROWS_PER_PAGE = 10
MAX_ROWS_WORLD_DISPLAY = 40
MAX_ROWS_JP_DISPLAY = 20
MAX_ROWS_REGION_DISPLAY = 20

LOGO_URL = "https://playhive.com/_next/static/media/Hive.9ce7fa58.png"
LOGO_HEIGHT = 34
BACKGROUND_BLUR_RADIUS = 4
BACKGROUND_DARKEN_ALPHA = 130

COLORS = {
    "panel_bg": (14, 18, 28, 235),
    "panel_border": (40, 46, 58, 255),
    "row_bg_a": (30, 38, 52, 200),
    "row_bg_b": (22, 28, 40, 200),
    "header_tab_bg": (18, 22, 32, 255),
    "header_tab_border": (60, 66, 80, 255),
    "title_cyan": (85, 210, 235, 255),
    "title_green": (85, 220, 100, 255),
    "col_header_pos": (240, 140, 130, 255),
    "col_header_white": (255, 255, 255, 255),
    "col_header_green": (95, 220, 105, 255),
    "col_header_red": (225, 90, 90, 255),
    "text_white": (240, 240, 240, 255),
    "rank_gold": (255, 215, 60, 255),
    "rank_silver": (200, 205, 210, 255),
    "rank_bronze": (190, 120, 70, 255),
    "rank_other": (235, 140, 140, 255),
    "player_name": (230, 230, 235, 255),
    "time_lightgreen": (150, 230, 90, 255),
    "date_darkgreen": (60, 140, 75, 255),
    "platform_red": (215, 80, 80, 255),
    "shadow": (0, 0, 0, 160),
}

# 地域表示名
REGION_LABELS = {
    "world": "Overall",
    "jp": "Japan",
    "na": "North America",
    "eu": "Europe",
    "as": "Asia",
    "oc": "Oceania",
    "sa": "South America",
    "af": "Africa",
    "other": "Other",
}

# デフォルトの地域別国コード一覧 (ISO 3166-1 alpha-2)
DEFAULT_REGION_COUNTRIES: dict[str, list[str]] = {
    "na": [
        "us", "ca", "mx", "gl", "bm", "pm", "bz", "cr", "sv", "gt", "hn",
        "ni", "pa", "ag", "bs", "bb", "cu", "dm", "do", "gd", "ht", "jm",
        "kn", "lc", "vc", "tt", "aw", "ai", "vg", "vi", "ky", "cw", "gp",
        "mq", "ms", "pr", "bl", "mf", "sx", "tc", "bq"
    ],
    "eu": [
        "gb", "uk", "de", "fr", "it", "es", "pt", "nl", "be", "ch", "at",
        "se", "no", "fi", "dk", "ie", "pl", "cz", "sk", "hu", "ro", "bg",
        "gr", "hr", "rs", "ba", "si", "me", "mk", "al", "ee", "lv", "lt",
        "ua", "by", "md", "ru", "is", "mt", "cy", "lu", "ad", "li", "mc",
        "sm", "va", "fo", "gi", "ax", "gg", "je", "im"
    ],
    "as": [
        "jp", "cn", "kr", "kp", "tw", "hk", "mo", "vn", "th", "id", "my",
        "ph", "sg", "in", "pk", "bd", "lk", "np", "bt", "mv", "ir", "iq",
        "sa", "ae", "qa", "kw", "om", "ye", "sy", "jo", "lb", "il", "ps",
        "tr", "ge", "am", "az", "kz", "uz", "tm", "kg", "tj", "mn", "mm",
        "kh", "la", "bn", "tl"
    ],
    "oc": [
        "au", "nz", "pg", "fj", "sb", "vu", "ws", "to", "tv", "nr", "ki",
        "pw", "fm", "mh", "ck", "nu", "tk", "wf", "pf", "nc", "as", "gu", "mp"
    ],
    "sa": [
        "br", "ar", "cl", "co", "pe", "ve", "ec", "bo", "py", "uy", "gy", "sr", "gf", "fk"
    ],
    "af": [
        "za", "eg", "ng", "ke", "ma", "gh", "tz", "ug", "dz", "sd", "et",
        "ao", "mz", "mg", "cm", "ci", "sn", "zw", "tn", "cd", "cg", "bw",
        "na", "zm", "rw", "so", "ly", "ml", "mw", "gn", "td", "sl", "bi",
        "bj", "tg", "mr", "er", "ga", "lr", "cf", "dj", "gq", "ls", "sz",
        "km", "cv", "st", "sc", "mu", "ss"
    ],
}

# 動的設定（config.jsonから注入）
JP_WHITELIST: set[str] = set()
DIVISIONS: dict[str, dict] = {}
REGION_COUNTRIES: dict[str, set[str]] = {k: set(v) for k, v in DEFAULT_REGION_COUNTRIES.items()}


def _to_raw_url(url: str) -> str:
    """GitHubの通常URLをRaw URLに変換"""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url


def _apply_config_data(data: dict) -> None:
    """取得した辞書データを反映"""
    global BOT_NAME, BOT_VERSION, BOT_ACTIVITY_TEXT
    global DEFAULT_BACKGROUND_URL, GAME_NAME, GAME_ID, CATEGORY_NAME
    global JP_COUNTRY_CODE, CACHE_TTL_MINUTES, LOGO_URL
    global JP_WHITELIST, DIVISIONS, REGION_COUNTRIES

    if "bot_name" in data:
        BOT_NAME = data["bot_name"]
    if "bot_version" in data:
        BOT_VERSION = data["bot_version"]
    if "bot_activity_text" in data:
        BOT_ACTIVITY_TEXT = data["bot_activity_text"]
    if "default_background_url" in data:
        DEFAULT_BACKGROUND_URL = data["default_background_url"]
    if "game_name" in data:
        GAME_NAME = data["game_name"]
    if "game_id" in data:
        GAME_ID = data["game_id"]
    if "category_name" in data:
        CATEGORY_NAME = data["category_name"]
    if "jp_country_code" in data:
        JP_COUNTRY_CODE = data["jp_country_code"]
    if "cache_ttl_minutes" in data:
        CACHE_TTL_MINUTES = data["cache_ttl_minutes"]
    if "logo_url" in data:
        LOGO_URL = data["logo_url"]

    # ホワイトリスト反映（環境変数とJSONをマージ）
    whitelist = set()
    env_wl = os.environ.get("JP_WHITELIST", "")
    if env_wl:
        whitelist.update(name.strip().lower() for name in env_wl.split(",") if name.strip())

    remote_wl = data.get("jp_whitelist", [])
    if isinstance(remote_wl, list):
        whitelist.update(name.strip().lower() for name in remote_wl if name.strip())
    elif isinstance(remote_wl, str):
        whitelist.update(name.strip().lower() for name in remote_wl.split(",") if name.strip())

    JP_WHITELIST.clear()
    JP_WHITELIST.update(whitelist)

    # 部門・マップ一覧反映
    if "divisions" in data and isinstance(data["divisions"], dict):
        DIVISIONS.clear()
        DIVISIONS.update(data["divisions"])

    # 地域別国コードリスト反映（JSONに定義があればマージ）
    if "region_countries" in data and isinstance(data["region_countries"], dict):
        for reg, codes in data["region_countries"].items():
            reg_lower = reg.lower()
            if isinstance(codes, list):
                REGION_COUNTRIES[reg_lower] = {c.strip().lower() for c in codes}


def reload_config() -> bool:
    """GitHubから設定JSONを取得して適用する"""
    url = _to_raw_url(REMOTE_CONFIG_URL)
    data = None

    try:
        logger.info("GitHubから設定JSONを取得中: %s", url)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # ローカルバックアップ保存
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(LOCAL_CONFIG_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

        logger.info("GitHubからの設定読み込みに成功しました。")

    except Exception as e:
        logger.warning("GitHubからの設定取得に失敗しました (%s)。ローカルキャッシュを試行します。", e)
        if os.path.exists(LOCAL_CONFIG_CACHE):
            try:
                with open(LOCAL_CONFIG_CACHE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("ローカルのバックアップ設定を読み込みました。")
            except Exception as read_err:
                logger.error("ローカルバックアップの読み込みにも失敗しました: %s", read_err)

    if data:
        _apply_config_data(data)
        return True
    return False


# 初回インポート時に実行
reload_config()
