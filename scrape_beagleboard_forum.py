import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin

class BeagleBoardForumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://forum.beagleboard.org"
    
    def scrape_thread(self, thread_url):
        """Extract Q&A from single thread - FIXED SELECTORS"""
        print(f"🕷️  Scraping: {thread_url}")
        
        try:
            resp = self.session.get(thread_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            conversations = []
            
            # FIXED Discourse post selectors (multiple fallbacks)
            post_selectors = [
                'article.topic-post',
                'div[data-post-id]',
                '.topic-post',
                'div.post'
            ]
            
            posts = []
            for selector in post_selectors:
                posts = soup.select(selector)
                if posts:
                    print(f"   → Using selector: {selector} ({len(posts)} posts)")
                    break
            
            for post in posts[:15]:  # Max 15 posts per thread
                # FIXED content extraction
                content_selectors = ['.cooked', '[data-post-id] .post-body', '.post-content']
                content_elem = None
                for selector in content_selectors:
                    content_elem = post.select_one(selector)
                    if content_elem:
                        break
                
                content = content_elem.get_text(strip=True)[:3000] if content_elem else ""
                
                # FIXED username extraction
                username_elem = (post.select_one('.username') or 
                               post.select_one('a.mention') or 
                               post.select_one('.author'))
                username = username_elem.get_text().strip()[:30] if username_elem else "Anonymous"
                
                if len(content) > 100:  # Only meaningful posts
                    conv = {
                        "messages": [
                            {"role": "system", "content": "You are a BeagleBoard forum expert."},
                            {"role": "user", "content": f"Forum post: {content}"},
                            {"role": "assistant", "content": f"Answer from forum user {username}"}
                        ]
                    }
                    conversations.append(conv)
            
            print(f"   → Extracted {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            print(f"   → ERROR: {e}")
            return []
    
    def scrape_category(self, category_url, max_threads=5):  # Reduced for testing
        """Scrape multiple threads from category"""
        print(f"📂 Category: {category_url}")
        
        try:
            resp = self.session.get(category_url, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # FIXED thread link selectors
            thread_selectors = [
                'a.raw-topic-link',
                'a.title',
                '.topic-list-item a[href*="/t/"]'
            ]
            
            threads = []
            for selector in thread_selectors:
                threads = soup.select(selector)
                if threads:
                    print(f"   → Found {len(threads)} threads using: {selector}")
                    break
            
            threads = threads[:max_threads]
            all_convos = []
            
            for i, thread_link in enumerate(threads):
                thread_url = urljoin(self.base_url, thread_link.get('href', ''))
                if '/t/' in thread_url:
                    convos = self.scrape_thread(thread_url)
                    all_convos.extend(convos)
                    print(f"   → Thread {i+1}/{len(threads)}: {len(convos)} convos")
                    time.sleep(2)  # Respectful rate limit
            
            return all_convos
            
        except Exception as e:
            print(f"   → Category ERROR: {e}")
            return []

# TARGET CATEGORIES (High-value BeagleBoard threads)
CATEGORIES = [
    "https://forum.beagleboard.org/c/beaglebone/7",           # BeagleBone
    "https://forum.beagleboard.org/c/general/8",              # General
    "https://forum.beagleboard.org/t/beaglemind/40806",       # BeagleMind
]

# Run scraper
print("🚀 BeagleBoard Forum Scraper Starting...")
scraper = BeagleBoardForumScraper()
forum_data = []

for category in CATEGORIES:
    convos = scraper.scrape_category(category, max_threads=3)  # Test with 3 threads
    forum_data.extend(convos)
    print(f"✅ Got {len(convos)} conversations from {category}")

# Save forum dataset
os.makedirs("data", exist_ok=True)
with open("data/forum_conversations.jsonl", "w", encoding="utf-8") as f:
    for convo in forum_data:
        f.write(json.dumps(convo, ensure_ascii=False) + "\n")

print(f"\n🎉 TOTAL: {len(forum_data)} forum conversations saved!")
print(f"📁 File: data/forum_conversations.jsonl")
print("Next: Modify convert_fayez_format.py for forum data")
