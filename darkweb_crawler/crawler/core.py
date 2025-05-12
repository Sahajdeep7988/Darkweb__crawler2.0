import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import urljoin, urlparse
from .tor_manager import TorManager
from .selenium_fetcher import fetch_full_content
import os
from datetime import datetime

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
        # Create the output directory if it doesn't exist
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "scraped_data")
        os.makedirs(self.output_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = os.path.join(self.output_dir, f"results_{self.timestamp}.json")
        self.incremental_file = os.path.join(self.output_dir, f"incremental_{self.timestamp}.json")
        
    def _create_session(self):
        """Create a fresh requests session with Tor proxy"""
        session = requests.Session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        return session

    def _save_incremental_result(self, page_data):
        """Save incremental result after each successful page crawl"""
        try:
            # First, load any existing data 
            if os.path.exists(self.incremental_file) and os.path.getsize(self.incremental_file) > 0:
                with open(self.incremental_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
                
            # Add new page data
            data.append(page_data)
            
            # Save back to file
            with open(self.incremental_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Saved incremental result to {self.incremental_file}")
        except Exception as e:
            print(f"⚠️ Error saving incremental result: {str(e)}")
    
    def crawl(self, start_urls, max_pages=10, depth=1):
        """Crawl dark web sites using Selenium with Tor proxy"""
        if not start_urls:
            return []
        
        results = []
        visited = set()
        to_visit = list(start_urls)
        pages_crawled = 0
        
        # Create initial incremental results file
        with open(self.incremental_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print(f"💾 Created incremental results file: {self.incremental_file}")
        
        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
                
            visited.add(url)
            
            print(f"🌐 Crawling: {url}")
            page_data = fetch_full_content(url)
            pages_crawled += 1
            
            if "error" in page_data:
                print(f"🚫 Error retrieving {url}: {page_data['error']}")
            else:
                print(f"✅ {pages_crawled}/{max_pages} - {url}")
                
                # Process the page to extract links and content
                try:
                    soup = BeautifulSoup(page_data["html"], "html.parser")
                    
                    # Extract links if we're not at max depth
                    if depth > 1:
                        links = []
                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"]
                            if href.startswith("http") and ".onion" in href and href not in visited and href not in to_visit:
                                links.append(href)
                                if depth > 0:  # Only add to crawl queue if we're not at max depth
                                    to_visit.append(href)
                        page_data["links"] = links
                    
                    # Extract more content types for better analysis
                    headings = [h.text for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
                    paragraphs = [p.text for p in soup.find_all("p")]
                    tables = [t.text for t in soup.find_all("table")]
                    forms = [f.text for f in soup.find_all("form")]
                    images = [img.get("src", "") for img in soup.find_all("img")]
                    
                    # Find hidden elements that were made visible
                    hidden_elements = []
                    for elem in soup.find_all(class_=lambda c: c and ("hidden" in c or "collapsed" in c)):
                        hidden_elements.append(elem.text)
                    
                    page_data["headings"] = headings
                    page_data["paragraphs"] = paragraphs
                    page_data["tables"] = tables
                    page_data["forms"] = forms
                    page_data["images"] = images
                    page_data["hidden_content"] = hidden_elements
                    page_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Save incremental result
                    self._save_incremental_result(page_data)
                    
                    results.append(page_data)
                except Exception as e:
                    print(f"⚠️ Error parsing {url}: {str(e)}")
                    page_data["parse_error"] = str(e)
                    results.append(page_data)
            
            # Sleep briefly to avoid overloading Tor circuits
            time.sleep(2)
            
            # Rotate Tor circuit if configured (requires stem)
            try:
                from stem import Signal
                from stem.control import Controller
                
                with Controller.from_port(port=9051) as controller:
                    controller.authenticate()
                    controller.signal(Signal.NEWNYM)
                    print("🔄 Rotated Tor circuit for fresh connection")
            except Exception as e:
                print(f"⚠️ Circuit rotation failed: {str(e)}")
        
        return results
        
    def save_results(self, results, output_file=None):
        """Save crawl results to a JSON file"""
        if not output_file:
            output_file = self.results_file
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print(f"✅ Results saved to {output_file}")
        
        # Also save a summary file with stats
        stats = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_pages": len(results),
            "urls_crawled": [page.get("url", "unknown") for page in results],
            "successful_pages": len([page for page in results if "error" not in page]),
            "error_pages": len([page for page in results if "error" in page])
        }
        
        summary_file = output_file.replace(".json", "_summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
            
        print(f"📊 Summary saved to {summary_file}")
        return output_file

    def _extract_data(self, url, soup, page_data):
        """Extract comprehensive page data"""
        # Base data
        data = {
            'url': url,
            'title': soup.title.string.strip() if soup.title else "No title",
            'timestamp': time.time(),
            'full_text': page_data.get('text', ''),
        }
        
        # Extract all content by section types
        data['headings'] = self._extract_headings(soup)
        data['paragraphs'] = self._extract_paragraphs(soup)
        data['lists'] = self._extract_lists(soup)
        data['tables'] = self._extract_tables(soup)
        data['forms'] = self._extract_forms(soup)
        data['images'] = self._extract_images(url, soup)
        data['links'] = self._extract_links(url, soup)
        data['hidden_content'] = self._extract_hidden_elements(soup)
        
        return data
    
    def _extract_headings(self, soup):
        """Extract all headings"""
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': heading.get_text(strip=True)
                })
        return headings
    
    def _extract_paragraphs(self, soup):
        """Extract all paragraphs"""
        return [p.get_text(strip=True) for p in soup.find_all('p')]
    
    def _extract_lists(self, soup):
        """Extract all lists"""
        lists = []
        for list_elem in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
            lists.append({
                'type': list_elem.name,
                'items': items
            })
        return lists
    
    def _extract_tables(self, soup):
        """Extract all tables"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
    
    def _extract_forms(self, soup):
        """Extract all forms and their fields"""
        forms = []
        for form in soup.find_all('form'):
            fields = []
            for field in form.find_all(['input', 'textarea', 'select']):
                field_data = {
                    'type': field.name,
                    'name': field.get('name', ''),
                    'id': field.get('id', ''),
                }
                if field.name == 'input':
                    field_data['input_type'] = field.get('type', 'text')
                fields.append(field_data)
            
            forms.append({
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'fields': fields
            })
        return forms
    
    def _extract_images(self, base_url, soup):
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                images.append({
                    'src': urljoin(base_url, src),
                    'alt': img.get('alt', ''),
                })
        return images
    
    def _extract_links(self, base_url, soup):
        """Extract all links with text"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href:
                links.append({
                    'url': urljoin(base_url, href),
                    'text': link.get_text(strip=True)
                })
        return links
    
    def _extract_hidden_elements(self, soup):
        """Extract content from hidden elements"""
        hidden_elements = []
        
        # Find elements with display:none or visibility:hidden
        for elem in soup.find_all(style=True):
            style = elem.get('style', '').lower()
            if 'display:none' in style or 'visibility:hidden' in style:
                hidden_elements.append({
                    'tag': elem.name,
                    'content': elem.get_text(strip=True),
                    'html': str(elem)
                })
        
        # Find elements with hidden class
        for elem in soup.find_all(class_=True):
            classes = elem.get('class', [])
            if 'hidden' in classes or 'hide' in classes:
                hidden_elements.append({
                    'tag': elem.name,
                    'content': elem.get_text(strip=True),
                    'html': str(elem)
                })
                
        return hidden_elements

    def _find_all_links(self, base_url, soup):
        """Find all links on page, including .onion and regular URLs"""
        new_links = set()
        for link in soup.find_all('a', href=True):
            try:
                href = link['href'].strip()
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                    
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                # Only add .onion domains or internal pages from the current domain
                if parsed.netloc.endswith('.onion'):
                    new_links.add(full_url)
                elif not parsed.netloc and parsed.path:
                    # Internal link on the same domain
                    new_links.add(full_url)
            except:
                continue
        return list(new_links) 