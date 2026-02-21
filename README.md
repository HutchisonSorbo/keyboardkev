# 🍻 Keyboard Kev for Keyboard Coaches

The ultimate unified Discord bot for the **Keyboard Coaches** AFL Fantasy league. Pull up a stool, grab a pint, and let Keyboard Kev run the show.

## 1. What Keyboard Kev Does

Keyboard Kev is 5 bots combined into one, featuring a massive suite of features:

- **🏉 AFL Fantasy**: Automatic Thursday lockout reminders (`LockoutLarry`), live scores (`ScoreboardStevo`), player stats (`StatmanStan`), and a snake draft manager (`DraftDayDave`).
- **💼 Keeper League**: Trade block management, future draft pick tracking, and automated league deadlines.
- **📰 News & Updates**: Automatic RSS feed fetching for AFL injury and team news (`TraumaTracker`).
- **🛡️ Moderation**: Auto-mod filters for banned words and spamming. Slash commands for warning, muting, kicking, banning, and purging messages.
- **⬆️ Levelling**: XP system where active users level up and earn roles. Top 10 leaderboard available.
- **📊 Polls**: Create rich embedded polls with up to 8 options and view results with `/endpoll`.
- **⚙️ Custom Commands**: Create automated replies to specific keywords (like `!rules`).
- **⏰ Reminders**: Set personal reminders like `/remindme 2h Fix my captain`.
- **🎭 Reaction Roles**: Let users self-assign roles by reacting to a message.
- **🎉 Fun**: Roast your league mates, flip coins, ask the magic 8-ball, and roll dice.

---

## 2. Discord Setup (Do This First)

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it **"Keyboard Kev"**.
3. Go to the **Bot** tab, click **Add Bot**.
4. Under **Privileged Gateway Intents** enable: **Presence Intent**, **Server Members Intent**, and **Message Content Intent**. All three are required.
5. Copy the bot token and paste it into `.env` as `DISCORD_TOKEN=your_token_here`.
6. Go to **OAuth2 > URL Generator**.
7. Select scopes: `bot` and `applications.commands`.
8. Select permissions: **Administrator** (simplest for a private league server).
9. Copy the generated invite URL and open it in your browser to add Keyboard Kev to your server.

---

## 3. Local Setup

1. Install **Python 3.11+** from [python.org](https://www.python.org/).
2. Download or clone this project folder.
3. Open a terminal in the project folder.
4. Create a virtual environment:
   - `python -m venv venv`
5. Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
6. Install dependencies: `pip install -r requirements.txt`
7. Copy `.env.example` to `.env` and paste your bot token.
8. Edit `config.py` to set your channel names and preferences.
9. Run the bot: `python main.py`

---

## 4. Free 24/7 Hosting on Render.com

1. Push your project folder to a GitHub repository (private is fine).
2. Go to [render.com](https://render.com) and create a free account.
3. Click **New** > **Background Worker** (Background Workers stay active 24/7 on the free tier, unlike Web Services).
4. Connect your GitHub repository.
5. Set the build command: `pip install -r requirements.txt`
6. Set the start command: `python main.py`
7. Go to **Environment** and add one variable: `DISCORD_TOKEN` = your token value. Do not upload the `.env` file!
8. Click **Create Background Worker**. Render will build and deploy. Keyboard Kev will come online within 2-3 minutes.
9. To redeploy after any code or config change, just push to GitHub. Render redeploys automatically.

---

## 5. How to Configure Keyboard Kev

All settings live in `config.py`. Open it, change the value, save, and restart (or push to GitHub if on Render).

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `SERVER_NAME` | `"Keyboard Coaches"` | Name of the server |
| `PREFIX` | `"!"` | Fallback prefix for legacy commands |
| `AFL_CHANNEL` | `"afl-fantasy"` | Where lockout reminders are sent |
| `NEWS_CHANNEL` | `"injuries-and-news"` | Where RSS injury articles are posted |
| `WELCOME_CHANNEL` | `"welcome"` | Where new member welcomes are sent |
| `MOD_LOG_CHANNEL` | `"mod-log"` | Where moderation actions are logged |
| `GENERAL_CHANNEL` | `"general"` | Level-up announcements and fun commands |
| `PING_EVERYONE` | `True` | Ping @everyone for lockout reminders |
| `LEVELLING_ENABLED` | `True` | Turn the XP system on or off |
| `TOTAL_TEAMS` | `8` | Number of teams for Snake Draft |

---

## 6. Setting Up Your Discord Server Channels

Keyboard Kev expects specific channel names exactly as defined in `config.py`. Create these channels (or rename existing ones):

- `#afl-fantasy` - Lineup reminders and draft chatter
- `#injuries-and-news` - Automatic injury feed (read-only recommended)
- `#scores` - Score lookups
- `#welcome` - New member welcome messages
- `#mod-log` - Moderation action log (admin only)
- `#general` - Regular chat, Level-up announcements and fun commands

---

## 7. First Steps After Deployment

- [ ] Verify Keyboard Kev appears online in your server member list.
- [ ] Run `/help` to confirm all commands are registered.
- [ ] Set team names using `/setteam 1 [name]` through `/setteam 8 [name]`.
- [ ] Test `/scores` to confirm the Squiggle API is working.
- [ ] Set up your league's keeper deadlines with `/setdeadline "List Lodgement" "2027-02-15 18:00"`.
- [ ] Throw your bust players on the market using `/tradeblock_add`.
- [ ] Check `#injuries-and-news` after 2 hours to confirm TraumaTracker is posting.
- [ ] Send a test message to confirm XP is being awarded (check with `/rank`).
- [ ] Set up at least one reaction role with `/reactionrole` for game day pings.
- [ ] Update `config.ROASTS` with league-specific chirps about your mates.
