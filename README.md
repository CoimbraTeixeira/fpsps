# fpsps — Flight Points Promotion Scraper

Monitors European airline loyalty program websites for **miles/points purchase promotions** and sends an email alert when a new promotion is detected.

Runs automatically every 6 hours via GitHub Actions. No server required.

## Airlines monitored

| Airline | Program | URL |
|---|---|---|
| TAP Air Portugal | Miles&Go | flytap.com |
| Iberia | Iberia Plus / Avios | iberia.com |
| British Airways | Executive Club / Avios | britishairways.com |
| Air France / KLM | Flying Blue | klm.com |
| Turkish Airlines | Miles&Smiles | turkishairlines.com |
| Lufthansa | Miles & More | miles-and-more.com |
| Aer Lingus | AerClub / Avios | aerlingus.com |

## How it works

1. Each run fetches the buy-miles page for every airline using a headless Chromium browser (Playwright), with a plain HTTP fallback for sites that block headless browsers
2. Extracts text blocks matching promotion keywords (bonus miles, % off, limited time offers, etc.)
3. Compares detected promotions against the previous run stored in `state.json`
4. Sends an email via [Resend](https://resend.com) if new promotions are found
5. Commits the updated `state.json` back to the repo

## Setup

### 1. Fork or clone this repo

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `RESEND_API_KEY` | API key from your [Resend](https://resend.com) account |

### 3. Enable Actions write permissions

Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions** (needed to commit `state.json`).

### 4. Run it

The workflow runs automatically every 6 hours. To trigger it manually:

**Actions → Monitor Flight Points Promotions → Run workflow**

To verify email delivery before waiting for a real promotion, set `test_email` to `yes` when triggering manually.

## Local usage

```bash
pip install -r requirements.txt
playwright install chromium

# Run the monitor
RESEND_API_KEY=your_key python main.py

# Send a test email
RESEND_API_KEY=your_key python main.py --test-email
```

## State

`state.json` tracks the last known promotion hash per airline. It is committed automatically after each run. On first run, baselines are recorded without sending any alert.
