# 🦅 Perceval

An automated event tracker for Duke University. Monitors Instagram accounts, Duke event pages, and external competition sources for upcoming events related to startups, tech, business, and finance. Sends notifications via Telegram.

## What It Tracks

### Duke Sources (Instagram)
- **@daborninnovation** - Duke I&E
- **@dukeventuregroup** - Duke Venture Group
- **@duke_daml** - Duke Applied Machine Learning
- **@dukeforwardfund** - Duke Forward Fund
- **@dukeinnovation** - Duke Innovation & Entrepreneurship

### Duke Sources (Websites)
- Duke CIE Events
- Duke Entrepreneurship Events
- Fuqua Events
- Pratt Engineering Events

### External Competitions
- Devpost Hackathons
- MLH Hackathons
- Pitch Competitions (Eventbrite)
- Case Competitions
- Trading Competitions

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐     ┌──────────┐
│  Scrapers   │────>│  LLM Filter  │────>│  Database  │────>│ Telegram │
│ (IG, Web)   │     │ (relevance)  │     │  (dedup)   │     │  Bot     │
└─────────────┘     └──────────────┘     └───────────┘     └──────────┘
       │                    │
  Runs every            OpenAI or
  60 minutes            Anthropic
```

## Setup

### 1. Deploy to your AWS server

```bash
# Copy the project to your server (alongside merlin)
scp -r perceval ubuntu@your-server:/home/ubuntu/

# SSH in and run setup
ssh ubuntu@your-server
cd perceval
bash setup.sh
```

### 2. Create a Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 3. Get Your Chat ID

1. Message your new bot (say anything like "hello")
2. On the server:
```bash
cd perceval
source venv/bin/activate
python notifiers/telegram_notifier.py
```
3. Copy the chat ID it prints

### 4. Configure

Edit `.env` with your keys:
```bash
nano .env
```

### 5. Test

```bash
source venv/bin/activate
python main.py --once
```

### 6. Run as Service

```bash
sudo systemctl enable perceval
sudo systemctl start perceval
```

## Monitoring

```bash
# Check status
sudo systemctl status perceval

# View logs
journalctl -u perceval -f

# View log file
tail -f perceval.log
```

## Configuration

All settings are in `config/settings.py` and `.env`. Key options:

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM to use: `openai` or `anthropic` |
| `SCRAPE_INTERVAL_MINUTES` | `60` | How often to check sources |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model (cheap and fast) |

## Adding New Sources

### New Instagram Account
Add to `INSTAGRAM_ACCOUNTS` in `config/settings.py`.

### New Website
Add to `DUKE_WEBSITES` or `EXTERNAL_SOURCES` in `config/settings.py`.

## Cost

Running with `gpt-4o-mini`, expect ~$0.50-2.00/month in API costs depending on how many events are found. The keyword pre-filter keeps LLM calls minimal.
