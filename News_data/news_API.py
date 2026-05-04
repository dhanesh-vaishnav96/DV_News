import os
import json
import re
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()


API_KEY = os.getenv("API_KEY")


from concurrent.futures import ThreadPoolExecutor

def clean_truncated_content(content):
    if not content:
        return ""
    # Strip any trailing "[+XXXX chars]"
    cleaned = re.sub(r'\[\+\d+\s*chars\]', '', content).strip()
    # Strip any trailing "..." if it exists right before the chars
    cleaned = re.sub(r'\.\.\.$', '', cleaned).strip()
    return cleaned


def scrape_full_content(url):
    """Scrape the full article text from the source URL with multiple fallbacks."""
    if not url or not url.startswith("http"):
        return None

    try:
        # Use advanced headers to emulate a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        
        # First attempt
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code != 200:
            # Second attempt with a different User-Agent
            headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
            resp = requests.get(url, headers=headers, timeout=6)

        soup = BeautifulSoup(resp.content, "html.parser")

        # Remove unwanted/distracting tags completely
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "meta", "link"]):
            tag.decompose()

        paragraphs = []
        
        # Strategy 1: Find all specific common container tags for articles
        containers = soup.find_all(["article", "main", "section"])
        for container in containers:
            for p in container.find_all(["p", "div"]):
                text = p.get_text(strip=True)
                if len(text) > 45 and not text.startswith("{") and not text.endswith("}"):
                    if text not in paragraphs:
                        paragraphs.append(text)

        # Strategy 2: Look globally for p and div tags if Strategy 1 wasn't sufficient
        if len(paragraphs) < 3:
            for p in soup.find_all(["p", "div", "span"]):
                # Avoid navigation links or footer text
                parent_classes = "".join(p.get("class", [])) if p.get("class") else ""
                parent_id = p.get("id", "") if p.get("id") else ""
                if any(x in parent_classes.lower() or x in parent_id.lower() for x in ["nav", "footer", "menu", "sidebar"]):
                    continue

                text = p.get_text(strip=True)
                if len(text) > 45 and not text.startswith("{") and not text.endswith("}"):
                    if text not in paragraphs:
                        paragraphs.append(text)

        # Filter duplicates and clean up
        unique_paragraphs = []
        for p in paragraphs:
            if p not in unique_paragraphs:
                if len(p) > 50 and not p.lower().startswith("sign in") and not p.lower().startswith("log in"):
                    unique_paragraphs.append(p)

        full_text = "\n\n".join(unique_paragraphs)
        if len(full_text) > 150:
            return full_text
        return None
    except Exception:
        return None


def fetch_news(query):
    try:
        URL = f"https://newsapi.org/v2/everything?q={query}&apiKey={API_KEY}"
        response = requests.get(URL)
        data = response.json()
    except Exception:
        return {"articles": []}

    articles = data.get("articles", [])[:12]  # Limit to 12 articles max for performance

    def process_article(article):
        content = article.get("content", "") or ""
        description = article.get("description", "") or ""
        url = article.get("url", "")
        
        # Clean truncated suffix
        cleaned_content = clean_truncated_content(content)
        
        # Try scraping if content is truncated
        if "[+" in content and "chars]" in content or len(content) < 300:
            if url:
                full_text = scrape_full_content(url)
                if full_text and len(full_text) > len(cleaned_content):
                    article["content"] = full_text
                    return
        
        # Fallback to combined description and content if scraping fails
        if cleaned_content:
            if description and description not in cleaned_content:
                if cleaned_content.startswith(description[:20]):
                    article["content"] = cleaned_content
                else:
                    article["content"] = f"{description}\n\n{cleaned_content}"
            else:
                article["content"] = cleaned_content
        elif description:
            article["content"] = description

    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.map(process_article, articles)

    data["articles"] = articles
    return data


