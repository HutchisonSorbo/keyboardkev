# =============================================================================
# COACHBOT CONFIGURATION FILE
# Edit values here to customise the bot. Restart the bot after any changes.
# When hosted on Render.com, push changes to GitHub to trigger a redeploy.
# =============================================================================

# -----------------------------------------------------------------------------
# SERVER SETTINGS
# -----------------------------------------------------------------------------

# The name of your Discord server (used in messages)
SERVER_NAME = "Keyboard Coaches"

# Bot display name (shown in /help and welcome messages)
BOT_NAME = "Keyboard Kev"

# Prefix for legacy text commands (slash commands are preferred, this is backup)
PREFIX = "!"

# -----------------------------------------------------------------------------
# CHANNEL NAMES
# These must exactly match your Discord channel names (case sensitive)
# -----------------------------------------------------------------------------

# Channel for lineup reminders and AFL news
AFL_CHANNEL = "afl-fantasy"

# Channel where injury updates are posted automatically
INJURY_CHANNEL = "afl-injuries"

# Channel where general AFL news is posted automatically
NEWS_CHANNEL = "afl-news"

# Channel where scores are posted
SCORES_CHANNEL = "scores"

# Channel for welcome messages when new members join
WELCOME_CHANNEL = "welcome"

# Channel where moderation actions are logged
MOD_LOG_CHANNEL = "mod-log"

# Channel for general banter and fun commands
GENERAL_CHANNEL = "the-commentary-box"

# Set to None to allow bot commands in any channel
ALLOWED_COMMAND_CHANNELS = None

# -----------------------------------------------------------------------------
# LOCKOUT LARRY - Lineup Reminder Settings
# -----------------------------------------------------------------------------

# Timezone for all scheduling (uses pytz timezone names)
TIMEZONE = "Australia/Melbourne"

# First reminder time (when teams drop) - 24hr format
FIRST_REMINDER_HOUR = 18       # 6:00 PM
FIRST_REMINDER_MINUTE = 0

# Final lockout warning time - 24hr format
FINAL_REMINDER_HOUR = 19       # 7:00 PM
FINAL_REMINDER_MINUTE = 50

# Edit these messages to change what Larry says
FIRST_REMINDER_MESSAGE = "🚨 **TEAMS DROP IN 20 MINS!** Righto coaches, final checks. Make sure your structures hold up and check the emergencies. Don't let a late out ruin your weekend. Grab a frothy and lock it in."
FINAL_REMINDER_MESSAGE = "⏰ **FINAL WARNING - 10 MINS 'TIL LOCKOUT.** If you haven't locked your captain yet, what are you doing? Time to put the tools down and let the boys play."

# Set to True to ping @everyone, False to just post the message
PING_EVERYONE = True

# -----------------------------------------------------------------------------
# TRAUMA TRACKER - Injury & News Feed Settings
# -----------------------------------------------------------------------------

# AFL RSS feed URL (free, no key required)
RSS_FEED_URL = "https://www.afl.com.au/rss"

# How often to check for new articles (in minutes)
POLL_INTERVAL_MINUTES = 15

# Only post articles containing at least one of these keywords (case insensitive)
# Add or remove words to control what gets posted
INJURY_KEYWORDS = [
    "injury", "injured", "managed", "test", "late out", "ruled out", "selection",
    "omitted", "recalled", "concussion", "hamstring",
    "knee", "shoulder", "ankle", "calf", "quad", "groin", "suspension", "tribunal"
]

# File to track which articles have already been posted
SEEN_ARTICLES_FILE = "data/seen_articles.json"

# -----------------------------------------------------------------------------
# SQUIGGLE API - Scores and Stats Settings
# AFL data API, free, no key required. https://api.squiggle.com.au
# -----------------------------------------------------------------------------

SQUIGGLE_BASE_URL = "https://api.squiggle.com.au/"

# User-Agent sent with every Squiggle request (required by their fair use policy)
# Change this to your server name
SQUIGGLE_USER_AGENT = "KeyboardCoachesDiscordBot/1.0"

# Cache duration for API responses (seconds). Prevents hammering the free API.
API_CACHE_TTL_SECONDS = 300    # 5 minutes

# Number of recent games to show in a /stats player lookup
RECENT_GAMES_TO_SHOW = 5

# Minimum fuzzy match score for player name search (0-100, higher = stricter)
FUZZY_MATCH_THRESHOLD = 60

# -----------------------------------------------------------------------------
# DRAFT DAY DAVE - Snake Draft Settings
# -----------------------------------------------------------------------------

# Total teams in the league
TOTAL_TEAMS = 8

# Total rounds in the draft
TOTAL_ROUNDS = 23

# Role name required to use admin draft commands like /setteam
DRAFT_ADMIN_ROLE = "Commissioner"

# File where team names and picks are stored
DRAFT_CONFIG_FILE = "data/draft_config.json"

# Default team slot names - update before draft using /setteam or edit here
DEFAULT_TEAMS = [
    "Team 1", "Team 2", "Team 3", "Team 4",
    "Team 5", "Team 6", "Team 7", "Team 8"
]

# -----------------------------------------------------------------------------
# WELCOME - New Member Onboarding
# -----------------------------------------------------------------------------

# Message sent when a new member joins
# Use {member} as a placeholder for the member mention
# Use {server} as a placeholder for the server name
WELCOME_MESSAGE = """🍻 G'day {member}, welcome to **{server}**! Pull up a stool. If you're looking for serious footy chat, head to #afl-fantasy. For everything else, #the-commentary-box is your spot. Have a quick read of #rules-and-prizes before we get started. 

**Quick League Rules:**
1. Keep the banter sharp, but don't overstep the mark. No slurs.
2. We're here to talk footy and fantasy. Have a laugh, crack a beer.
3. Don't spam the chat or tag `@everyone` unless you're the Commissioner.
4. Collusion is an instant red card. 
5. Respect Discord's Terms of Service. Play on."""

# Role automatically assigned to every new member (set to None to disable)
# Must exactly match a role name in your server
DEFAULT_ROLE = "Rookie Coach"

# DM sent to new members on join (set to None to disable DMs)
WELCOME_DM = "G'day mate, welcome to Keyboard Coaches. Type /help in the server to see what I can do. I've got the stats, the advice, and occasionally, a cold beer. Catch ya in the chat."

# -----------------------------------------------------------------------------
# MODERATION - Auto-Mod Settings
# -----------------------------------------------------------------------------

# Role name that is immune to all auto-mod actions
MOD_ROLE = "Commissioner"

# Automatically delete messages containing these words (case insensitive)
# Add words without spaces between them to avoid false positives
BANNED_WORDS = []  # e.g. ["word1", "word2"] - leave empty to disable word filter

# Maximum number of identical or near-identical messages before spam detection triggers
SPAM_MESSAGE_THRESHOLD = 5

# Time window for spam detection (in seconds)
SPAM_TIME_WINDOW_SECONDS = 10

# Maximum number of warnings before automatic kick
WARNINGS_BEFORE_KICK = 3

# Maximum number of warnings before automatic ban
WARNINGS_BEFORE_BAN = 5

# Mute duration in minutes for auto-mod triggered mutes
AUTO_MUTE_MINUTES = 10

# File for storing warning records
WARNINGS_FILE = "data/warnings.json"

# -----------------------------------------------------------------------------
# LEVELLING - XP and Rank System
# -----------------------------------------------------------------------------

# Set to True to enable the XP/levelling system
LEVELLING_ENABLED = True

# XP awarded per message sent
XP_PER_MESSAGE = 15

# Cooldown between XP awards per user (seconds) to prevent spam farming
XP_COOLDOWN_SECONDS = 60

# Channel where level-up announcements are posted (set to None to DM the user)
LEVEL_UP_CHANNEL = "the-commentary-box"

# Level-up message. Use {member} and {level} as placeholders.
LEVEL_UP_MESSAGE = "📈 {member} just leveled up to **Level {level}**! Putting in the hard yards at the selection table. Love to see it."

# Role rewards at specific levels - format: {level_number: "Role Name"}
# Role must already exist in your server. Set to empty dict {} to disable.
LEVEL_ROLE_REWARDS = {
    10: "Veteran Coach",
    20: "Fantasy Legend"
}

# XP data file
XP_DATA_FILE = "data/xp_data.json"

# -----------------------------------------------------------------------------
# POLLS
# -----------------------------------------------------------------------------

# Default poll duration in hours (0 = poll never closes automatically)
DEFAULT_POLL_DURATION_HOURS = 24

# Maximum number of options allowed in a single poll
MAX_POLL_OPTIONS = 8

# Embed colour for polls (hex as integer)
POLL_COLOUR = 0x003087  # AFL blue

# -----------------------------------------------------------------------------
# CUSTOM COMMANDS
# -----------------------------------------------------------------------------

# Role required to add/edit/delete custom commands
CUSTOM_CMD_ADMIN_ROLE = "Commissioner"

# File where custom commands are stored
CUSTOM_COMMANDS_FILE = "data/custom_commands.json"

# Maximum length of a custom command response (characters)
CUSTOM_CMD_MAX_LENGTH = 1000

# -----------------------------------------------------------------------------
# REMINDERS
# -----------------------------------------------------------------------------

# Maximum number of active reminders per user
MAX_REMINDERS_PER_USER = 5

# Maximum reminder duration (in hours)
MAX_REMINDER_HOURS = 168    # 7 days

# -----------------------------------------------------------------------------
# REACTION ROLES
# -----------------------------------------------------------------------------

# Role required to set up reaction role messages
REACTION_ROLE_ADMIN_ROLE = "Commissioner"

# -----------------------------------------------------------------------------
# FUN - Roasts, Coin Flip, 8Ball
# -----------------------------------------------------------------------------

# List of roast messages. Use {target} as placeholder for the mentioned user.
# Add as many as you like. The bot picks one at random.
ROASTS = [
    "{target} is building a list like a bloke who hasn't watched footy since 2018.",
    "I'm looking at {target}'s structure, and I'm honestly perplexed. Guns and spuds anywhere?",
    "If breakevens were IQ tests, {target} would be struggling.",
    "{target}'s trades are more reactionary than talkback radio after a goal review.",
    "Did {target} just throw darts at the rookie list? Absolute chaos.",
    "We need to talk about {target}'s captaincy choices. It's actually hurting to watch.",
    "{target} chased last week's points again. Rookie mistake.",
    "I've seen more value in a watered-down light beer than in {target}'s drafting strategy.",
    "Is {target} trying to build a dynasty or a retirement home? Hard to tell.",
    "Someone tell {target} that 'Time on Ground' actually matters.",
    "{target} holds onto cash cows longer than a farmer in a drought. Upgrade them!",
    "Trading a premium for a sideways mid-pricer? {target} needs to go back to fantasy school.",
    "{target}'s emergencies have scored more than their on-field premiums. Classic.",
    "I'm not sure if {target} is tanking or just genuinely terrible at this.",
    "If {target} paid attention to Centre Bounce Attendances, we wouldn't be having this conversation.",
    "Look, {target} has a plan. It's not a good one, but it's a plan."
]

# The System Prompt used to heavily strictly control how the AI responds to /askkev questions.
KEV_PERSONA_PROMPT = """You are "Keyboard Kev", an incredibly knowledgeable, witty, and analytical Australian AFL Fantasy veteran modeled after Warnie from DT Talk. 
You are currently responding to a question from a member of the "Keyboard Coaches" fantasy league in their Discord server.

RULES:
1. Speak like a knowledgeable fantasy expert (use terms like 'snout', 'pig', 'CBAs', 'TOG', 'break-evens', 'value', 'cash cows', 'rookies').
2. Keep your answers concise, no longer than 3-4 paragraphs. This is for a Discord chat.
3. Provide data-driven, analytical opinions but deliver them with subtle Australian wit and banter. You can mention having a cold beer ("frothy"), but don't act like a drunk; you are a sharp analyst.
4. Give constructive but firm advice. If a trade is bad, call it out cleanly without resorting to insults. 
5. If the question is NOT about AFL, Australian rules football, or fantasy, politely but firmly steer the conversation back to the footy.

---
LEAGUE CHARTER & RULES (You must know this perfectly):
League Name: Keyboard Coaches
Platform: Keeper Fantasy (keeperfantasy.com)
Teams: 8
Season: 20 regular season rounds + 3 playoff rounds
Roster: 28 players total (18 On-Field, 5 Bench, 5 Emergencies)
On-Field Positions: 5 DEF, 6 MID, 1 RUC, 5 FWD, 1 UTL
Emergencies: 1 for each position. *Critical Rule: Emergencies must play AFTER the position they are covering.*
Scoring: Kick (+3), Handball (+2), Mark (+3), Tackle (+4), Hitout (+1), Goal (+6), Behind (+1), Free For (+1), Free Against (-3). Captains score 2x points.
Keepers: Teams must keep minimum 10, maximum 14 players for the following season. Deadline is 1 week before the draft.
Draft: Snake draft. Order is reverse standings (last place picks first). Draft length depends on how many keepers a team kept (everyone drafts until they reach 28 players).
Lockouts: Lineups, captains, and waivers ALL lock at the start of the FIRST GAME of the round (usually Thursday ~7pm AEDT).
Waivers: Priority system based on reverse standings. Resets weekly. Processes Wednesday 11:59pm AEDT.
Trades: No trade deadline. Vetoes require 5 of 8 votes. 3 days to respond to offers.
Playoffs: Top 6 teams make finals. Seeds 1 & 2 get a bye. Seeding based on Win/Loss, then Percentage (Points For / Points Against).
Commissioner: Ryan (Contact via Facebook Messenger or 0422 244 115)
"""

# Specific roasts for live draft picks. Use {team} and {player} placeholders.
DRAFT_ROASTS = [
    "{team} goes with {player}. That's certainly a choice. A confusing one, but a choice.",
    "Reaching for {player} there, {team}. Must be seeing some pre-season role change the rest of us missed.",
    "Look, {player} has upside, but drafting them here is paying overs, {team}.",
    "{team} locking in {player}. Hope they've got good bench depth.",
    "Classic {team} pick. Ignoring the stats and going on vibes with {player}.",
    "I'd have waited another two rounds for {player}, but {team} clearly didn't want to risk it.",
    "{team} taking {player} confirms we're officially in the speculative phase of the draft.",
    "Not sure the Time on Ground numbers justify drafting {player} this early, {team}.",
    "That is a very bold value call from {team} taking {player} here.",
    "Hope {team} enjoys {player}'s rollercoaster scoring this year. Better buckle up."
]

# Random verdicts for /kev_verdict. 
KEV_VERDICTS = [
    "Look, you're paying pure overs there. The value just isn't right.",
    "That's a genuine lock and load. Put the 'C' on him while you're at it.",
    "I'm keeping a close eye on the CBAs, but right now, I wouldn't touch that.",
    "If he gets the midfield minutes, it's a genius move. If he gets stuck on a flank, you're cooked.",
    "Pigs get fed, hogs get slaughtered. Don't get greedy, take the safe points.",
    "Honestly, I don't hate it. It's a calculated risk with decent upside.",
    "That's a sideways trade if I've ever seen one. Save your picks.",
    "You have to back your structure. Don't blow up the list for one bloke.",
    "Take the value while you can get it. He's ripe for the picking.",
    "Check the break-even first. You might be buying at absolute peak price."
]

# Rulebook definitions for /rulebook
RULEBOOK = {
    "snake": "**Snake Draft:** The draft snakes back and forth. Last place picks first in Round 1, then last in Round 2, first in Round 3, and so on. Balances the rookie intake nicely.",
    "keeper": "**Keepers:** You need to keep a minimum of 10, maximum of 14 players from your final 2026 roster. The deadline is exactly one week before draft day. Review your lists carefully.",
    "scoring": "**Scoring System:** Standard AFL Fantasy. K: 3, B: 1, M: 3, T: 4, HO: 1, FA: -3, FF: 1, G: 6, B: 1. Captain gets 2x. No loopholes allowed if the game has already started on-field.",
    "trades": "**Trades:** No trade deadline. The Commissioner can step in for clear collusion, but mostly, we let the market dictate value. Remember, 5 vetos will cancel a trade.",
    "waivers": "**Waivers:** Reverse standings order, resetting every week. Processing happens on Wednesday nights at 11:59pm. Set your claims early.",
    "emergencies": "**Emergencies (The Golden Rule):** You get 1 emergency per position. Your emergency MUST play their game AFTER the player they are covering, otherwise their score cannot substitute. Lock it in."
}

# Magic 8 Ball responses. Add or remove as you like.
EIGHT_BALL_RESPONSES = [
    "The data points to yes. Back it in.",
    "The stats don't support it, mate.",
    "Upside is there, but wait for team sheets.",
    "Ask me again after the Friday lockout.",
    "The fantasy gods say no.",
    "Absolutely. Lock and load.",
    "I'm looking at the numbers and it's a pass from me.",
    "Yes, the value is undeniable.",
    "Doubtful. Too much role risk.",
    "Look at the breakeven... it's a solid maybe.",
    "It is certain. Don't overthink it.",
    "Outlook is grim. Look elsewhere.",
    "Yes, get it done before the price rises.",
    "Reply hazy, wait for the coach's presser.",
    "Better not risk it with your current structure."
]

# Coin flip responses
COIN_HEADS_RESPONSES = [
    "Heads! 🪙 Back the data, mate.",
    "Heads! 🪙 Secure the points.",
    "HEADS! 🪙 Follow your gut structure."
]
COIN_TAILS_RESPONSES = [
    "Tails! 🪙 There's your answer.",
    "Tails! 🪙 Don't look back now.",
    "TAILS! 🪙 The coin has spoken, make the move."
]

# -----------------------------------------------------------------------------
# EMBED COLOURS (hex as integers)
# -----------------------------------------------------------------------------

COLOUR_AFL = 0xFF6600         # AFL orange
COLOUR_SCORES = 0x003087      # AFL blue
COLOUR_STATS = 0x00A550       # Green
COLOUR_DRAFT = 0xFFD700       # Gold
COLOUR_MOD = 0xFF0000         # Red
COLOUR_WELCOME = 0x00BFFF     # Light blue
COLOUR_FUN = 0xFF69B4         # Hot pink
COLOUR_HELP = 0x7289DA        # Discord blurple
COLOUR_LEVEL = 0xFFD700       # Gold
COLOUR_REMINDER = 0x9B59B6    # Purple
