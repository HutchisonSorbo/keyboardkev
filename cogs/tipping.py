import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime
import pytz

import config
import helpers

log = logging.getLogger("CoachBot.Tipping")


class Tipping(commands.Cog):
    """Pulls AFL tipping predictions from Squiggle (s10 aggregate + Don't Blame the Data)
    and posts them to the #tipping channel on a smart schedule."""

    def __init__(self, bot):
        self.bot = bot
        self.cache = helpers.SimpleCache()
        self.last_preview_round = None     # Track which round we already auto-posted
        self.last_update_round = None
        self.tipping_schedule.start()

    def cog_unload(self):
        self.tipping_schedule.cancel()

    # -------------------------------------------------------------------------
    # Squiggle API helpers
    # -------------------------------------------------------------------------

    async def fetch_tips(self, source_id, year=None, round_num=None):
        """Fetch tips from Squiggle API for a given source."""
        url = f"{config.SQUIGGLE_BASE_URL}?q=tips;source={source_id}"
        if year:
            url += f";year={year}"
        if round_num:
            url += f";round={round_num}"

        cached = self.cache.get(url)
        if cached:
            return cached

        headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}

        try:
            async with self.bot.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache.set(url, data, config.API_CACHE_TTL_SECONDS)
                    return data
                else:
                    log.error(f"Squiggle tips API error: {response.status} for {url}")
                    return None
        except Exception as e:
            log.error(f"Exception fetching Squiggle tips: {e}")
            return None

    async def get_current_round(self, year):
        """Determine the current or next round from the games endpoint."""
        url = f"{config.SQUIGGLE_BASE_URL}?q=games;year={year}"
        
        cached = self.cache.get(url)
        if not cached:
            headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
            try:
                async with self.bot.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        cached = await response.json()
                        self.cache.set(url, cached, config.API_CACHE_TTL_SECONDS)
            except Exception as e:
                log.error(f"Exception fetching games for round detection: {e}")
                return None

        if not cached or "games" not in cached:
            return None

        games = cached["games"]

        # Find the first incomplete game — that's the current round
        for g in games:
            if g.get("complete", 100) < 100:
                return g.get("round")

        # All games complete — return the last round
        if games:
            return games[-1].get("round")
        return None

    # -------------------------------------------------------------------------
    # Embed builder
    # -------------------------------------------------------------------------

    def build_tips_embed(self, s10_tips, dbtd_tips, round_num, year, is_update=False):
        """Build a compact embed combining s10 and DBTD tips for a round."""

        # Index DBTD tips by game ID for easy lookup
        dbtd_by_game = {}
        if dbtd_tips and "tips" in dbtd_tips:
            for t in dbtd_tips["tips"]:
                dbtd_by_game[t.get("gameid")] = t

        title_prefix = "📊 Updated Tips" if is_update else "🏈 Round Tips"
        embed = discord.Embed(
            title=f"{title_prefix} — Round {round_num}, {year}",
            colour=config.COLOUR_TIPPING
        )

        if not s10_tips or "tips" not in s10_tips or not s10_tips["tips"]:
            embed.description = "No tips available for this round yet. Check back closer to game day."
            return embed

        # Sort by game date
        tips_sorted = sorted(s10_tips["tips"], key=lambda t: t.get("date", ""))

        lines = []
        for tip in tips_sorted:
            game_id = tip.get("gameid")
            home = tip.get("hteam", "?")
            away = tip.get("ateam", "?")

            # s10 data
            s10_pick = tip.get("tip", "?")
            s10_margin = tip.get("margin")
            s10_conf = tip.get("confidence")

            s10_text = f"**{s10_pick}**"
            if s10_margin:
                s10_text += f" by {float(s10_margin):.0f}"
            if s10_conf:
                s10_text += f" ({float(s10_conf):.0f}%)"

            # DBTD data
            dbtd_tip = dbtd_by_game.get(game_id)
            if dbtd_tip:
                dbtd_pick = dbtd_tip.get("tip", "?")
                dbtd_margin = dbtd_tip.get("margin")
                dbtd_conf = dbtd_tip.get("confidence")

                dbtd_text = f"**{dbtd_pick}**"
                if dbtd_margin:
                    dbtd_text += f" by {float(dbtd_margin):.0f}"
                if dbtd_conf:
                    dbtd_text += f" ({float(dbtd_conf):.0f}%)"

                # Agreement indicator
                agree = "✅" if s10_pick == dbtd_pick else "⚠️"
            else:
                dbtd_text = "*N/A*"
                agree = "❓"

            # Game date/time
            game_date = tip.get("date", "")
            try:
                dt = datetime.strptime(game_date, "%Y-%m-%d %H:%M:%S")
                tz = pytz.timezone(config.TIMEZONE)
                dt = pytz.utc.localize(dt).astimezone(tz) if dt.tzinfo is None else dt
                date_str = dt.strftime("%a %d %b %I:%M%p").lstrip("0").replace(" 0", " ").replace("AM", "am").replace("PM", "pm")
            except (ValueError, AttributeError):
                date_str = game_date

            venue = tip.get("venue", "")

            lines.append(
                f"{agree} **{home} v {away}**\n"
                f"┣ s10: {s10_text}\n"
                f"┣ DBTD: {dbtd_text}\n"
                f"┗ *{date_str} — {venue}*"
            )

        embed.description = "\n\n".join(lines)

        embed.set_footer(
            text="s10 = Squiggle Top-10 Aggregate | DBTD = Don't Blame the Data\n"
                 "squiggle.com.au • dontblamethedata.com"
        )

        return embed

    # -------------------------------------------------------------------------
    # Slash command: /tips
    # -------------------------------------------------------------------------

    @app_commands.command(name="tips", description="Get AFL tipping predictions from s10 and Don't Blame the Data")
    @app_commands.describe(
        round="Round number (defaults to current/next round)",
        public="Show to everyone in the channel? (Default: No)"
    )
    async def tips_command(self, interaction: discord.Interaction, round: int = None, public: bool = False):
        await interaction.response.defer(ephemeral=not public)

        year = datetime.now().year

        if round is None:
            round = await self.get_current_round(year)
            if round is None:
                await interaction.followup.send("Couldn't determine the current round. Try specifying one: `/tips round:1`")
                return

        # Fetch both sources
        s10_data = await self.fetch_tips(config.SQUIGGLE_S10_SOURCE_ID, year=year, round_num=round)
        dbtd_data = await self.fetch_tips(config.SQUIGGLE_DBTD_SOURCE_ID, year=year, round_num=round)

        embed = self.build_tips_embed(s10_data, dbtd_data, round, year)
        await interaction.followup.send(embed=embed)

    # -------------------------------------------------------------------------
    # Scheduled auto-post
    # -------------------------------------------------------------------------

    @tasks.loop(minutes=30)
    async def tipping_schedule(self):
        """Check if it's time to auto-post tips to #tipping."""
        try:
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)
            year = now.year
            weekday = now.weekday()   # 0=Mon
            hour = now.hour
            minute = now.minute

            current_round = await self.get_current_round(year)
            if current_round is None:
                return

            # Tuesday preview post
            if (weekday == config.TIPPING_PREVIEW_DAY
                    and hour == config.TIPPING_PREVIEW_HOUR
                    and minute < 30
                    and self.last_preview_round != current_round):

                await self._auto_post_tips(current_round, year, is_update=False)
                self.last_preview_round = current_round
                log.info(f"Auto-posted tipping preview for Round {current_round}")

            # Thursday update post (after team sheets)
            if (weekday == 3  # Thursday
                    and hour == config.TIPPING_UPDATE_HOUR
                    and minute >= config.TIPPING_UPDATE_MINUTE
                    and minute < config.TIPPING_UPDATE_MINUTE + 30
                    and self.last_update_round != current_round):

                await self._auto_post_tips(current_round, year, is_update=True)
                self.last_update_round = current_round
                log.info(f"Auto-posted tipping update for Round {current_round}")

        except Exception as e:
            log.error(f"Error in tipping schedule: {e}")

    @tipping_schedule.before_loop
    async def before_tipping_schedule(self):
        await self.bot.wait_until_ready()

    async def _auto_post_tips(self, round_num, year, is_update=False):
        """Post tips embed to #tipping in all guilds."""
        s10_data = await self.fetch_tips(config.SQUIGGLE_S10_SOURCE_ID, year=year, round_num=round_num)
        dbtd_data = await self.fetch_tips(config.SQUIGGLE_DBTD_SOURCE_ID, year=year, round_num=round_num)

        embed = self.build_tips_embed(s10_data, dbtd_data, round_num, year, is_update=is_update)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=config.TIPPING_CHANNEL)
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    log.error(f"Missing permissions to post in #{config.TIPPING_CHANNEL} in {guild.name}")


async def setup(bot):
    await bot.add_cog(Tipping(bot))
