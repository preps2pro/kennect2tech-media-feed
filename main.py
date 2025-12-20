from flask import Flask, request, jsonify, send_from_directory
from bs4 import BeautifulSoup
import requests
import datetime
from datetime import datetime as dt
import os
import json
import hashlib
import uuid

app = Flask(__name__, static_folder='static')

FEEDS_DIR = "feeds"
PUBLISH_DIR = "publish_queue"
PORTFOLIO_DIR = "portfolio"
SETTINGS_FILE = "settings.json"
os.makedirs(FEEDS_DIR, exist_ok=True)
os.makedirs(PUBLISH_DIR, exist_ok=True)
os.makedirs(PORTFOLIO_DIR, exist_ok=True)

BING_API_KEY = os.environ.get("BING_SEARCH_API_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
ZAPIER_WEBHOOK_URL = os.environ.get("ZAPIER_WEBHOOK_URL")
BUFFER_ACCESS_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")
ADMIN_KEY = os.environ.get("ADMIN_KEY")

FOUNDER_PLAYBOOKS = [
    {
        "id": "funding-round",
        "title": "Announcing a Funding Round",
        "category": "Funding",
        "sections": [
            {"title": "Headline", "content": "[Company] Raises $[X]M [Round] to [Mission Statement]"},
            {"title": "Opening", "content": "We're thrilled to announce that [Company] has closed a $[X]M [Series A/Seed/etc.] round led by [Lead Investor], with participation from [Other Investors]."},
            {"title": "What This Means", "content": "This funding will accelerate our mission to [core mission]. Specifically, we'll be investing in [3 key areas: product, team, market expansion]."},
            {"title": "Traction & Validation", "content": "Since launching [timeframe], we've [key metrics: users, revenue, partnerships]. This round validates our approach to [problem space]."},
            {"title": "Quote from Founder", "content": "\"[Personal reflection on journey and gratitude to team, customers, investors]\" — [Founder Name], CEO"},
            {"title": "Quote from Investor", "content": "\"[Why they invested - team, market, traction]\" — [Investor Name], [Firm]"},
            {"title": "Call to Action", "content": "We're hiring! If you're passionate about [mission], check out our open roles at [careers page]."}
        ]
    },
    {
        "id": "product-launch",
        "title": "Launching a Product Feature",
        "category": "Launch",
        "sections": [
            {"title": "Headline", "content": "Introducing [Feature Name]: [One-line value prop]"},
            {"title": "The Problem", "content": "Our customers told us [pain point]. Until now, [workaround or gap]."},
            {"title": "The Solution", "content": "[Feature] lets you [core benefit] with [key differentiator]."},
            {"title": "How It Works", "content": "1. [Step 1]\n2. [Step 2]\n3. [Step 3]"},
            {"title": "Early Results", "content": "Beta users are seeing [metric improvement]. [Customer quote if available]."},
            {"title": "Availability", "content": "[Feature] is available today for [plan tier]. Existing customers can access it in [location]."},
            {"title": "What's Next", "content": "This is just the beginning. Coming soon: [teaser of roadmap]."}
        ]
    },
    {
        "id": "partnership",
        "title": "Sharing a Partnership",
        "category": "Partnership",
        "sections": [
            {"title": "Headline", "content": "[Company] Partners with [Partner] to [Outcome]"},
            {"title": "Why This Matters", "content": "[Partner] is a leader in [their space]. Together, we're [joint value prop]."},
            {"title": "What Customers Get", "content": "This partnership brings [specific benefit 1], [benefit 2], and [benefit 3] to our customers."},
            {"title": "Quote from Your Team", "content": "\"[Strategic importance of partnership]\" — [Your Name], [Title]"},
            {"title": "Quote from Partner", "content": "\"[Why they chose to partner]\" — [Partner Name], [Title]"},
            {"title": "Next Steps", "content": "Starting [date], customers can [access/use integration]. Learn more at [link]."}
        ]
    }
]

LAUNCH_TEMPLATES = {
    "linkedin": {
        "funding": {
            "title": "Funding Announcement - LinkedIn",
            "template": "🚀 Big news: We just raised $[X]M!\n\n[Lead Investor] led the round, joined by [investors].\n\nWhat we're building: [one-line mission]\n\nWhat's next:\n→ [Priority 1]\n→ [Priority 2]\n→ [Priority 3]\n\nWe're hiring! DM me or check out [careers link]\n\nGrateful to our team, customers, and investors who believe in this mission.\n\n#Startup #Funding #[Industry]"
        },
        "launch": {
            "title": "Product Launch - LinkedIn",
            "template": "Today we're launching [Feature] 🎉\n\nThe problem: [Pain point in 1 sentence]\n\nOur solution: [Feature benefit in 1 sentence]\n\nEarly results from beta:\n→ [Metric 1]\n→ [Metric 2]\n\nTry it today: [Link]\n\nWould love your feedback in the comments 👇\n\n#ProductLaunch #Innovation #[Industry]"
        },
        "partnership": {
            "title": "Partnership Announcement - LinkedIn",
            "template": "Excited to announce: [Company] + [Partner] 🤝\n\nWhat this means for our customers:\n→ [Benefit 1]\n→ [Benefit 2]\n→ [Benefit 3]\n\n[Partner] is a leader in [their space]. Together, we're making [outcome] a reality.\n\nLearn more: [Link]\n\n#Partnership #Collaboration #[Industry]"
        }
    },
    "email": {
        "funding": {
            "title": "Funding Announcement - Email",
            "subject": "[Company] Raises $[X]M to [Mission]",
            "template": "Hi [Name],\n\nI'm excited to share some news: [Company] has just closed a $[X]M [round type] led by [Lead Investor].\n\nThis investment will help us:\n• [Priority 1]\n• [Priority 2]\n• [Priority 3]\n\nWe couldn't have reached this milestone without customers like you. Thank you for believing in what we're building.\n\nIf you have any questions, just reply to this email.\n\nOnward,\n[Founder Name]"
        },
        "launch": {
            "title": "Product Launch - Email",
            "subject": "New: [Feature Name] is here",
            "template": "Hi [Name],\n\nYou asked, we listened. Today we're launching [Feature Name].\n\nWhat's new:\n• [Capability 1]\n• [Capability 2]\n• [Capability 3]\n\nHow to try it: [Instructions]\n\nWe'd love your feedback. Just reply to this email.\n\nBest,\n[Team]"
        },
        "partnership": {
            "title": "Partnership Announcement - Email",
            "subject": "Exciting news: [Company] + [Partner]",
            "template": "Hi [Name],\n\nWe're thrilled to announce a new partnership with [Partner].\n\nWhat this means for you:\n• [Benefit 1]\n• [Benefit 2]\n• [Benefit 3]\n\nThis integration is available now. [Instructions to access]\n\nQuestions? Just reply to this email.\n\nBest,\n[Team]"
        }
    }
}

INVESTOR_UPDATE_TEMPLATES = {
    "monthly": {
        "title": "Monthly Investor Update",
        "sections": [
            {"title": "TL;DR", "content": "• [Key highlight 1]\n• [Key highlight 2]\n• [Key metric or milestone]"},
            {"title": "Metrics", "content": "MRR: $[X] ([+/-]% MoM)\nUsers: [X] ([+/-]% MoM)\nBurn: $[X]/month\nRunway: [X] months"},
            {"title": "Wins", "content": "• [Win 1]\n• [Win 2]\n• [Win 3]"},
            {"title": "Challenges", "content": "• [Challenge 1]: [What we're doing about it]\n• [Challenge 2]: [What we're doing about it]"},
            {"title": "Asks", "content": "• [Intro to...]\n• [Feedback on...]\n• [Help with...]"},
            {"title": "Team", "content": "[New hires, departures, or org changes]"},
            {"title": "What's Next", "content": "Focus for next month:\n• [Priority 1]\n• [Priority 2]\n• [Priority 3]"}
        ]
    },
    "quarterly": {
        "title": "Quarterly LP Update",
        "sections": [
            {"title": "Executive Summary", "content": "[2-3 sentence overview of quarter performance and outlook]"},
            {"title": "Financial Highlights", "content": "Revenue: $[X] ([+/-]% QoQ)\nGross Margin: [X]%\nNet Burn: $[X]\nCash Position: $[X]\nRunway: [X] months"},
            {"title": "Key Accomplishments", "content": "• [Major milestone 1]\n• [Major milestone 2]\n• [Major milestone 3]"},
            {"title": "Product & Engineering", "content": "• [Shipped feature 1]\n• [Shipped feature 2]\n• [Technical improvement]"},
            {"title": "Go-to-Market", "content": "• New customers: [X]\n• Pipeline: $[X]\n• Key wins: [Notable logos]"},
            {"title": "Team & Culture", "content": "Headcount: [X] ([+/-] from last quarter)\n• New hires: [Names/roles]\n• Key departures: [If any]"},
            {"title": "Strategic Priorities (Next Quarter)", "content": "1. [Priority 1]\n2. [Priority 2]\n3. [Priority 3]"},
            {"title": "Asks for Investors", "content": "• [Specific ask 1]\n• [Specific ask 2]"}
        ]
    }
}

THOUGHT_LEADERSHIP_PROMPTS = [
    {"id": "1", "category": "Market Insight", "prompt": "What's one thing most people get wrong about [your industry]?", "hook": "Contrarian take: "},
    {"id": "2", "category": "Lessons Learned", "prompt": "What's the most expensive mistake you've made as a founder?", "hook": "A $[X]K lesson: "},
    {"id": "3", "category": "Hiring", "prompt": "What's your #1 interview question for [role] candidates?", "hook": "The question that reveals everything: "},
    {"id": "4", "category": "Product", "prompt": "What feature did customers ask for that you refused to build?", "hook": "Why we said no to our biggest customer request: "},
    {"id": "5", "category": "Fundraising", "prompt": "What do you wish you knew before your first fundraise?", "hook": "Advice I'd give myself before raising: "},
    {"id": "6", "category": "Culture", "prompt": "What's one company value you'd never compromise on?", "hook": "The non-negotiable: "},
    {"id": "7", "category": "Growth", "prompt": "What's your most underrated growth channel?", "hook": "The channel no one talks about: "},
    {"id": "8", "category": "Leadership", "prompt": "What's the hardest conversation you've had as a leader?", "hook": "The conversation that changed how I lead: "},
    {"id": "9", "category": "Strategy", "prompt": "What would you do differently if starting over today?", "hook": "If I started [Company] today: "},
    {"id": "10", "category": "Trends", "prompt": "What trend in [industry] are you most excited about?", "hook": "The trend that will define the next 5 years: "}
]

SPORTS_TECH_TEMPLATES = [
    {"id": "funding-sports", "title": "Sports-Tech Funding Announcement", "category": "Funding", "template": "🏆 [Company] raises $[X]M to transform [sports tech vertical]\n\nWe're building the future of [athlete performance/fan engagement/sports analytics].\n\nLed by [Investor], with participation from [sports-focused VCs/athletes].\n\nWhat's next:\n→ [League/team partnerships]\n→ [Product expansion]\n→ [Market growth]\n\n#SportsTech #AthletePerformance #VC"},
    {"id": "league-partnership", "title": "League/Team Partnership", "category": "Partnership", "template": "Proud to announce: [Company] partners with [League/Team] 🏈\n\nWe're bringing [technology/capability] to [use case].\n\nWhat this means:\n→ [Benefit for athletes]\n→ [Benefit for teams]\n→ [Benefit for fans]\n\nThis is what the future of sports looks like.\n\n#SportsTech #Innovation #[League]"},
    {"id": "athlete-adoption", "title": "Athlete Adoption Milestone", "category": "Milestone", "template": "[X]+ athletes now use [Company] 💪\n\nFrom [sport 1] to [sport 2], elite performers are choosing [Company] for:\n→ [Benefit 1]\n→ [Benefit 2]\n→ [Benefit 3]\n\n\"[Athlete quote]\" — [Athlete Name], [Team/Sport]\n\n#AthletePerformance #SportsTech"},
    {"id": "innovation-lab", "title": "Innovation Lab Update", "category": "Innovation", "template": "Inside [Team/League] Innovation Lab 🔬\n\nWe're working with [partner] to explore:\n→ [Technology 1]\n→ [Technology 2]\n→ [Technology 3]\n\nThe goal: [outcome for athletes/fans/teams]\n\nStay tuned for results.\n\n#SportsInnovation #R&D #SportsTech"},
    {"id": "performance-research", "title": "Performance/Health Research", "category": "Research", "template": "New research: [Finding headline] 📊\n\nOur latest study with [partner/institution] reveals:\n→ [Key finding 1]\n→ [Key finding 2]\n→ [Implication for athletes]\n\nFull report: [Link]\n\n#SportsScience #AthleteHealth #Research"}
]

def generate_owned_media_metadata(title, description, company_name=None, category="general"):
    """Generate metadata for owned media (FAST/Brightcove) - narrative only, no video upload"""
    base_title = title[:80] if title else "Portfolio Update"
    
    episode_title = f"{company_name}: {base_title}" if company_name else base_title
    
    episode_description = f"{description[:300]}..." if len(description) > 300 else description
    
    segment_outline = [
        f"1. Introduction: Context on {company_name or 'this update'}",
        f"2. Key Highlights: What makes this newsworthy",
        f"3. Market Impact: Why this matters to the industry",
        f"4. Expert Perspective: Analysis and insights",
        f"5. What's Next: Future outlook and implications"
    ]
    
    talking_points = [
        f"• The significance of {title[:50]}...",
        f"• How this impacts the {category} landscape",
        f"• Key metrics and data points to highlight",
        f"• Expert quotes and validation",
        f"• Connection to broader industry trends"
    ]
    
    cta_copy = f"Learn more about {company_name or 'this story'} and stay updated on {category} news."
    
    metadata_tags = [category.title()]
    if company_name:
        metadata_tags.append(company_name)
    tag_mapping = {
        "sports-tech": ["Sports", "Technology", "Performance"],
        "fintech": ["Finance", "Technology", "Innovation"],
        "startups": ["Startups", "VC", "Entrepreneurship"],
        "tech": ["Technology", "Innovation", "Digital"],
        "blockchain": ["Blockchain", "Crypto", "Web3"],
        "health-tech": ["Health", "Technology", "Wellness"]
    }
    metadata_tags.extend(tag_mapping.get(category, ["Business", "Industry"]))
    
    return {
        "episodeTitle": episode_title,
        "episodeDescription": episode_description,
        "segmentOutline": segment_outline,
        "talkingPoints": talking_points,
        "ctaCopy": cta_copy,
        "metadataTags": list(set(metadata_tags))
    }

def require_admin():
    """Check X-Admin-Key header for write operations. Returns error tuple if unauthorized."""
    if ADMIN_KEY:
        provided_key = request.headers.get("X-Admin-Key")
        if provided_key != ADMIN_KEY:
            return jsonify({"error": "Unauthorized - Admin key required"}), 401
    return None

CATEGORY_HASHTAGS = {
    "sports": ["#Sports", "#Athletics", "#GameDay", "#SportsNews", "#Competition"],
    "finance": ["#Finance", "#Investing", "#Markets", "#FinTech", "#WealthManagement", "#VC", "#AngelInvestor"],
    "web3": ["#Web3", "#Blockchain", "#Crypto", "#DeFi", "#NFT", "#Decentralized"],
    "startups": ["#Startups", "#Entrepreneurship", "#VC", "#AngelInvestor", "#Innovation", "#Founder", "#Funding"],
    "tech": ["#Technology", "#Tech", "#Innovation", "#Digital", "#TechNews", "#AI"],
    "news": ["#News", "#BreakingNews", "#Headlines", "#CurrentEvents"],
    "blockchain": ["#Blockchain", "#Crypto", "#DeFi", "#Web3", "#DigitalAssets"],
    "tokenization-web3": ["#Tokenization", "#Web3", "#RWA", "#DigitalAssets", "#Blockchain", "#DeFi"],
    "fintech": ["#FinTech", "#Finance", "#Banking", "#Payments", "#Innovation"],
    "sports-tech": ["#SportsTech", "#AthletePerformance", "#SportsAnalytics", "#Wearables"],
    "fitness-tech": ["#FitnessTech", "#HealthTech", "#Wearables", "#Wellness"],
    "health-tech": ["#HealthTech", "#MedTech", "#DigitalHealth", "#Healthcare"],
    "football-tech": ["#FootballTech", "#NFLTech", "#SportsAnalytics", "#GameDay"],
    "business": ["#Business", "#Leadership", "#Strategy", "#Growth", "#Management"],
    "books": ["#Books", "#Reading", "#Literature", "#BookRecommendations"],
    "ebooks": ["#eBooks", "#DigitalReading", "#Kindle", "#Reading"],
    "audiobooks": ["#Audiobooks", "#Listening", "#Books", "#Learning"],
    "digital-assets": ["#DigitalAssets", "#Crypto", "#Tokenization", "#Blockchain"],
    "design": ["#Design", "#UX", "#UI", "#Creative", "#VisualDesign"],
    "general": ["#Content", "#Articles", "#Reading", "#Curated"],
    "vc": ["#VC", "#VentureCapital", "#Funding", "#Startups", "#AngelInvestor", "#PrivateEquity"]
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"max_posts_per_day": 3, "auto_approve": False, "notification_webhook": "", "notification_enabled": False}

import threading

def send_article_notification(article, category, blocking=False):
    """Send webhook notification when a new article is added.
    By default runs in background thread to avoid blocking the request.
    Set blocking=True for test notifications that need immediate feedback."""
    settings = load_settings()
    webhook_url = settings.get("notification_webhook", "")
    enabled = settings.get("notification_enabled", False)
    
    if not enabled or not webhook_url:
        return None
    
    def do_send():
        try:
            # Format message for Slack/Teams/generic webhook
            payload = {
                "text": f"New article added to {category} feed",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*New Article in {category.title()} Feed*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{article.get('title', 'Untitled')}*\n{article.get('description', '')[:200]}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{article.get('url', '')}|Read Article>"
                        }
                    }
                ],
                # Generic webhook format
                "title": article.get("title", "New Article"),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "category": category,
                "date": article.get("date", ""),
                "source": "Kennect2Tech Media Feed"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            # Accept any 2xx status code as success
            is_success = 200 <= response.status_code < 300
            return {"success": is_success, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    if blocking:
        return do_send()
    else:
        # Fire-and-forget in background thread
        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()
        return {"success": True, "async": True}

def load_portfolio():
    portfolio_file = os.path.join(PORTFOLIO_DIR, "portfolio.json")
    if os.path.exists(portfolio_file):
        with open(portfolio_file, "r") as f:
            return json.load(f)
    return {
        "id": str(uuid.uuid4()),
        "name": "My Portfolio",
        "firmName": "",
        "visibility": "internal",
        "defaultDistribution": {"social": True, "email": True},
        "companies": [],
        "createdAt": datetime.datetime.utcnow().isoformat()
    }

def save_portfolio(portfolio):
    portfolio_file = os.path.join(PORTFOLIO_DIR, "portfolio.json")
    with open(portfolio_file, "w") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

def load_email_drafts():
    drafts_file = os.path.join(PORTFOLIO_DIR, "email_drafts.json")
    if os.path.exists(drafts_file):
        with open(drafts_file, "r") as f:
            return json.load(f)
    return []

def save_email_drafts(drafts):
    drafts_file = os.path.join(PORTFOLIO_DIR, "email_drafts.json")
    with open(drafts_file, "w") as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

SIGNAL_KEYWORDS = {
    "funding": ["raised", "funding", "series a", "series b", "seed round", "investment", "backed by", "secures", "million", "closes"],
    "launch": ["launches", "launched", "introducing", "announces", "unveils", "debuts", "releases", "new product"],
    "milestone": ["milestone", "achieves", "reaches", "surpasses", "growth", "expansion", "partnership", "acquisition"],
    "media": ["featured in", "coverage", "interview", "profile", "named", "recognized", "award", "selected"]
}

def detect_signals(text):
    text_lower = text.lower() if text else ""
    detected = []
    for signal_type, keywords in SIGNAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append(signal_type)
                break
    return list(set(detected))

def generate_email_draft(article, company_name, tone="informational"):
    title = article.get("title", "")
    description = article.get("description", "")
    url = article.get("url", "")
    signals = detect_signals(title + " " + description)
    
    signal_label = signals[0].title() if signals else "Update"
    
    subject = f"Portfolio Update: {company_name} - {signal_label}"
    
    if tone == "supportive":
        intro = f"Exciting news from our portfolio company {company_name}!"
    elif tone == "thought_leadership":
        intro = f"Strategic insight: {company_name} continues to execute on their vision."
    else:
        intro = f"Update from {company_name}:"
    
    body = f"""{intro}

{title}

{description}

Read more: {url}

---
Generated by Portfolio Updates Engine
"""
    
    return {
        "subject": subject,
        "body": body,
        "tone": tone,
        "signals": signals
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_publish_queue():
    queue_file = os.path.join(PUBLISH_DIR, "queue.json")
    if os.path.exists(queue_file):
        with open(queue_file, "r") as f:
            return json.load(f)
    return []

def save_publish_queue(queue):
    queue_file = os.path.join(PUBLISH_DIR, "queue.json")
    with open(queue_file, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def load_sent_urls():
    sent_file = os.path.join(PUBLISH_DIR, "sent_urls.json")
    if os.path.exists(sent_file):
        with open(sent_file, "r") as f:
            return json.load(f)
    return []

def save_sent_urls(urls):
    sent_file = os.path.join(PUBLISH_DIR, "sent_urls.json")
    with open(sent_file, "w") as f:
        json.dump(urls, f, indent=2)

def get_today_send_count():
    queue = load_publish_queue()
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return sum(1 for item in queue if item.get("status") == "sent" and item.get("sentAt", "").startswith(today))

def generate_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()

def generate_linkedin_copy(item):
    title = item.get("title", "")
    description = item.get("description", "")
    url = item.get("url", "")
    category = item.get("category", "general")
    
    hook = title[:100] if title else "Check this out"
    
    bullet1 = description[:150] if description else ""
    if len(description) > 150:
        bullet1 = description[:147] + "..."
    
    hashtags = CATEGORY_HASHTAGS.get(category, CATEGORY_HASHTAGS["general"])[:6]
    hashtag_str = " ".join(hashtags)
    
    post_text = f"{hook}\n\n{bullet1}\n\n{url}\n\n{hashtag_str}"
    
    return post_text

def sanitize(text):
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )

def scrape_metadata(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        html = requests.get(url, timeout=15, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")

        title = ""
        if soup.find("title"):
            title = soup.find("title").get_text(strip=True)
        
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"]

        desc = title
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            desc = desc_tag["content"]
        
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content"):
            desc = og_desc["content"]

        date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        date_tag = soup.find("meta", attrs={"property": "article:published_time"})
        if date_tag and date_tag.get("content"):
            try:
                parsed = datetime.datetime.fromisoformat(date_tag["content"].replace("Z", "+00:00"))
                date = parsed.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except:
                pass

        image = ""
        og_image = soup.find("meta", attrs={"property": "og:image"})
        if og_image and og_image.get("content"):
            image = og_image["content"]

        return {
            "title": sanitize(title) if title else "Untitled Article",
            "description": sanitize(desc)[:500] if desc else "No description available.",
            "date": date,
            "url": url,
            "image": image
        }

    except Exception as e:
        print(f"Scrape error for {url}: {e}")
        return {
            "title": "Unknown Title",
            "description": "No description found.",
            "date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "url": url,
            "image": ""
        }

def rss_item(meta, category=None):
    image_tag = ""
    if meta.get('image'):
        image_tag = f"\n        <enclosure url=\"{sanitize(meta['image'])}\" type=\"image/jpeg\" />"
    
    category_tag = ""
    if category:
        category_tag = f"\n        <category>{category}</category>"
    
    return f"""
    <item>
        <title>{meta['title']}</title>
        <link>{meta['url']}</link>
        <guid isPermaLink="true">{meta['url']}</guid>
        <description><![CDATA[{meta['description']}]]></description>
        <pubDate>{meta['date']}</pubDate>{category_tag}{image_tag}
    </item>"""

def load_feed_items(category):
    feed_file = os.path.join(FEEDS_DIR, f"{category}.json")
    if os.path.exists(feed_file):
        with open(feed_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_feed_items(category, items):
    feed_file = os.path.join(FEEDS_DIR, f"{category}.json")
    with open(feed_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def search_bing(query, count=10):
    if not BING_API_KEY:
        return None
    
    try:
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
        params = {"q": query, "count": count, "mkt": "en-US"}
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=10
        )
        data = response.json()
        
        results = []
        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "description": item.get("snippet", "")
            })
        return results
    except Exception as e:
        print(f"Bing search error: {e}")
        return None

def search_serpapi(query, count=10):
    if not SERPAPI_KEY:
        return None
    
    try:
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": count
        }
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10
        )
        data = response.json()
        
        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", "")
            })
        return results
    except Exception as e:
        print(f"SerpAPI search error: {e}")
        return None

def search_fallback(query, count=10):
    """Fallback search using curated website suggestions"""
    q = query.lower()
    all_websites = [
        {"title": "ESPN Sports News", "url": "https://www.espn.com", "description": "Sports news, scores, and highlights"},
        {"title": "Sports Illustrated", "url": "https://www.si.com", "description": "Sports journalism and coverage"},
        {"title": "Bleacher Report", "url": "https://www.bleacherreport.com", "description": "Sports news and commentary"},
        {"title": "CBS Sports", "url": "https://www.cbssports.com", "description": "Sports highlights and analysis"},
        {"title": "TechCrunch", "url": "https://techcrunch.com", "description": "Technology news and startup coverage"},
        {"title": "The Verge", "url": "https://www.theverge.com", "description": "Technology and culture"},
        {"title": "Wired", "url": "https://www.wired.com", "description": "Technology, business, and culture"},
        {"title": "Bloomberg", "url": "https://www.bloomberg.com", "description": "Financial news and analysis"},
        {"title": "CNBC", "url": "https://www.cnbc.com", "description": "Business and financial news"},
        {"title": "Yahoo Finance", "url": "https://finance.yahoo.com", "description": "Stock quotes and financial news"},
        {"title": "Forbes", "url": "https://www.forbes.com", "description": "Business news and analysis"},
        {"title": "Business Insider", "url": "https://www.businessinsider.com", "description": "Business and tech news"},
        {"title": "CoinDesk", "url": "https://www.coindesk.com", "description": "Cryptocurrency and blockchain news"},
        {"title": "Cointelegraph", "url": "https://cointelegraph.com", "description": "Blockchain and crypto news"},
        {"title": "BBC News", "url": "https://www.bbc.com/news", "description": "Global news coverage"},
        {"title": "Reuters", "url": "https://www.reuters.com", "description": "International news agency"},
        {"title": "AP News", "url": "https://apnews.com", "description": "Breaking news and reporting"},
        {"title": "NPR", "url": "https://www.npr.org", "description": "News and information"},
        {"title": "The Guardian", "url": "https://www.theguardian.com", "description": "Independent journalism"},
        {"title": "Standard Ebooks", "url": "https://standardebooks.org", "description": "Free public domain ebooks, beautifully formatted"},
        {"title": "Project Gutenberg", "url": "https://www.gutenberg.org", "description": "Free ebooks library with 70,000+ books"},
        {"title": "Open Library", "url": "https://openlibrary.org", "description": "Open library with millions of free books"},
        {"title": "Goodreads", "url": "https://www.goodreads.com", "description": "Book reviews, recommendations and reading lists"},
        {"title": "Book Riot", "url": "https://bookriot.com", "description": "Book news, reviews, and recommendations"},
        {"title": "Literary Hub", "url": "https://lithub.com", "description": "Literary news, essays and book culture"},
        {"title": "The New York Times Books", "url": "https://www.nytimes.com/section/books", "description": "Book reviews and bestseller lists"},
        {"title": "Publishers Weekly", "url": "https://www.publishersweekly.com", "description": "Publishing industry news and book reviews"},
        {"title": "Kindle Daily Deals", "url": "https://www.amazon.com/kindle-dbs/deals", "description": "Daily discounted Kindle ebooks"},
        {"title": "Librivox", "url": "https://librivox.org", "description": "Free public domain audiobooks"},
    ]
    
    results = []
    for site in all_websites:
        if q in site["title"].lower() or q in site["description"].lower():
            results.append(site)
    
    if len(results) < count:
        for site in all_websites:
            if site not in results:
                results.append(site)
    
    return results[:count]

@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/hub")
def hub():
    return send_from_directory('static', 'hub.html')

SUBSCRIBERS_FILE = "subscribers.json"

def generate_unsubscribe_token():
    import secrets
    return secrets.token_urlsafe(32)

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                if len(data) == 0:
                    return {}
                if isinstance(data[0], str):
                    new_data = {}
                    for email in data:
                        new_data[email] = {
                            "token": generate_unsubscribe_token(),
                            "subscribed_at": dt.now().isoformat(),
                            "preferences": {"categories": ["all"], "frequency": "weekly"},
                            "active": True
                        }
                    save_subscribers(new_data)
                    return new_data
            return data
    return {}

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f, indent=2)

@app.route("/api/hub/subscribe", methods=["POST"])
def hub_subscribe():
    data = request.json
    email = data.get("email", "").strip().lower()
    categories = data.get("categories", ["all"])
    frequency = data.get("frequency", "weekly")
    
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Valid email required"}), 400
    
    subscribers = load_subscribers()
    
    if email in subscribers and subscribers[email].get("active", True):
        return jsonify({"success": True, "message": "Already subscribed"})
    
    token = generate_unsubscribe_token()
    subscribers[email] = {
        "token": token,
        "subscribed_at": dt.now().isoformat(),
        "preferences": {"categories": categories, "frequency": frequency},
        "active": True
    }
    save_subscribers(subscribers)
    
    return jsonify({"success": True, "message": "Subscribed successfully"})

@app.route("/api/hub/unsubscribe", methods=["POST"])
def hub_unsubscribe():
    data = request.json
    email = data.get("email", "").strip().lower()
    token = data.get("token", "")
    
    subscribers = load_subscribers()
    
    if email not in subscribers:
        return jsonify({"success": False, "error": "Email not found"}), 404
    
    if subscribers[email].get("token") != token:
        return jsonify({"success": False, "error": "Invalid token"}), 403
    
    subscribers[email]["active"] = False
    subscribers[email]["unsubscribed_at"] = dt.now().isoformat()
    save_subscribers(subscribers)
    
    return jsonify({"success": True, "message": "Unsubscribed successfully"})

@app.route("/api/hub/preferences", methods=["POST"])
def update_preferences():
    data = request.json
    email = data.get("email", "").strip().lower()
    token = data.get("token", "")
    categories = data.get("categories", ["all"])
    frequency = data.get("frequency", "weekly")
    
    subscribers = load_subscribers()
    
    if email not in subscribers:
        return jsonify({"success": False, "error": "Email not found"}), 404
    
    if subscribers[email].get("token") != token:
        return jsonify({"success": False, "error": "Invalid token"}), 403
    
    subscribers[email]["preferences"] = {"categories": categories, "frequency": frequency}
    save_subscribers(subscribers)
    
    return jsonify({"success": True, "message": "Preferences updated"})

@app.route("/unsubscribe")
def unsubscribe_page():
    email = request.args.get("email", "")
    token = request.args.get("token", "")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unsubscribe | Kennect2Tech</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0a0a0a; color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
    .container {{ max-width: 400px; text-align: center; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 16px; }}
    p {{ color: #94a3b8; margin-bottom: 24px; line-height: 1.6; }}
    .btn {{ display: inline-block; padding: 12px 24px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; text-decoration: none; }}
    .btn-danger {{ background: #ef4444; color: #fff; }}
    .btn-danger:hover {{ background: #dc2626; }}
    .btn-secondary {{ background: #222; color: #fff; margin-left: 12px; }}
    .btn-secondary:hover {{ background: #333; }}
    .result {{ padding: 20px; border-radius: 8px; margin-top: 20px; }}
    .success {{ background: rgba(34, 197, 94, 0.2); border: 1px solid #22c55e; }}
    .error {{ background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Unsubscribe from Newsletter</h1>
    <p>Are you sure you want to unsubscribe <strong>{email}</strong> from the Kennect2Tech News Hub updates?</p>
    <button class="btn btn-danger" onclick="unsubscribe()">Yes, Unsubscribe</button>
    <a href="/hub" class="btn btn-secondary">Cancel</a>
    <div id="result"></div>
  </div>
  <script>
    async function unsubscribe() {{
      try {{
        const res = await fetch('/api/hub/unsubscribe', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ email: '{email}', token: '{token}' }})
        }});
        const data = await res.json();
        document.getElementById('result').innerHTML = data.success 
          ? '<div class="result success">You have been unsubscribed.</div>'
          : '<div class="result error">' + (data.error || 'Failed to unsubscribe') + '</div>';
      }} catch (e) {{
        document.getElementById('result').innerHTML = '<div class="result error">An error occurred</div>';
      }}
    }}
  </script>
</body>
</html>'''

@app.route("/api/hub/subscribers", methods=["GET"])
def list_subscribers():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    subscribers = load_subscribers()
    active = {email: data for email, data in subscribers.items() if data.get("active", True)}
    return jsonify(active)

@app.route("/api/scrape", methods=["POST"])
def preview_scrape():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    meta = scrape_metadata(url)
    return jsonify(meta)

@app.route("/api/create", methods=["POST"])
def create_feed():
    # No admin key required - RSS feed creation is public
    data = request.json
    url = data.get("url")
    category = data.get("category", "general")
    custom_title = data.get("title")
    custom_description = data.get("description")

    if not url:
        return jsonify({"error": "URL required"}), 400

    meta = scrape_metadata(url)
    
    if custom_title:
        meta["title"] = sanitize(custom_title)
    if custom_description:
        meta["description"] = sanitize(custom_description)[:500]

    items = load_feed_items(category)
    
    existing_urls = [item["url"] for item in items]
    is_new = url not in existing_urls
    if is_new:
        items.insert(0, meta)
        items = items[:100]
        save_feed_items(category, items)
        # Send webhook notification for new article
        send_article_notification(meta, category)

    return jsonify({
        "status": "success", 
        "feed_url": f"/feed/{category}",
        "item": meta,
        "total_items": len(items),
        "is_new": is_new
    })

@app.route("/api/feeds")
def list_feeds():
    feeds = []
    categories = ["sports", "finance", "web3", "startups", "tech", "news", "blockchain", "digital-assets", "business", "design", "general", "books", "ebooks", "audiobooks", "tokenization-web3", "fintech", "sports-tech", "fitness-tech", "health-tech", "football-tech", "marketing", "vc-tools", "video", "webinar", "vc"]
    
    category_icons = {
        "sports": "&#9917;", "finance": "&#128176;", "web3": "&#127760;", "startups": "&#128640;",
        "tech": "&#128187;", "news": "&#128240;", "blockchain": "&#9939;", "digital-assets": "&#129689;",
        "business": "&#128188;", "design": "&#127912;", "general": "&#128196;", "books": "&#128218;",
        "ebooks": "&#128214;", "audiobooks": "&#127911;", "tokenization-web3": "&#129689;",
        "fintech": "&#128179;", "sports-tech": "&#127939;", "fitness-tech": "&#128170;",
        "health-tech": "&#129657;", "football-tech": "&#127944;", "marketing": "&#128226;",
        "vc-tools": "&#128200;", "video": "&#127909;", "webinar": "&#127897;", "vc": "&#128176;"
    }
    
    for cat in categories:
        items = load_feed_items(cat)
        if items:
            feeds.append({
                "category": cat,
                "feed_url": f"/feed/{cat}",
                "item_count": len(items),
                "latest_item": items[0] if items else None,
                "icon": category_icons.get(cat, "&#128196;")
            })
    
    return jsonify(feeds)

@app.route("/api/feeds/<category>")
def get_feed_items(category):
    items = load_feed_items(category)
    return jsonify(items)

@app.route("/api/feeds/<category>/<int:index>", methods=["DELETE"])
def delete_feed_item(category, index):
    # No admin key required - RSS feed management is public
    items = load_feed_items(category)
    if 0 <= index < len(items):
        deleted = items.pop(index)
        save_feed_items(category, items)
        return jsonify({"status": "deleted", "item": deleted})
    return jsonify({"error": "Item not found"}), 404

@app.route("/api/reader")
def get_all_articles():
    categories = ["sports", "finance", "web3", "startups", "tech", "news", "blockchain", "digital-assets", "business", "design", "general", "books", "ebooks", "audiobooks", "tokenization-web3", "fintech", "sports-tech", "fitness-tech", "health-tech", "football-tech", "marketing", "vc-tools", "video", "webinar", "vc"]
    all_articles = []
    
    for cat in categories:
        items = load_feed_items(cat)
        for item in items:
            item["category"] = cat
            all_articles.append(item)
    
    all_articles.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify(all_articles[:50])

@app.route("/api/search")
def search_topics():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    results = search_bing(query)
    if not results:
        results = search_serpapi(query)
    
    if not results:
        results = search_fallback(query)
    
    return jsonify({"results": results})

@app.route("/feed/<category>")
def serve_feed(category):
    items = load_feed_items(category)
    
    items_xml = ""
    for item in items:
        items_xml += rss_item(item, category)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>Preps2Pro {category.title()} Feed</title>
    <link>https://feedforge.replit.app</link>
    <description>Aggregated {category.title()} content from Preps2Pro Media Feed Generator</description>
    <language>en-us</language>
    <lastBuildDate>{datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
    <atom:link href="https://feedforge.replit.app/feed/{category}" rel="self" type="application/rss+xml" />{items_xml}
</channel>
</rss>"""

    return rss, 200, {"Content-Type": "application/rss+xml; charset=utf-8"}

@app.route("/feed/combined")
def serve_combined_feed():
    categories = ["sports", "finance", "web3", "startups", "tech", "news", "blockchain", "digital-assets", "business", "design", "general"]
    all_items = []
    
    for cat in categories:
        items = load_feed_items(cat)
        for item in items:
            item["_category"] = cat
            all_items.append(item)
    
    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)
    all_items = all_items[:50]
    
    items_xml = ""
    for item in all_items:
        items_xml += rss_item(item, item.get("_category"))

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>Preps2Pro Combined Feed</title>
    <link>https://feedforge.replit.app</link>
    <description>All content from Preps2Pro Media Feed Generator</description>
    <language>en-us</language>
    <lastBuildDate>{datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
    <atom:link href="https://feedforge.replit.app/feed/combined" rel="self" type="application/rss+xml" />{items_xml}
</channel>
</rss>"""

    return rss, 200, {"Content-Type": "application/rss+xml; charset=utf-8"}

GROUPS_FILE = os.path.join(FEEDS_DIR, "custom_groups.json")

def load_custom_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return []

def save_custom_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)

@app.route("/api/groups", methods=["GET"])
def list_groups():
    groups = load_custom_groups()
    return jsonify(groups)

@app.route("/api/groups", methods=["POST"])
def create_group():
    data = request.json
    name = data.get("name", "").strip()
    articles = data.get("articles", [])
    
    if not name:
        return jsonify({"error": "Name required"}), 400
    if not articles:
        return jsonify({"error": "At least one article required"}), 400
    
    groups = load_custom_groups()
    
    group = {
        "id": str(uuid.uuid4()),
        "name": name,
        "articles": articles,
        "createdAt": datetime.datetime.utcnow().isoformat()
    }
    
    groups.insert(0, group)
    save_custom_groups(groups)
    
    return jsonify({"status": "success", "group": group})

@app.route("/api/groups/<group_id>", methods=["DELETE"])
def delete_group(group_id):
    groups = load_custom_groups()
    groups = [g for g in groups if g.get("id") != group_id]
    save_custom_groups(groups)
    return jsonify({"status": "deleted"})

@app.route("/feed/group/<group_id>")
def serve_group_feed(group_id):
    groups = load_custom_groups()
    group = next((g for g in groups if g.get("id") == group_id), None)
    
    if not group:
        return "Group not found", 404
    
    items_xml = ""
    for article in group.get("articles", []):
        meta = {
            "title": sanitize(article.get("title", "Untitled")),
            "url": article.get("url", ""),
            "description": sanitize(article.get("title", "")),
            "date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "image": ""
        }
        items_xml += rss_item(meta, article.get("category"))
    
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{sanitize(group.get("name", "Custom Feed"))}</title>
    <link>https://feedforge.replit.app</link>
    <description>Custom combined feed: {sanitize(group.get("name", ""))}</description>
    <language>en-us</language>
    <lastBuildDate>{datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
    <atom:link href="https://feedforge.replit.app/feed/group/{group_id}" rel="self" type="application/rss+xml" />{items_xml}
</channel>
</rss>"""
    
    return rss, 200, {"Content-Type": "application/rss+xml; charset=utf-8"}

@app.route("/api/publish/queue", methods=["GET"])
def get_publish_queue():
    queue = load_publish_queue()
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    
    if status_filter:
        queue = [item for item in queue if item.get("status") == status_filter]
    if category_filter:
        queue = [item for item in queue if item.get("category") == category_filter]
    
    return jsonify(queue)

@app.route("/api/publish/queue", methods=["POST"])
def add_to_publish_queue():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    url = data.get("url")
    title = data.get("title", "")
    description = data.get("description", "")
    category = data.get("category", "general")
    image = data.get("image", "")
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    queue = load_publish_queue()
    
    url_hash = generate_url_hash(url)
    if any(item.get("urlHash") == url_hash for item in queue):
        return jsonify({"error": "URL already in queue"}), 400
    
    item = {
        "id": str(uuid.uuid4()),
        "url": url,
        "urlHash": url_hash,
        "title": title,
        "description": description,
        "category": category,
        "image": image,
        "postText": generate_linkedin_copy({"title": title, "description": description, "url": url, "category": category}),
        "status": "draft",
        "createdAt": datetime.datetime.utcnow().isoformat(),
        "sentAt": None,
        "error": None
    }
    
    queue.insert(0, item)
    save_publish_queue(queue)
    
    return jsonify({"status": "success", "item": item})

@app.route("/api/publish/queue/<item_id>", methods=["PATCH"])
def update_queue_item(item_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    queue = load_publish_queue()
    
    for item in queue:
        if item.get("id") == item_id:
            if "postText" in data:
                item["postText"] = data["postText"]
            if "status" in data:
                item["status"] = data["status"]
            if "title" in data:
                item["title"] = data["title"]
            save_publish_queue(queue)
            return jsonify({"status": "success", "item": item})
    
    return jsonify({"error": "Item not found"}), 404

@app.route("/api/publish/queue/<item_id>", methods=["DELETE"])
def delete_queue_item(item_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    queue = load_publish_queue()
    queue = [item for item in queue if item.get("id") != item_id]
    save_publish_queue(queue)
    return jsonify({"status": "deleted"})

@app.route("/api/publish/send/<item_id>", methods=["POST"])
def send_publish_item(item_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    settings = load_settings()
    max_per_day = settings.get("max_posts_per_day", 3)
    
    if get_today_send_count() >= max_per_day:
        return jsonify({"error": f"Rate limit reached ({max_per_day}/day)"}), 429
    
    queue = load_publish_queue()
    item = next((i for i in queue if i.get("id") == item_id), None)
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    sent_urls = load_sent_urls()
    if item.get("urlHash") in sent_urls:
        return jsonify({"error": "URL already sent previously"}), 400
    
    webhook_url = os.environ.get("ZAPIER_WEBHOOK_URL")
    buffer_token = os.environ.get("BUFFER_ACCESS_TOKEN")
    buffer_profile = os.environ.get("BUFFER_PROFILE_ID")
    
    success = False
    error_msg = None
    
    if webhook_url:
        try:
            payload = {
                "text": item.get("postText", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": "FeedForge",
                "category": item.get("category", ""),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code in [200, 201, 202]:
                success = True
            else:
                error_msg = f"Webhook returned {resp.status_code}"
        except Exception as e:
            error_msg = str(e)
    elif buffer_token and buffer_profile:
        try:
            headers = {"Authorization": f"Bearer {buffer_token}"}
            payload = {
                "profile_ids": [buffer_profile],
                "text": item.get("postText", ""),
                "media": {"link": item.get("url", "")}
            }
            resp = requests.post("https://api.bufferapp.com/1/updates/create.json", headers=headers, data=payload, timeout=10)
            if resp.status_code in [200, 201]:
                success = True
            else:
                error_msg = f"Buffer returned {resp.status_code}"
        except Exception as e:
            error_msg = str(e)
    else:
        return jsonify({"error": "No integration configured. Set ZAPIER_WEBHOOK_URL or Buffer credentials."}), 400
    
    for i in queue:
        if i.get("id") == item_id:
            if success:
                i["status"] = "sent"
                i["sentAt"] = datetime.datetime.utcnow().isoformat()
                sent_urls.append(item.get("urlHash"))
                save_sent_urls(sent_urls)
            else:
                i["status"] = "failed"
                i["error"] = error_msg
            break
    
    save_publish_queue(queue)
    
    if success:
        return jsonify({"status": "sent", "item": item})
    else:
        return jsonify({"error": error_msg, "status": "failed"}), 500

@app.route("/api/publish/settings", methods=["GET"])
def get_publish_settings():
    settings = load_settings()
    settings["zapier_configured"] = bool(os.environ.get("ZAPIER_WEBHOOK_URL"))
    settings["buffer_configured"] = bool(os.environ.get("BUFFER_ACCESS_TOKEN") and os.environ.get("BUFFER_PROFILE_ID"))
    settings["today_sent"] = get_today_send_count()
    return jsonify(settings)

@app.route("/api/publish/settings", methods=["POST"])
def update_publish_settings():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    settings = load_settings()
    
    if "max_posts_per_day" in data:
        settings["max_posts_per_day"] = int(data["max_posts_per_day"])
    if "auto_approve" in data:
        settings["auto_approve"] = bool(data["auto_approve"])
    
    save_settings(settings)
    return jsonify(settings)

@app.route("/api/notifications/settings", methods=["GET"])
def get_notification_settings():
    settings = load_settings()
    return jsonify({
        "notification_webhook": settings.get("notification_webhook", ""),
        "notification_enabled": settings.get("notification_enabled", False)
    })

@app.route("/api/notifications/settings", methods=["POST"])
def update_notification_settings():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    settings = load_settings()
    
    if "notification_webhook" in data:
        settings["notification_webhook"] = data["notification_webhook"]
    if "notification_enabled" in data:
        settings["notification_enabled"] = bool(data["notification_enabled"])
    
    save_settings(settings)
    return jsonify({
        "notification_webhook": settings.get("notification_webhook", ""),
        "notification_enabled": settings.get("notification_enabled", False)
    })

@app.route("/api/notifications/test", methods=["POST"])
def test_notification():
    """Send a test notification to verify webhook is working"""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    settings = load_settings()
    webhook_url = settings.get("notification_webhook", "")
    
    if not webhook_url:
        return jsonify({"error": "No webhook URL configured"}), 400
    
    test_article = {
        "title": "Test Notification from Kennect2Tech",
        "description": "This is a test notification to verify your webhook is working correctly.",
        "url": "https://kennect2tech.example.com/test",
        "date": datetime.datetime.utcnow().isoformat()
    }
    
    # Force send for testing even if notifications are disabled
    try:
        payload = {
            "text": "Test notification from Kennect2Tech Media Feed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Test Notification*\nThis confirms your webhook integration is working correctly."
                    }
                }
            ],
            "title": test_article["title"],
            "description": test_article["description"],
            "url": test_article["url"],
            "category": "test",
            "source": "Kennect2Tech Media Feed"
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        # Accept any 2xx status code as success
        is_success = 200 <= response.status_code < 300
        
        if is_success:
            return jsonify({"status": "success", "message": "Test notification sent!", "status_code": response.status_code})
        else:
            return jsonify({"error": f"Webhook returned status {response.status_code}", "status": "failed", "status_code": response.status_code}), 400
    except requests.exceptions.Timeout:
        return jsonify({"error": "Webhook request timed out", "status": "failed"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to webhook URL", "status": "failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e), "status": "failed"}), 500

@app.route("/api/publish/generate-copy", methods=["POST"])
def generate_copy():
    data = request.json
    post_text = generate_linkedin_copy(data)
    return jsonify({"postText": post_text})

@app.route("/api/portfolio", methods=["GET"])
def get_portfolio():
    portfolio = load_portfolio()
    return jsonify(portfolio)

@app.route("/api/portfolio", methods=["PATCH"])
def update_portfolio():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    portfolio = load_portfolio()
    
    if "name" in data:
        portfolio["name"] = data["name"]
    if "firmName" in data:
        portfolio["firmName"] = data["firmName"]
    if "visibility" in data:
        portfolio["visibility"] = data["visibility"]
    if "defaultDistribution" in data:
        portfolio["defaultDistribution"] = data["defaultDistribution"]
    
    save_portfolio(portfolio)
    return jsonify(portfolio)

@app.route("/api/portfolio/companies", methods=["GET"])
def get_companies():
    portfolio = load_portfolio()
    return jsonify(portfolio.get("companies", []))

@app.route("/api/portfolio/companies", methods=["POST"])
def add_company():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    name = data.get("name")
    
    if not name:
        return jsonify({"error": "Company name required"}), 400
    
    portfolio = load_portfolio()
    
    company = {
        "id": str(uuid.uuid4()),
        "name": name,
        "website": data.get("website", ""),
        "industry": data.get("industry", ""),
        "stage": data.get("stage", ""),
        "tags": data.get("tags", []),
        "assignedFeeds": data.get("assignedFeeds", []),
        "distributionSurfaces": data.get("distributionSurfaces", {"social": True, "email": True}),
        "createdAt": datetime.datetime.utcnow().isoformat()
    }
    
    portfolio["companies"].append(company)
    save_portfolio(portfolio)
    
    return jsonify({"status": "success", "company": company})

@app.route("/api/portfolio/companies/<company_id>", methods=["GET"])
def get_company(company_id):
    portfolio = load_portfolio()
    company = next((c for c in portfolio["companies"] if c["id"] == company_id), None)
    
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    return jsonify(company)

@app.route("/api/portfolio/companies/<company_id>", methods=["PATCH"])
def update_company(company_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    portfolio = load_portfolio()
    
    for company in portfolio["companies"]:
        if company["id"] == company_id:
            if "name" in data:
                company["name"] = data["name"]
            if "website" in data:
                company["website"] = data["website"]
            if "industry" in data:
                company["industry"] = data["industry"]
            if "stage" in data:
                company["stage"] = data["stage"]
            if "tags" in data:
                company["tags"] = data["tags"]
            if "assignedFeeds" in data:
                company["assignedFeeds"] = data["assignedFeeds"]
            if "distributionSurfaces" in data:
                company["distributionSurfaces"] = data["distributionSurfaces"]
            
            save_portfolio(portfolio)
            return jsonify({"status": "success", "company": company})
    
    return jsonify({"error": "Company not found"}), 404

@app.route("/api/portfolio/companies/<company_id>", methods=["DELETE"])
def delete_company(company_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    portfolio = load_portfolio()
    portfolio["companies"] = [c for c in portfolio["companies"] if c["id"] != company_id]
    save_portfolio(portfolio)
    return jsonify({"status": "deleted"})

@app.route("/api/portfolio/companies/<company_id>/feeds", methods=["POST"])
def assign_feed_to_company(company_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    feed_category = data.get("category")
    
    if not feed_category:
        return jsonify({"error": "Feed category required"}), 400
    
    portfolio = load_portfolio()
    
    for company in portfolio["companies"]:
        if company["id"] == company_id:
            if feed_category not in company.get("assignedFeeds", []):
                if "assignedFeeds" not in company:
                    company["assignedFeeds"] = []
                company["assignedFeeds"].append(feed_category)
                save_portfolio(portfolio)
            return jsonify({"status": "success", "company": company})
    
    return jsonify({"error": "Company not found"}), 404

@app.route("/api/portfolio/companies/<company_id>/feeds/<feed_category>", methods=["DELETE"])
def unassign_feed_from_company(company_id, feed_category):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    portfolio = load_portfolio()
    
    for company in portfolio["companies"]:
        if company["id"] == company_id:
            if "assignedFeeds" in company and feed_category in company["assignedFeeds"]:
                company["assignedFeeds"].remove(feed_category)
                save_portfolio(portfolio)
            return jsonify({"status": "success", "company": company})
    
    return jsonify({"error": "Company not found"}), 404

@app.route("/api/portfolio/updates", methods=["GET"])
def get_portfolio_updates():
    portfolio = load_portfolio()
    all_updates = []
    
    for company in portfolio.get("companies", []):
        company_id = company["id"]
        company_name = company["name"]
        assigned_feeds = company.get("assignedFeeds", [])
        distribution = company.get("distributionSurfaces", {"social": True, "email": True})
        
        for feed_category in assigned_feeds:
            items = load_feed_items(feed_category)
            for item in items[:10]:
                signals = detect_signals(item.get("title", "") + " " + item.get("description", ""))
                all_updates.append({
                    "companyId": company_id,
                    "companyName": company_name,
                    "feedCategory": feed_category,
                    "article": item,
                    "signals": signals,
                    "distribution": distribution
                })
    
    all_updates.sort(key=lambda x: x["article"].get("date", ""), reverse=True)
    return jsonify(all_updates[:50])

@app.route("/api/portfolio/updates/generate-drafts", methods=["POST"])
def generate_portfolio_drafts():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    company_id = data.get("companyId")
    article = data.get("article")
    draft_type = data.get("type", "both")
    tone = data.get("tone", "informational")
    
    if not company_id or not article:
        return jsonify({"error": "companyId and article required"}), 400
    
    portfolio = load_portfolio()
    company = next((c for c in portfolio["companies"] if c["id"] == company_id), None)
    
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    result = {
        "companyId": company_id,
        "companyName": company["name"],
        "article": article
    }
    
    if draft_type in ["social", "both"]:
        result["socialDraft"] = generate_linkedin_copy({
            "title": f"{company['name']}: {article.get('title', '')}",
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "category": article.get("category", "general")
        })
    
    if draft_type in ["email", "both"]:
        result["emailDraft"] = generate_email_draft(article, company["name"], tone)
    
    return jsonify(result)

@app.route("/api/portfolio/updates/queue-social", methods=["POST"])
def queue_social_from_portfolio():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    company_id = data.get("companyId")
    article = data.get("article")
    custom_text = data.get("postText")
    
    if not company_id or not article:
        return jsonify({"error": "companyId and article required"}), 400
    
    portfolio = load_portfolio()
    company = next((c for c in portfolio["companies"] if c["id"] == company_id), None)
    
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    url = article.get("url", "")
    if not url:
        return jsonify({"error": "Article URL required"}), 400
    
    queue = load_publish_queue()
    url_hash = generate_url_hash(url)
    
    if any(item.get("urlHash") == url_hash for item in queue):
        return jsonify({"error": "URL already in queue"}), 400
    
    post_text = custom_text or generate_linkedin_copy({
        "title": f"{company['name']}: {article.get('title', '')}",
        "description": article.get("description", ""),
        "url": url,
        "category": article.get("category", "general")
    })
    
    item = {
        "id": str(uuid.uuid4()),
        "url": url,
        "urlHash": url_hash,
        "title": article.get("title", ""),
        "description": article.get("description", ""),
        "category": article.get("category", "general"),
        "image": article.get("image", ""),
        "postText": post_text,
        "status": "draft",
        "companyId": company_id,
        "companyName": company["name"],
        "source": "portfolio",
        "createdAt": datetime.datetime.utcnow().isoformat(),
        "sentAt": None,
        "error": None
    }
    
    queue.insert(0, item)
    save_publish_queue(queue)
    
    return jsonify({"status": "success", "item": item})

@app.route("/api/portfolio/email-drafts", methods=["GET"])
def get_email_drafts():
    drafts = load_email_drafts()
    return jsonify(drafts)

@app.route("/api/portfolio/email-drafts", methods=["POST"])
def save_email_draft():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    company_id = data.get("companyId")
    article = data.get("article")
    tone = data.get("tone", "informational")
    
    if not company_id or not article:
        return jsonify({"error": "companyId and article required"}), 400
    
    portfolio = load_portfolio()
    company = next((c for c in portfolio["companies"] if c["id"] == company_id), None)
    
    if not company:
        return jsonify({"error": "Company not found"}), 404
    
    email_draft = generate_email_draft(article, company["name"], tone)
    
    draft = {
        "id": str(uuid.uuid4()),
        "companyId": company_id,
        "companyName": company["name"],
        "article": article,
        "subject": email_draft["subject"],
        "body": email_draft["body"],
        "tone": tone,
        "signals": email_draft["signals"],
        "status": "draft",
        "createdAt": datetime.datetime.utcnow().isoformat()
    }
    
    drafts = load_email_drafts()
    drafts.insert(0, draft)
    save_email_drafts(drafts)
    
    return jsonify({"status": "success", "draft": draft})

@app.route("/api/portfolio/email-drafts/<draft_id>", methods=["PATCH"])
def update_email_draft(draft_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    drafts = load_email_drafts()
    
    for draft in drafts:
        if draft["id"] == draft_id:
            if "subject" in data:
                draft["subject"] = data["subject"]
            if "body" in data:
                draft["body"] = data["body"]
            if "status" in data:
                draft["status"] = data["status"]
            save_email_drafts(drafts)
            return jsonify({"status": "success", "draft": draft})
    
    return jsonify({"error": "Draft not found"}), 404

@app.route("/api/portfolio/email-drafts/<draft_id>", methods=["DELETE"])
def delete_email_draft(draft_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    drafts = load_email_drafts()
    drafts = [d for d in drafts if d["id"] != draft_id]
    save_email_drafts(drafts)
    return jsonify({"status": "deleted"})

@app.route("/api/playbooks", methods=["GET"])
def get_playbooks():
    return jsonify(FOUNDER_PLAYBOOKS)

@app.route("/api/playbooks/<playbook_id>", methods=["GET"])
def get_playbook(playbook_id):
    playbook = next((p for p in FOUNDER_PLAYBOOKS if p["id"] == playbook_id), None)
    if not playbook:
        return jsonify({"error": "Playbook not found"}), 404
    return jsonify(playbook)

@app.route("/api/templates/launch", methods=["GET"])
def get_launch_templates():
    return jsonify(LAUNCH_TEMPLATES)

@app.route("/api/templates/investor-updates", methods=["GET"])
def get_investor_update_templates():
    return jsonify(INVESTOR_UPDATE_TEMPLATES)

@app.route("/api/templates/sports-tech", methods=["GET"])
def get_sports_tech_templates():
    return jsonify(SPORTS_TECH_TEMPLATES)

@app.route("/api/prompts/thought-leadership", methods=["GET"])
def get_thought_leadership_prompts():
    import random
    prompts = THOUGHT_LEADERSHIP_PROMPTS.copy()
    random.shuffle(prompts)
    return jsonify(prompts[:5])

@app.route("/api/owned-media/generate", methods=["POST"])
def generate_owned_media():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    title = data.get("title", "")
    description = data.get("description", "")
    company_name = data.get("companyName")
    category = data.get("category", "general")
    
    if not title:
        return jsonify({"error": "Title required"}), 400
    
    metadata = generate_owned_media_metadata(title, description, company_name, category)
    return jsonify(metadata)

@app.route("/api/import/nvca", methods=["POST"])
def import_nvca_feed():
    """Import articles from NVCA RSS feed into VC category"""
    try:
        import xml.etree.ElementTree as ET
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get("https://nvca.org/feed", timeout=15, headers=headers)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            return jsonify({"error": "Invalid RSS feed"}), 400
        
        items = load_feed_items("vc")
        existing_urls = [item["url"] for item in items]
        imported = 0
        
        for item in channel.findall("item")[:20]:
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_date_el = item.find("pubDate")
            
            if link_el is None or link_el.text in existing_urls:
                continue
            
            title = title_el.text if title_el is not None else "NVCA Update"
            description = ""
            if desc_el is not None and desc_el.text:
                soup = BeautifulSoup(desc_el.text, "html.parser")
                description = soup.get_text()[:500]
            
            date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            if pub_date_el is not None and pub_date_el.text:
                try:
                    from email.utils import parsedate_to_datetime
                    parsed = parsedate_to_datetime(pub_date_el.text)
                    date = parsed.strftime("%a, %d %b %Y %H:%M:%S GMT")
                except:
                    pass
            
            meta = {
                "title": sanitize(title),
                "description": sanitize(description) if description else sanitize(title),
                "url": link_el.text,
                "date": date,
                "image": "",
                "source": "NVCA"
            }
            items.insert(0, meta)
            imported += 1
        
        items = items[:100]
        save_feed_items("vc", items)
        
        return jsonify({
            "status": "success",
            "imported": imported,
            "total": len(items),
            "source": "National Venture Capital Association"
        })
    except Exception as e:
        print(f"NVCA import error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/import/pitchbook", methods=["POST"])
def import_pitchbook_news():
    """Scrape articles from Pitchbook news page into VC category"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get("https://pitchbook.com/news", timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        items = load_feed_items("vc")
        existing_urls = [item["url"] for item in items]
        imported = 0
        
        selectors = [
            ("article a[href*='/news/']", "h2, h3, .title"),
            (".news-item a", "h2, h3, .headline"),
            ("a.article-link", "h2, h3"),
            ("[class*='card'] a[href*='/news/']", "h2, h3, h4"),
            (".content-list a[href*='/news/']", "h2, h3")
        ]
        
        found_articles = []
        
        for link_selector, title_selector in selectors:
            links = soup.select(link_selector)
            for link in links[:15]:
                href = link.get("href", "")
                if not href or href in existing_urls:
                    continue
                
                if not href.startswith("http"):
                    href = "https://pitchbook.com" + href
                
                if href in existing_urls or href in [a["url"] for a in found_articles]:
                    continue
                
                title_el = link.select_one(title_selector)
                if title_el:
                    title = title_el.get_text(strip=True)
                else:
                    title = link.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                found_articles.append({
                    "title": sanitize(title[:200]),
                    "url": href
                })
            
            if found_articles:
                break
        
        if not found_articles:
            all_links = soup.select("a[href*='/news/']")
            for link in all_links[:20]:
                href = link.get("href", "")
                if not href:
                    continue
                if not href.startswith("http"):
                    href = "https://pitchbook.com" + href
                if href in existing_urls or "/news/reports" in href:
                    continue
                
                title = link.get_text(strip=True)
                if title and len(title) > 15 and href not in [a["url"] for a in found_articles]:
                    found_articles.append({
                        "title": sanitize(title[:200]),
                        "url": href
                    })
        
        for article in found_articles[:10]:
            meta = {
                "title": article["title"],
                "description": f"VC/PE news from Pitchbook: {article['title'][:100]}",
                "url": article["url"],
                "date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "image": "",
                "source": "Pitchbook"
            }
            items.insert(0, meta)
            imported += 1
        
        items = items[:100]
        save_feed_items("vc", items)
        
        return jsonify({
            "status": "success",
            "imported": imported,
            "total": len(items),
            "source": "Pitchbook"
        })
    except Exception as e:
        print(f"Pitchbook import error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vc-sources", methods=["GET"])
def get_vc_sources():
    """Get list of VC data sources with their status"""
    items = load_feed_items("vc")
    nvca_count = len([i for i in items if i.get("source") == "NVCA"])
    pitchbook_count = len([i for i in items if i.get("source") == "Pitchbook"])
    
    return jsonify({
        "sources": [
            {
                "id": "nvca",
                "name": "National Venture Capital Association",
                "url": "https://nvca.org",
                "description": "Trade association for the US VC industry - policy updates, research, and industry news",
                "articleCount": nvca_count,
                "feedType": "rss"
            },
            {
                "id": "pitchbook",
                "name": "Pitchbook",
                "url": "https://pitchbook.com/news",
                "description": "Private market data and research - VC, PE, and M&A news and analysis",
                "articleCount": pitchbook_count,
                "feedType": "scrape"
            }
        ],
        "totalArticles": len(items)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    is_dev = os.environ.get("NODE_ENV") == "development"
    print(f"=== FeedForge Flask Server ===")
    print(f"Starting on http://0.0.0.0:{port}")
    print(f"ADMIN_KEY configured: {'Yes' if ADMIN_KEY else 'No (dev mode - writes allowed)'}")
    app.run(host="0.0.0.0", port=port, debug=is_dev)
