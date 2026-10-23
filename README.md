# hermes

A bot that finds startup, tech, business, and finance events at Duke and sends them to me on Telegram.

Every hour it scrapes a set of Duke Instagram accounts, Duke event pages, and hackathon/competition sites. An LLM filters out the irrelevant ones, the rest get deduplicated in a small database, and new events get sent as Telegram messages.

```
scrapers -> LLM filter -> database (dedup) -> Telegram
```

## Running it

Copy `.env.example` to `.env` and add your API keys and Telegram bot token, then:

```bash
bash setup.sh
source venv/bin/activate
python main.py --once
```

It runs as a systemd service on a server (`perceval.service`). Sources are configured in `config/settings.py`.
