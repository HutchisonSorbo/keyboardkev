# 🏆 Keyboard Coaches: Ultimate Server Blueprint

Follow this step-by-step guide to set up the perfect Discord server architecture for your Keeper League. Keyboard Kev has been specifically programmed to interact with these exact channels.

---

## 🏗️ Step 1: Create Your Categories

In your Discord server, right-click the empty space on the left panel and select **Create Category**. Create these four categories exactly as named:

1. **The League Office** (For Commish announcements and rules)
2. **AFL Fantasy HQ** (For all the serious footy action)
3. **The Commentary Box** (For general chat and banter)
4. **Draft Night War Room** (Only used around draft time)

---

## 📝 Step 2: Create The Channels

Underneath each Category, click the `+` icon to add a Text Channel or Voice Channel. Name them *exactly* as shown below (Discord channels must be all lowercase with dashes).

### 📂 The League Office

*These channels should be set to "Read Only" for regular members so important info doesn't get buried in chat.*

* **`#welcome`**
  * **Purpose:** The entry point. Kev will drop a "G'day" message here when anyone joins the server.
* **`#rules-and-prizes`**
  * **Purpose:** Pin your league constitution, keeper rules, and prize pool here.
* **`#announcements`**
  * **Purpose:** Commish posts major league updates here.
* **`#mod-log`**
  * **Purpose:** *Make this channel Private (visible only to you).* Kev will privately log every auto-mod warning, deleted swear word, and kick here.

### 📂 AFL Fantasy HQ

*This is the engine room where Kev does his best work.*

* **`#afl-fantasy`**
  * **Purpose:** The main channel for lineup strategy, start/sit debates, and general AFL chatter.
  * **Kev's Role:** He drops his automatic Lockout Warnings here on Thursday evenings to yell at managers who haven't set their teams.
* **`#trade-floor`**
  * **Purpose:** Where coaches post proposed trades.
  * **Kev's Role:** Members can use `/tradeblock_add` here to list players they are shopping. Kev tracks everyone's trade block.
* **`#afl-news`**
  * **Purpose:** *Set to Read Only.*
  * **Kev's Role:** He automatically scrapes AFL.com.au every 2 hours and drops all general articles here.
* **`#afl-injuries`**
  * **Purpose:** *Set to Read Only.*
  * **Kev's Role:** Kev sifts through the news and specifically posts *only* articles relating to injuries, suspensions, or team selections here.
* **`#scores`**
  * **Purpose:** A dedicated channel so people don't clog up the main chat when looking up players.
  * **Kev's Role:** Members type `/scores`, `/ladder`, or `/stats [player]` here to instantly pull live AFL data.

### 📂 The Commentary Box

*For off-topic chat.*

* **`#general`**
  * **Purpose:** Standard weekend plans, banter, and non-footy chat.
  * **Kev's Role:** As members chat, they earn XP. When they level up, Kev announces their rank promotion here.
* **`#bot-spam`**
  * **Purpose:** Keeping the fun commands out of the serious footy channels.
  * **Kev's Role:** Members use `/askkev`, `/roast`, `/8ball`, `/roll`, and `/flipcoin` here.

### 📂 Draft Night War Room

*A dedicated space for the offseason climax.*

* **`#draft-banter`** (Text Channel)
  * **Purpose:** Talking absolute trash about reach picks.
  * **Kev's Role:** The Commish uses `/draftpick [Team] [Player]` here to announce live picks, prompting Kev to randomly roast the selection.
* **`#The War Room`** (Voice Channel)
  * **Purpose:** Where everyone jumps on the mics to chat while the draft clock ticks down.

---

## 🔒 Step 3: Set Up Permissions

Now that the channels exist, you need to make sure regular members can't mess them up. For the **Read Only** channels (`#rules-and-prizes`, `#announcements`, `#afl-news`, `#afl-injuries`):

1. Right-click the channel, click **Edit Channel**.
2. Go to **Permissions**.
3. Under `@everyone`, click the red `X` next to **Send Messages**.
4. (Make sure your "Commissioner" role has a green checkmark next to Send Messages so you can still post).

## 🧠 Step 4: Add the Brain (Gemini API)

You now have the `/askkev` command! Players can ask Kev literally anything about AFL history, grand finals, or players, and he will respond with accurate historical facts delivered entirely in his DT Talk persona.

**To turn this brain on:**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API Key**. It is 100% free.
3. Copy the key.
4. Go to your Keyboard Kev deployment on Render.com.
5. Click **Environment**.
6. Add a new variable:
   * Key: `GEMINI_API_KEY`
   * Value: (Paste the key you just copied).
7. Save changes. Kev will restart and his brain will be fully functional.

Enjoy the ultimate Discord Fantasy League setup!
