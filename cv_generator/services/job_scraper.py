import sys
import requests
from bs4 import BeautifulSoup


def scrape_job(url: str) -> str:
    """Scrape job posting from URL"""
    try:
        print(f"Scraping job posting from: {url}")
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        print(f"Successfully scraped {len(text)} characters")
        return text

    except Exception as e:
        print(f"Error scraping job posting: {e}")
        sys.exit(1)
