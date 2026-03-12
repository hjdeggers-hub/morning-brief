#!/usr/bin/env python3
"""
Hunter's Daily News Brief
Fetches RSS feeds, summarizes with Claude API, sends via SendGrid.
"""

import os
import json
import feedparser
import anthropic
import sendgrid
from sendgrid.helpers.mail import Mail
from datetime import datetime, date
import pytz

# âââââââââââââââââââââââââââââââââââââââââââââ
# CONFIGURATION
# âââââââââââââââââââââââââââââââââââââââââââââ

RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]       # your email
SENDER_EMAIL    = os.environ["SENDER_EMAIL"]          # verified SendGrid sender
ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
SENDGRID_KEY    = os.environ["SENDGRID_API_KEY"]

IS_SUNDAY = date.today().weekday() == 6

# âââââââââââââââââââââââââââââââââââââââââââââ
# RSS FEED SOURCES  (url, display name, ideology)
# âââââââââââââââââââââââââââââââââââââââââââââ

FEEDS = [
    # ââ Left / Progressive âââââââââââââââââââââââââââââââââââââââââââââ
    ("https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml",
        "New York Times", "Center"),
    ("https://jacobin.com/feed/",
        "Jacobin", "Left"),
    ("https://thelever.news/feed/",
        "The Lever", "Left"),
    ("https://thebaffler.com/feed",
        "The Baffler", "Left"),
    ("https://truthout.org/feed/",
        "Truthout", "Left"),
    ("https://inthesetimes.com/feed",
        "In These Times", "Left"),
    ("https://www.dissentmagazine.org/feed",
        "Dissent Magazine", "Left"),

    # ââ Center / Wire âââââââââââââââââââââââââââââââââââââââââââââââââââ
    ("https://feeds.reuters.com/reuters/topNews",
        "Reuters", "Center"),
    ("https://rsshub.app/apnews/topics/apf-topnews",
        "Associated Press", "Center"),
    ("https://www.economist.com/latest/rss.xml",
        "The Economist", "Center"),

    # ââ Right / Conservative ââââââââââââââââââââââââââââââââââââââââââââ
    ("https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "Wall Street Journal", "Right"),
    ("https://thedispatch.com/feed/",
        "The Dispatch", "Right"),
    ("https://www.nationalreview.com/feed/",
        "National Review", "Right"),

    # ââ Al Jazeera ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    ("https://www.aljazeera.com/xml/rss/all.xml",
        "Al Jazeera", "Center"),

    # ââ Africa & Emerging Markets âââââââââââââââââââââââââââââââââââââââ
    ("https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
        "AllAfrica", "Center"),
    ("https://qz.com/africa/feed/",
        "Quartz Africa", "Center"),
    ("https://www.theeastafrican.co.ke/tea/rss",
        "The East African", "Center"),
    ("https://www.theafricareport.com/feed/",
        "The Africa Report", "Center"),

    # ââ Food Systems & Agriculture ââââââââââââââââââââââââââââââââââââââ
    ("https://civileats.com/feed/",
        "Civil Eats", "Left"),
    ("https://www.agri-pulse.com/rss/news",
        "AgriPulse", "Center"),

    # ââ NYC / Local âââââââââââââââââââââââââââââââââââââââââââââââââââââ
    ("https://gothamist.com/feed",
        "Gothamist", "Center"),
]

# âââââââââââââââââââââââââââââââââââââââââââââ
# SECTION DEFINITIONS  (name, emoji, keywords)
# âââââââââââââââââââââââââââââââââââââââââââââ

SECTIONS = [
    ("ð Global Politics & Geopolitics",
        ["geopolit", "foreign", "international", "diplomacy", "war", "conflict", "treaty", "nato", "un ", "united nations", "sanction"]),
    ("ðºð¸ US Domestic Politics",
        ["congress", "senate", "white house", "democrat", "republican", "trump", "biden", "harris", "legislation", "supreme court", "election", "doge"]),
    ("ð° Economics & Finance",
        ["economy", "gdp", "inflation", "federal reserve", "fed ", "market", "stock", "trade", "tariff", "fiscal", "monetary", "debt", "imf", "world bank"]),
    ("ð¾ Food Systems & Agriculture",
        ["food", "farm", "agricultur", "crop", "hunger", "famine", "supply chain", "agri", "soil", "seed", "harvest", "csa", "agroecolog"]),
    ("ð Africa & African Geopolitics",
        ["africa", "african", "nigeria", "kenya", "ethiopia", "ghana", "sahel", "sub-saharan", "east africa", "west africa", "southern africa", "one acre fund", "smallholder"]),
    ("ð½ NYC / Westchester Local",
        ["new york", "nyc", "brooklyn", "manhattan", "bronx", "queens", "westchester", "pelham", "gothamist", "mta", "albany"]),
]

FALLBACK_SECTION = "ð° Other Notable Stories"

# âââââââââââââââââââââââââââââââââââââââââââââ
# FETCH FEEDS
# âââââââââââââââââââââââââââââââââââââââââââââ

def fetch_articles(max_per_feed=8 if IS_SUNDAY else 5):
    articles = []
    for url, source, ideology in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title   = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                link    = entry.get("link", "")
                if title:
                    articles.append({
                        "title":    title,
                        "summary":  summary[:400],
                        "link":     link,
                        "source":   source,
                        "ideology": ideology,
                    })
        except Exception as e:
            print(f"Feed error [{source}]: {e}")
    return articles

# âââââââââââââââââââââââââââââââââââââââââââââ
# CLASSIFY ARTICLES INTO SECTIONS
# âââââââââââââââââââââââââââââââââââââââââââââ

def classify_article(article):
    text = (article["title"] + " " + article["summary"] + " " + article["source"]).lower()
    for section_name, keywords in SECTIONS:
        if any(kw in text for kw in keywords):
            return section_name
    return FALLBACK_SECTION

def group_by_section(articles):
    grouped = {s[0]: [] for s in SECTIONS}
    grouped[FALLBACK_SECTION] = []
    for a in articles:
        section = classify_article(a)
        grouped[section].append(a)
    return grouped

# âââââââââââââââââââââââââââââââââââââââââââââ
# CLAUDE SUMMARIZATION
# âââââââââââââââââââââââââââââââââââââââââââââ

def summarize_with_claude(grouped):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    # Build input payload for Claude
    payload = []
    for section, arts in grouped.items():
        if not arts:
            continue
        payload.append({"section": section, "articles": [
            {"title": a["title"], "summary": a["summary"],
             "source": a["source"], "ideology": a["ideology"], "link": a["link"]}
            for a in arts[:10]
        ]})

    edition = "Sunday Long-Read Edition" if IS_SUNDAY else "Daily Brief"
    depth   = (
        "Write 3-5 sentences per story. Include important context, "
        "stakes, and any ideological framing worth noting."
        if IS_SUNDAY else
        "Write 2-3 crisp sentences per story. Focus on the key facts and why it matters."
    )

    prompt = f"""You are the editor of Hunter's Morning News Brief â a personalized daily newspaper.

Hunter's background: works in grants finance at One Acre Fund (agricultural development in Africa), 
deeply interested in degrowth economics, food systems, anti-capitalist theory, African development, 
solidarity economy, and local NYC/Westchester life. Married, lives in Pelham NY.

Today is {datetime.now(pytz.timezone('America/New_York')).strftime('%A, %B %d, %Y')}.
Edition: {edition}

Here are the news articles grouped by section (JSON):
{json.dumps(payload, indent=2)}

Your task:
1. For each section that has articles, write a tight editorial digest.
2. Pick the 3-5 most newsworthy/relevant stories per section (more for Sunday).
3. {depth}
4. Each story entry must include:
   - Headline (you may rewrite for clarity)
   - [Left] / [Center] / [Right] ideology label based on the source
   - 2-3 sentence summary (more on Sundays)
   - Source name and link
5. Add a brief 2-sentence "Editor's Note" at the top of each section flagging the big theme of the day.
6. For Sunday only: add a "ð­ Deeper Read" callout for 1 story per section worth reading in full.
7. Do NOT include sections with zero stories.
8. Return ONLY valid JSON in this exact structure:
{{
  "date": "...",
  "edition": "...",
  "sections": [
    {{
      "name": "section name with emoji",
      "editors_note": "...",
      "stories": [
        {{
          "headline": "...",
          "ideology": "Left|Center|Right",
          "summary": "...",
          "source": "...",
          "link": "...",
          "deeper_read": true/false
        }}
      ]
    }}
  ]
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# âââââââââââââââââââââââââââââââââââââââââââââ
# HTML EMAIL BUILDER
# âââââââââââââââââââââââââââââââââââââââââââââ

IDEOLOGY_COLORS = {
    "Left":   "#d73027",
    "Center": "#4575b4",
    "Right":  "#1a9850",
}

def ideology_badge(label):
    color = IDEOLOGY_COLORS.get(label, "#888")
    return (f'<span style="display:inline-block;padding:1px 7px;border-radius:10px;'
            f'background:{color};color:#fff;font-size:11px;font-weight:600;'
            f'letter-spacing:0.5px;margin-right:6px;">{label}</span>')

def build_html(brief):
    today     = brief["date"]
    edition   = brief["edition"]
    is_sunday = "Sunday" in edition

    header_color = "#1a1a2e" if not is_sunday else "#2c003e"
    accent_color = "#e8a020" if not is_sunday else "#c084fc"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hunter's News Brief â {today}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f0;font-family:'Georgia',serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f0;">
<tr><td align="center" style="padding:24px 16px;">
<table width="640" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <!-- MASTHEAD -->
  <tr><td style="background:{header_color};padding:32px 40px;text-align:center;">
    <div style="color:{accent_color};font-size:11px;letter-spacing:3px;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:8px;">
      {today}
    </div>
    <div style="color:#fff;font-size:32px;font-weight:700;letter-spacing:-0.5px;">
      Hunter's Morning Brief
    </div>
    <div style="color:#aaa;font-size:13px;margin-top:6px;font-family:Arial,sans-serif;">
      {edition}
    </div>
  </td></tr>

  <!-- DIVIDER -->
  <tr><td style="background:{accent_color};height:4px;"></td></tr>

  <!-- BODY -->
  <tr><td style="padding:32px 40px;">
"""

    for section in brief.get("sections", []):
        sec_name     = section["name"]
        editors_note = section.get("editors_note", "")
        stories      = section.get("stories", [])

        html += f"""
    <!-- SECTION: {sec_name} -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:36px;">
      <tr><td style="border-bottom:2px solid {header_color};padding-bottom:6px;margin-bottom:12px;">
        <span style="font-size:18px;font-weight:700;color:{header_color};font-family:Arial,sans-serif;">
          {sec_name}
        </span>
      </td></tr>
"""
        if editors_note:
            html += f"""
      <tr><td style="background:#f8f8f4;border-left:3px solid {accent_color};padding:10px 14px;margin:10px 0;font-size:13px;color:#555;font-style:italic;font-family:Arial,sans-serif;">
        <strong>Editor's Note:</strong> {editors_note}
      </td></tr>
      <tr><td style="height:12px;"></td></tr>
"""

        for story in stories:
            headline    = story.get("headline", "")
            ideology    = story.get("ideology", "Center")
            summary     = story.get("summary", "")
            source      = story.get("source", "")
            link        = story.get("link", "#")
            deeper_read = story.get("deeper_read", False)

            deeper = ""
            if deeper_read:
                deeper = f"""
        <div style="margin-top:6px;background:#f0e6ff;border-radius:3px;padding:5px 10px;display:inline-block;font-size:11px;color:#6b21a8;font-family:Arial,sans-serif;font-weight:600;">
          ð­ Deeper Read â Worth reading in full
        </div>"""

            html += f"""
      <tr><td style="padding:14px 0;border-bottom:1px solid #eee;">
        <div style="margin-bottom:4px;">
          {ideology_badge(ideology)}
          <a href="{link}" style="font-size:15px;font-weight:700;color:{header_color};text-decoration:none;line-height:1.4;">
            {headline}
          </a>
        </div>
        <div style="font-size:13px;color:#333;line-height:1.6;font-family:Arial,sans-serif;margin-top:4px;">
          {summary}
        </div>
        <div style="margin-top:6px;font-size:11px;color:#888;font-family:Arial,sans-serif;">
          via <strong>{source}</strong>
        </div>
        {deeper}
      </td></tr>
"""

        html += "    </table>\n"

    # FOOTER
    html += f"""
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:{header_color};padding:20px 40px;text-align:center;">
    <div style="color:#888;font-size:11px;font-family:Arial,sans-serif;line-height:1.8;">
      Hunter's Morning Brief Â· Delivered daily at 7 AM ET<br/>
      Built with Claude + SendGrid + GitHub Actions
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return html

# âââââââââââââââââââââââââââââââââââââââââââââ
# SEND EMAIL
# âââââââââââââââââââââââââââââââââââââââââââââ

def send_email(html_content, subject):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_KEY)
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=subject,
        html_content=html_content,
    )
    response = sg.send(message)
    print(f"Email sent: {response.status_code}")

# âââââââââââââââââââââââââââââââââââââââââââââ
# MAIN
# âââââââââââââââââââââââââââââââââââââââââââââ

def main():
    print("Fetching articles...")
    articles = fetch_articles()
    print(f"  â {len(articles)} articles fetched")

    print("Grouping by section...")
    grouped = group_by_section(articles)

    print("Summarizing with Claude...")
    brief = summarize_with_claude(grouped)

    print("Building HTML...")
    html = build_html(brief)

    edition_label = "âï¸ Sunday Long-Read" if IS_SUNDAY else "ð° Daily Brief"
    today_str     = datetime.now(pytz.timezone("America/New_York")).strftime("%b %d, %Y")
    subject       = f"{edition_label} | {today_str}"

    print("Sending email...")
    send_email(html, subject)
    print("Done.")

if __name__ == "__main__":
    main()
