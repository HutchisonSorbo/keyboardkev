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
GENERAL_CHANNEL = "general"

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
FIRST_REMINDER_MESSAGE = "🚨 **TEAMS DROP IN 20 MINS!** Righto ya flaming galahs, get your lineups sorted before I finish this pint. Check for late outs and managed players. Don't be that bloke who forgets. Put your bevvy down and set your team."
FINAL_REMINDER_MESSAGE = "⏰ **FINAL WARNING - 10 MINS 'TIL LOCKOUT.** Still haven't set your team? Absolute amateur hour. I'm going back to the bar. 🍻"

# Set to True to ping @everyone, False to just post the message
PING_EVERYONE = True

# -----------------------------------------------------------------------------
# TRAUMA TRACKER - Injury & News Feed Settings
# -----------------------------------------------------------------------------

# AFL RSS feed URL (free, no key required)
RSS_FEED_URL = "https://www.afl.com.au/rss"

# How often to check for new articles (in minutes)
POLL_INTERVAL_MINUTES = 120

# Only post articles containing at least one of these keywords (case insensitive)
# Add or remove words to control what gets posted
INJURY_KEYWORDS = [
    "injury", "injured", "managed", "test", "out", "selection",
    "team", "omitted", "recalled", "concussion", "hamstring",
    "knee", "shoulder", "ankle", "calf", "quad", "groin"
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
WELCOME_MESSAGE = "🍻 G'day {member}, welcome to **{server}**! Pull up a stool at the bar. You've just walked into the most chaotic AFL Fantasy league on the internet. Have a squiz at #rules to see how we operate, and hit up #afl-fantasy for the footy chat. First round is on you. 🍻"

# Role automatically assigned to every new member (set to None to disable)
# Must exactly match a role name in your server
DEFAULT_ROLE = "Coach"

# DM sent to new members on join (set to None to disable DMs)
WELCOME_DM = "G'day mate! Welcome to Keyboard Coaches. Type /help in the server to see what old Kev can do for ya. Catch ya in the banter channel, I'm just heading back to the bar for another schooner. 🍺"

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
LEVEL_UP_CHANNEL = "general"

# Level-up message. Use {member} and {level} as placeholders.
LEVEL_UP_MESSAGE = "🎉 Oooaahh! {member} just hit **Level {level}**! The fantasy rig is looking good... or the luck's holding out. Either way, get this bloke a beer to celebrate! 🍻"

# Role rewards at specific levels - format: {level_number: "Role Name"}
# Role must already exist in your server. Set to empty dict {} to disable.
LEVEL_ROLE_REWARDS = {
    5:  "Rookie Coach",
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
    "Look at {target} out here thinking they can coach. Mate, you couldn't organise a piss-up in a brewery.",
    "{target}'s team last week looked like it was picked by a bloke who's had 12 pints.",
    "I've seen better fantasy decisions from the bloke asleep on the pokies.",
    "{target} keeps saying they have a plan. Yeah, and my local's doing $2 pints. Both are fairy tales.",
    "Rumour has it {target} still hasn't worked out how to set a captain. Fair dinkum.",
    "{target}'s trading record is more tragic than dropping a fresh schnitty on the floor.",
    "If bad trades were beers, {target} would be absolutely written off by Tuesday.",
    "{target} treated the waiver wire like the designated driver. Completely ignored it.",
    "Scientists have confirmed that {target}'s lineup decisions are worse than warm VB.",
    "{target} said they did research at the pub. The research was just drinking.",
    "The only thing lower than {target}'s rank is my glass. Whose shout is it?",
    "{target}'s draft strategy was clearly: close eyes, click, sink a pint, regret everything.",
    "Sources close to {target} confirm they still think Clayton Oliver is worth a first rounder. What a drongo.",
    "{target} and smart trades: name a less iconic duo. I'll wait at the bar.",
    "Breaking news: {target}'s bench scored more than their starting side. I need another drink."
]

# The System Prompt used to heavily strictly control how the AI responds to /askkev questions.
KEV_PERSONA_PROMPT = """You are "Keyboard Kev", an incredibly knowledgeable, overly-opinionated, and very funny Australian pub-goer who knows absolutely everything about the history of the Australian Football League (AFL) and AFL Fantasy. 
You are currently responding to a question from a member of the "Keyboard Coaches" fantasy league in their Discord server.

RULES:
1. Always respond in character. Use Australian slang (mate, fair dinkum, drongo, frothies, etc) but don't overdo it to the point of being unreadable.
2. Keep your answers concise, no longer than 3-4 paragraphs. This is for a Discord chat.
3. If they ask about historical AFL stats, grand finals, or player careers, give them the exact correct information but deliver it with banter.
4. Often reference the fact that you are currently drinking a pint at the pub.
5. If the question is NOT about ALF, Australian rules football, or general sports banter, aggressively tell them to stop asking stupid non-footy questions and get back to managing their fantasy team."""

# Specific roasts for live draft picks. Use {team} and {player} placeholders.
DRAFT_ROASTS = [
    "Really? {player}? {team} must be drinking earlier than me today.",
    "Great pick by {team}. Assuming we teleport back to 2019.",
    "I was gonna say {team} is building a dynasty, but grabbing {player} here is just rebuilding forever.",
    "Wow. {team} just ruined their entire season with one click. Welcome to {player} town.",
    "Oh mate. {player} is going to break {team}'s heart by Round 3. Lock it in.",
    "Did {team} just close their eyes and point? {player} belongs on the waivers.",
    "I actually feel bad for {player}. They have to play for {team} now.",
    "{team} thinks {player} is a premium. The rest of the league thinks {team} is an idiot.",
    "The Keeper App just crashed because it couldn't believe {team} took {player} that high.",
    "Bold strategy from {team} drafting {player}. Let's see if it pays off. Spoiler: It won't."
]

# Magic 8 Ball responses. Add or remove as you like.
EIGHT_BALL_RESPONSES = [
    "Yeah nah, absolutely yes. Back yourself.",
    "Tell 'em they're dreaming. Not a chance.",
    "Signs point to yes, but knowing your luck...",
    "Ask me again after I've finished this pint.",
    "The footy gods say no, mate.",
    "Hussle up, definitely yes.",
    "My mates at the pub say no, and they watch way more footy than you.",
    "Without a shadow of a doubt.",
    "Yeah nah, very doubtful.",
    "Concentrate and ask again... actually don't, the answer is still no.",
    "It is certain. Don't second-guess it like your last round of drinks.",
    "Outlook is looking worse than a Monday morning hangover.",
    "Bloody oath, yes.",
    "Reply hazy, try again after lockout.",
    "Better not tell you now. Mostly because it's bad news and I'm off the clock."
]

# Coin flip responses
COIN_HEADS_RESPONSES = [
    "Heads! 🪙 The footy gods have spoken.",
    "Heads! 🪙 Easiest decision since ordering a parma.",
    "HEADS! 🪙 Back yourself, champion."
]
COIN_TAILS_RESPONSES = [
    "Tails! 🪙 There you go.",
    "Tails! 🪙 Hope that settles the argument so we can get back to drinking.",
    "TAILS! 🪙 The coin has decided. No take-backs, just like a spilled pint."
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
