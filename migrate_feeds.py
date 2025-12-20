import os
import json
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
FEEDS_DIR = "feeds"

os.makedirs(FEEDS_DIR, exist_ok=True)

def migrate_feeds():
    if not DATABASE_URL:
        print("DATABASE_URL not set")
        return
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT f.id, f.title, f.source_url, f.categories, 
               a.title as article_title, a.excerpt, a.url, a.image_url, a.published_at
        FROM feeds f
        LEFT JOIN articles a ON f.id = a.feed_id
        ORDER BY f.id, a.published_at DESC
    """)
    
    rows = cur.fetchall()
    
    feeds_by_category = {}
    
    for row in rows:
        feed_id, feed_title, source_url, categories, article_title, excerpt, url, image_url, published_at = row
        
        if not categories:
            categories = ["general"]
        
        for cat in categories:
            cat = cat.lower().strip()
            if cat not in feeds_by_category:
                feeds_by_category[cat] = []
            
            if article_title and url:
                date_str = ""
                if published_at:
                    try:
                        date_str = published_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    except:
                        date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
                else:
                    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
                
                existing_urls = [item["url"] for item in feeds_by_category[cat]]
                if url not in existing_urls:
                    feeds_by_category[cat].append({
                        "title": article_title[:200] if article_title else "Untitled",
                        "description": (excerpt[:500] if excerpt else "")[:500],
                        "date": date_str,
                        "url": url,
                        "image": image_url or ""
                    })
    
    for cat, items in feeds_by_category.items():
        items = items[:100]
        feed_file = os.path.join(FEEDS_DIR, f"{cat}.json")
        with open(feed_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(items)} items to {feed_file}")
    
    cur.close()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate_feeds()
