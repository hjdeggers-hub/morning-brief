# Hunter's Morning News Brief

A personalized daily newspaper delivered to your inbox at 7 AM ET.  
Built with Python, Claude API, SendGrid, and GitHub Actions.

---

## What It Does

- **MonâSat**: Concise daily brief with 3â5 stories per section, ideology-labeled + color-coded
- **Sunday**: Long-read edition with deeper summaries + "ð­ Deeper Read" callouts
- **Ideology labels**: ð´ Left Â· ðµ Center Â· ð¢ Right â color-coded badges on every story
- **Sections covered**:
  - ð Global Politics & Geopolitics
  - ðºð¸ US Domestic Politics
  - ð° Economics & Finance
  - ð¾ Food Systems & Agriculture
  - ð Africa & African Geopolitics
  - ð½ NYC / Westchester Local
  - ð° Other Notable Stories

---

## Source List

| Source | Ideology |
|---|---|
| Jacobin | ð´ Left |
| The Lever | ð´ Left |
| The Baffler | ð´ Left |
| Truthout | ð´ Left |
| In These Times | ð´ Left |
| Dissent Magazine | ð´ Left |
| Civil Eats | ð´ Left |
| New York Times | ðµ Center |
| Reuters | ðµ Center |
| Associated Press | ðµ Center |
| The Economist | ðµ Center |
| Al Jazeera | ðµ Center |
| AllAfrica | ðµ Center |
| Quartz Africa | ðµ Center |
| The East African | ðµ Center |
| The Africa Report | ðµ Center |
| AgriPulse | ðµ Center |
| Gothamist | ðµ Center |
| Wall Street Journal | ð¢ Right |
| The Dispatch | ð¢ Right |
| National Review | ð¢ Right |

---

## Setup (One-Time, ~20 minutes)

### 1. Clone This Repo

```bash
git clone https://github.com/YOUR_USERNAME/morning-brief.git
cd morning-brief
```

### 2. Get Your API Keys

| Service | Where to get it | Cost |
|---|---|---|
| **Anthropic (Claude)** | [console.anthropic.com](https://console.anthropic.com) | ~$0.05â0.15/day |
| **SendGrid** | [sendgrid.com](https://sendgrid.com) | Free (100 emails/day) |

**SendGrid setup:**
1. Create a free account
2. Go to **Settings â API Keys â Create API Key** (Full Access)
3. Go to **Settings â Sender Authentication** and verify your sender email address

### 3. Add GitHub Secrets

In your GitHub repo go to: **Settings â Secrets and variables â Actions â New repository secret**

Add all four of these:

| Secret Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `SENDGRID_API_KEY` | Your SendGrid API key |
| `RECIPIENT_EMAIL` | Email address to receive the brief |
| `SENDER_EMAIL` | Verified sender email in SendGrid |

### 4. Push to GitHub & Enable Actions

```bash
git add .
git commit -m "Initial news brief setup"
git push origin main
```

Go to the **Actions** tab in your repo and confirm workflows are enabled.

### 5. Test It Manually

Go to **Actions â Hunter's Daily News Brief â Run workflow** to trigger an immediate test send.

---

## Customization

### Add or Remove Sources

Edit the `FEEDS` list in `news_brief.py`:

```python
("https://example.com/feed.rss", "Source Name", "Left"),  # Left | Center | Right
```

To find an RSS feed for any site, try appending `/feed`, `/rss`, or `/feed.xml` to the homepage URL,
or search "[site name] RSS feed".

### Add a New Section

Edit the `SECTIONS` list. Each entry is a tuple of (name, keyword list):

```python
("ð¬ Tech & AI", ["artificial intelligence", "ai ", "openai", "silicon valley", "tech industry"]),
```

Stories are auto-classified based on keyword matches in the title + summary.

### Change Delivery Time

Edit `.github/workflows/news_brief.yml`. The cron runs in UTC.

```yaml
- cron: '0 12 * * *'   # 12:00 UTC = 7:00 AM ET (EST) / 8:00 AM ET (EDT)
```

Use [crontab.guru](https://crontab.guru) to find the right UTC time for your timezone.

---

## Estimated Cost

| Item | Cost |
|---|---|
| Claude API (daily brief) | ~$0.05â0.10/day |
| Claude API (Sunday long-read) | ~$0.10â0.20/week |
| SendGrid | Free |
| GitHub Actions | Free |
| **Monthly total** | **~$2â5/month** |

---

## File Structure

```
morning-brief/
âââ news_brief.py               # Main script
âââ requirements.txt            # Python dependencies
âââ README.md                   # This file
âââ .github/
    âââ workflows/
        -news_brief.yml      # GitHub Actions schedule
```

---

## Troubleshooting

**Email not arriving?**
- Check your SendGrid Activity Feed for delivery status
- Verify your sender email is authenticated in SendGrid
- Check your spam folder

**Script errors in GitHub Actions?**
- Go to Actions tab â click the failed run â expand the logs
- Most common issues: missing secrets, or an RSS feed URL that has changed

**A feed returning no results?**
- RSS URLs change occasionally. Google "[source name] RSS feed" to find the current URL
- You can also test feeds at [validator.w3.org/feed](https://validator.w3.org/feed/)
