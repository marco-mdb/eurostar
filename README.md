[README.md](https://github.com/user-attachments/files/28444583/README.md)
# Eurostar Snap Scanner

Monitors the Eurostar Snap page for ticket availability on your target dates and emails you the moment one appears. Runs every 5 minutes on GitHub's servers — no laptop needed.

---

## Setup

### 1. Create a GitHub account
Go to [github.com](https://github.com) and sign up for free if you don't have one.

### 2. Create a new repository
- Click the **+** icon top right → **New repository**
- Name it `eurostar-scanner`
- Set it to **Private** (keeps your workflow files private)
- Click **Create repository**

### 3. Upload the files
You need to upload two files into the repo, maintaining the folder structure:

```
eurostar-scanner/
├── scanner.py
└── .github/
    └── workflows/
        └── scan.yml
```

**Easiest way — GitHub web UI:**
- In your new repo, click **Add file → Upload files**
- Upload `scanner.py` directly
- For the workflow file, you need to create the folder path manually:
  - Click **Add file → Create new file**
  - In the filename box type: `.github/workflows/scan.yml`
  - Paste the contents of `scan.yml` and click **Commit new file**

### 4. Edit your target dates
Open `scanner.py` in the GitHub editor (click the file, then the pencil icon).
Find this section and set the dates you want to watch:

```python
WATCH_DATES = [
    "2026-06-18",
    "2026-06-19",
]
```

Commit the change.

### 5. Add your Gmail credentials as Secrets
Your email credentials are stored as encrypted GitHub Secrets —
they are never visible in your code or logs.

- Go to your repo → **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret** and add these three, one at a time:

| Secret name        | Value                              |
|--------------------|------------------------------------|
| `GMAIL_FROM`       | your Gmail address                 |
| `GMAIL_TO`         | address to send alerts to (can be same) |
| `GMAIL_APP_PASSWORD` | your 16-character Gmail app password |

**Getting a Gmail App Password:**
1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable 2-Step Verification if not already on
3. Search for **App Passwords**
4. Create one for Mail → copy the 16-character code (no spaces)

### 6. Enable Actions
- Go to the **Actions** tab in your repo
- If prompted, click **"I understand my workflows, enable them"**
- You should see the **Eurostar Snap Scanner** workflow listed

### 7. Test it manually
- Click the workflow → **Run workflow** → **Run workflow**
- Watch the run complete — green tick means it worked
- Check the logs to see which dates it checked and whether any were available

---

## How it works

Every 5 minutes GitHub spins up a small server, runs `scanner.py`,
and shuts it back down. The script:

1. Fetches the Snap search page for each of your target dates
2. Reads the availability JSON embedded in the page (no browser needed)
3. If a slot is found → sends you an email with the time, price, and a direct booking link
4. Exits — GitHub restarts it 5 minutes later

## Checking the logs

Go to **Actions** tab → click any run → click the **scan** job to see
the full output, including which dates were checked and whether emails were sent.

## Stopping the scanner

Go to **Actions** → **Eurostar Snap Scanner** → click the **...** menu → **Disable workflow**.

## Costs

Completely free. GitHub gives every account 2,000 free Actions
minutes per month. Each scan run takes ~15 seconds, so 5-minute
checks use roughly 4,320 minutes/month — this does exceed the free
limit on a standard account.

**Fix:** set the cron to every 10 minutes instead:
```yaml
- cron: '*/10 * * * *'
```
That brings usage to ~2,160 minutes/month, just within the free tier.
Or upgrade to GitHub Pro (£3.50/month) for 3,000 minutes.
