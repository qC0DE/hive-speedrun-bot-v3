# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import io
import logging
import sys
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import cache_manager
import config
from gas_client import GasClientError
from image_generator import generate_leaderboard_image
from scheduler import cache_refresh_loop, run_initial_refresh

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("bot")

# ------------------------------------------------------------
# Discord Bot
# ------------------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

COUNTRY_CHOICES = [
    app_commands.Choice(name="World (all players)", value="world"),
    app_commands.Choice(name="JP (Japan)", value="jp"),
    app_commands.Choice(name="NA (North America)", value="na"),
    app_commands.Choice(name="EU (Europe)", value="eu"),
    app_commands.Choice(name="AS (Asia)", value="as"),
    app_commands.Choice(name="OC (Oceania)", value="oc"),
    app_commands.Choice(name="SA (South America)", value="sa"),
    app_commands.Choice(name="AF (Africa)", value="af"),
    app_commands.Choice(name="Other (unlisted / no country)", value="other"),
]


async def division_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    current_lower = current.strip().lower()

    if not current_lower:
        choices = [
            app_commands.Choice(name="5 Maps", value="5maps"),
            app_commands.Choice(name="5 Maps No Custom Server", value="nocustom"),
            app_commands.Choice(name="Other (please enter map name)", value="_guide_placeholder_"),
        ]
        for key, div_conf in config.DIVISIONS.items():
            if key in ("5maps", "nocustom"):
                continue
            choices.append(app_commands.Choice(name=div_conf["label"], value=key))
            if len(choices) >= 25:
                break
        return choices

    matched_choices = []
    for key, div_conf in config.DIVISIONS.items():
        label = div_conf["label"]
        if current_lower in label.lower() or current_lower in key.lower():
            matched_choices.append(app_commands.Choice(name=label, value=key))
            if len(matched_choices) >= 25:
                break

    return matched_choices


_image_cache: dict[tuple[str, str, int], tuple[float, bytes]] = {}


def _build_message_payload(
    country_key: str, division_key: str, page: int
) -> tuple[
    Optional[discord.File],
    Optional[str],
    Optional["LeaderboardView"],
    Optional[str],
]:
    div_conf = config.DIVISIONS.get(division_key)
    if not div_conf:
        return (None, None, None, "指定されたマップ・部門の設定が見つかりません。")

    page_data = cache_manager.get_page(country_key, division_key, page)
    if page_data is None:
        return (
            None,
            None,
            None,
            "リーダーボードのキャッシュが準備できていません。少し時間をおいて再度お試しください。",
        )

    entries = page_data["entries"]
    updated_at = page_data["updated_at"]
    current_page = page_data["page"]
    max_page = page_data["max_page"]

    cache_key = (country_key, division_key, current_page)

    if cache_key in _image_cache and _image_cache[cache_key][0] == updated_at:
        image_bytes = _image_cache[cache_key][1]
    else:
        try:
            image = generate_leaderboard_image(
                entries=entries,
                division_label=div_conf["label"],
                country=country_key,
                background_url=div_conf.get("background_url") or config.DEFAULT_BACKGROUND_URL,
                page=current_page,
                max_page=max_page,
            )

            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            _image_cache[cache_key] = (updated_at, image_bytes)

        except Exception:
            logger.exception("画像生成中にエラーが発生しました。")
            return (None, None, None, "画像の生成中にエラーが発生しました。しばらくしてから再度お試しください。")

    updated_str = dt.datetime.fromtimestamp(
        updated_at, tz=dt.timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    tab_label = config.REGION_LABELS.get(country_key.lower(), country_key.upper())
    range_start = (current_page - 1) * config.ROWS_PER_PAGE + 1
    range_end = range_start + len(entries) - 1
    range_label = f"{range_start}-{range_end}th" if entries else "データなし"

    content = (
        f"**{tab_label} - Gravity {div_conf['label']}** （{range_label}）\n"
        f"-# キャッシュ更新: {updated_str}（30分毎に自動更新）"
    )

    file = discord.File(fp=io.BytesIO(image_bytes), filename="leaderboard.png")
    view = LeaderboardView(country_key, division_key, current_page, max_page) if max_page > 1 else None

    return file, content, view, None


class LeaderboardView(discord.ui.View):

    def __init__(self, country_key: str, division_key: str, current_page: int, max_page: int):
        super().__init__(timeout=600)
        self.country_key = country_key
        self.division_key = division_key
        self.current_page = current_page
        self.max_page = max_page
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.clear_items()
        for p in range(1, self.max_page + 1):
            range_start = (p - 1) * config.ROWS_PER_PAGE + 1
            range_end = p * config.ROWS_PER_PAGE
            self.add_item(
                _PageButton(
                    label=f"{range_start}-{range_end}th",
                    target_page=p,
                    is_current=(self.current_page == p),
                    view_ref=self,
                )
            )

    async def switch_page(self, interaction: discord.Interaction, target_page: int) -> None:
        file, content, new_view, error = _build_message_payload(
            self.country_key, self.division_key, target_page
        )

        if error:
            if not interaction.response.is_done():
                await interaction.response.send_message(error, ephemeral=True)
            else:
                await interaction.followup.send(error, ephemeral=True)
            return

        await interaction.response.edit_message(
            content=content, attachments=[file], view=new_view
        )


class _PageButton(discord.ui.Button):

    def __init__(self, label: str, target_page: int, is_current: bool, view_ref: LeaderboardView):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary if is_current else discord.ButtonStyle.secondary,
            disabled=is_current,
        )
        self.target_page = target_page
        self.view_ref = view_ref
        self.last_clicked = 0.0

    async def callback(self, interaction: discord.Interaction) -> None:
        now = time.time()
        if now - self.last_clicked < 1.5:
            await interaction.response.send_message(
                "ボタンを連打しないでください。少し待ってから再度押してください。", ephemeral=True
            )
            return
        self.last_clicked = now
        await self.view_ref.switch_page(interaction, self.target_page)


@bot.event
async def on_ready() -> None:
    logger.info("Botとしてログインしました: %s", bot.user)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name=config.BOT_ACTIVITY_TEXT
        )
    )
    try:
        if config.DEV_GUILD_ID:
            guild = discord.Object(id=int(config.DEV_GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            logger.info("スラッシュコマンドをギルド限定で同期しました (%d件)", len(synced))
        else:
            synced = await bot.tree.sync()
            logger.info("スラッシュコマンドをグローバル同期しました (%d件)", len(synced))
    except discord.DiscordException:
        logger.exception("スラッシュコマンドの同期に失敗しました。")

    if not cache_refresh_loop.is_running():
        await run_initial_refresh()
        cache_refresh_loop.start()
        logger.info("定期キャッシュ更新ループを開始しました。")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    original = getattr(error, "original", error)

    if isinstance(original, discord.HTTPException) and original.status == 429:
        retry_after = getattr(original, "retry_after", 5.0)
        message = f"⚠️ 一時的に制限されています。約 **{int(retry_after) + 1}秒後** に再度お試しください。"
    else:
        logger.exception("スラッシュコマンド実行中にエラーが発生しました。", exc_info=error)
        message = "予期しないエラーが発生しました。"

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.tree.command(
    name="speedrun", description="The Hive Gravityカテゴリのリーダーボードを表示します。"
)
@app_commands.describe(
    country="対象地域・プレイヤー（world / jp / na / eu / as / oc / sa / af / other）",
    division="部門・マップ名（5maps / nocustom / 各種マップ）",
)
@app_commands.choices(country=COUNTRY_CHOICES)
@app_commands.autocomplete(division=division_autocomplete)
@app_commands.checks.cooldown(1, 5.0)
# --- DMおよびユーザーインストール対応の設定 ---
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def speedrun_command(
    interaction: discord.Interaction,
    country: app_commands.Choice[str],
    division: str,
) -> None:
    if division == "_guide_placeholder_":
        await interaction.response.send_message(
            "個別マップを表示するには、文字を入力して表示される候補からマップを選択してください。",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)

    country_key = country.value
    division_key = division.strip()

    if division_key not in config.DIVISIONS:
        matched = next(
            (k for k, v in config.DIVISIONS.items() if v["label"].lower() == division_key.lower()),
            None,
        )
        if matched:
            division_key = matched
        else:
            await interaction.followup.send("指定されたマップが見つかりませんでした。入力候補から選択してください。")
            return

    file, content, view, error = _build_message_payload(country_key, division_key, page=1)
    if error:
        await interaction.followup.send(error)
        return

    if view is not None:
        await interaction.followup.send(content=content, file=file, view=view)
    else:
        await interaction.followup.send(content=content, file=file)


@speedrun_command.error
async def speedrun_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"このコマンドはクールダウン中です。あと **{error.retry_after:.1f}秒** 後にお試しください。",
            ephemeral=True,
        )


@bot.tree.command(
    name="speedrun_refresh",
    description="（管理者向け）GitHubの設定とspeedrun.comのデータを即時再取得し、キャッシュを更新します。",
)
@app_commands.checks.has_permissions(administrator=True)
# --- サーバー限定（DM・ユーザーインストール不可）の設定 ---
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
async def speedrun_refresh_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        config.reload_config()
        cache_manager.trigger_gas_refresh()
        await cache_manager.refresh_all()
    except GasClientError as e:
        logger.error("手動更新中にAPIエラーが発生しました: %s", e)
        await interaction.followup.send(f"データ取得側でエラーが発生しました: {e}", ephemeral=True)
        return
    except Exception:
        logger.exception("手動キャッシュ更新中にエラーが発生しました。")
        await interaction.followup.send("キャッシュ更新中にエラーが発生しました。", ephemeral=True)
        return

    await interaction.followup.send("GitHubの設定とspeedrun.comのデータを再取得し、キャッシュを更新しました。", ephemeral=True)


@speedrun_refresh_command.error
async def speedrun_refresh_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
    else:
        logger.exception("speedrun_refresh コマンドでエラーが発生しました。", exc_info=error)
        msg = "予期しないエラーが発生しました。"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


def main() -> None:
    if not config.DISCORD_TOKEN:
        logger.error("Environment variable DISCORD_TOKEN is not set. Cannot start bot.")
        sys.exit(1)

    logger.info("%s v%s を起動します。", config.BOT_NAME, config.BOT_VERSION)
    bot.run(config.DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
