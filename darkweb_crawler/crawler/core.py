import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import urljoin, urlparse
from .tor_manager import TorManager

class DarkWebCrawler:
    def __init__(self):
        self.tor = TorManager()
        self.visited = set()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
            "TorBrowser/11.0.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
        ]
        self.session = self._create_session()
        
    def _create_session(self):
        """Create a fresh requests session with Tor proxy"""
        session = requests.Session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        return session

    def crawl(self, start_urls, max_pages=20, depth=2):
        """Main crawling method"""
        queue = [(url, 0) for url in start_urls]
        results = []
        page_count = 0
        
        while queue and page_count < max_pages:
            url, current_depth = queue.pop(0)
            
            if url in self.visited:
                continue
                
            try:
                time.sleep(random.uniform(3, 7))  # Random delay
                
                print(f"🌐 Crawling: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    self.visited.add(url)
                    page_count += 1
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_data = self._extract_data(url, soup)
                    results.append(page_data)
                    print(f"✅ {page_count}/{max_pages} - {url}")
                    
                    if current_depth < depth:
                        new_links = self._find_links(url, soup)
                        queue.extend((link, current_depth + 1) for link in new_links)
                        
                elif response.status_code in [403, 429]:
                    print(f"🚫 Blocked ({response.status_code}), rotating circuit...")
                    self.tor.rotate_circuit()
                    self.session = self._create_session()
                    queue.append((url, current_depth))
                    
            except Exception as e:
                print(f"❌ Error on {url}: {str(e)}")
                
        return results

    def _extract_data(self, url, soup):
        """Extract page data"""
        title = soup.title.string.strip() if soup.title else "No title"
        return {
            'url': url,
            'title': title,
            'content': ' '.join(p.get_text() for p in soup.find_all('p'))[:5000],
            'timestamp': time.time()
        }

    def _find_links(self, base_url, soup):
        """Find all .onion links on page"""
        new_links = set()
        for link in soup.find_all('a', href=True):
            try:
                full_url = urljoin(base_url, link['href'])
                if full_url.endswith('.onion'):
                    new_links.add(full_url)
            except:
                continue
        return list(new_links)

    def save_results(self, results, filename):
        """Save results to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)