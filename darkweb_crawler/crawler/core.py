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
from .keywords import KeywordDetector
from .classifier import CategoryClassifier
from .alerting import AlertLogger

class DarkWebCrawler:
    def __init__(self, config=None):
        # Load configuration if provided
        self.config = config or self._load_default_config()
        
        # Initialize Tor manager
        self.tor = TorManager()
        
        # Set up tracking variables
        self.visited = set()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
            "TorBrowser/11.0.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
        ]
        
        # Create requests session
        self.session = self._create_session()
        
        # Set up output directories
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "scraped_data")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up timestamp and file paths
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = os.path.join(self.output_dir, f"results_{self.timestamp}.json")
        self.incremental_file = os.path.join(self.output_dir, f"incremental_{self.timestamp}.json")
        
        # Initialize advanced features
        self._init_advanced_features()
        
        # Set up circuit rotation settings
        self.requests_since_rotation = 0
        self.rotation_threshold = self.config.get("rotation_threshold", 10)
        
    def _load_default_config(self):
        """Load default configuration"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "crawler_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default configuration if file not found
        return {
            "rotation_threshold": 10,
            "use_keywords": True,
            "use_classification": True,
            "keywords_file": None,
            "custom_categories_file": None,
            "max_retry_attempts": 3,
            "scan_frequency": 5,  # seconds between requests
            "depth": 2
        }
        
    def _init_advanced_features(self):
        """Initialize advanced features based on config"""
        # Set up keyword detection
        self.keyword_detector = None
        if self.config.get("use_keywords", True):
            keywords_file = self.config.get("keywords_file")
            self.keyword_detector = KeywordDetector(keywords_file)
        
        # Set up category classification
        self.classifier = None
        if self.config.get("use_classification", True):
            custom_categories_file = self.config.get("custom_categories_file")
            self.classifier = CategoryClassifier(
                custom_categories_file=custom_categories_file,
                keywords_detector=self.keyword_detector
            )
            
        # Set up alert logging
        self.alert_logger = AlertLogger()
        
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
    
    def crawl(self, start_urls=None, max_pages=10, depth=None):
        """Crawl dark web sites using Selenium with Tor proxy
        
        Args:
            start_urls: List of URLs to start crawling from
            max_pages: Maximum number of pages to crawl
            depth: Maximum depth to crawl (overrides config)
            
        Returns:
            list: Results from crawling
        """
        # Use provided URLs or try to load from config
        if not start_urls:
            start_urls = self.config.get("start_urls", [])
            
        if not start_urls:
            print("❌ No start URLs provided and none found in config")
            return []
        
        # Use provided depth or value from config
        if depth is None:
            depth = self.config.get("depth", 1)
        
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
            
            # Check if circuit rotation is needed
            self.requests_since_rotation += 1
            if self.requests_since_rotation >= self.rotation_threshold:
                self._rotate_identity()
            
            if "error" in page_data:
                print(f"🚫 Error retrieving {url}: {page_data['error']}")
                
                # Handle login/CAPTCHA detection
                if self._is_login_or_captcha_error(page_data["error"]):
                    print("⚠️ Login or CAPTCHA detected - marking URL for possible manual review")
                    page_data["requires_login"] = True
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
                    
                    # Add extracted content to page data
                    page_data["headings"] = headings
                    page_data["paragraphs"] = paragraphs
                    page_data["tables"] = tables
                    page_data["forms"] = forms
                    page_data["images"] = images
                    page_data["hidden_content"] = hidden_elements
                    page_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Combine all text for analysis
                    all_text = "\n".join([
                        " ".join(headings),
                        " ".join(paragraphs),
                        " ".join(tables),
                        " ".join(forms),
                        " ".join(hidden_elements)
                    ])
                    
                    # Run content analysis with classifier
                    if self.classifier:
                        classification = self.classifier.classify_content(
                            all_text, 
                            url=url, 
                            html=page_data["html"]
                        )
                        page_data["classification"] = classification
                        
                        # Create alerts for suspicious content
                        if classification:
                            for category, category_data in classification.items():
                                severity = category_data.get("severity", 1)
                                confidence = category_data.get("confidence", 0)
                                
                                # Only alert if confidence is high enough
                                if confidence >= 70:
                                    # Get a snippet of the matching content
                                    matches = category_data.get("matches", [])
                                    snippet = matches[0].get("context", "") if matches else ""
                                    
                                    self.alert_logger.log_alert(
                                        url=url,
                                        category=category,
                                        severity=severity,
                                        snippet=snippet
                                    )
                    
                    # Save incremental result
                    self._save_incremental_result(page_data)
                    
                    results.append(page_data)
                except Exception as e:
                    print(f"⚠️ Error parsing {url}: {str(e)}")
                    page_data["parse_error"] = str(e)
                    results.append(page_data)
            
            # Sleep briefly to avoid overloading Tor circuits
            scan_frequency = self.config.get("scan_frequency", 2)
            time.sleep(scan_frequency)
        
        return results
    
    def _rotate_identity(self):
        """Rotate Tor identity after N requests"""
        print(f"🔄 Rotating Tor identity after {self.requests_since_rotation} requests...")
        
        # Use Tor Manager to rotate circuit
        if self.tor.rotate_circuit():
            print("✅ Tor identity rotated successfully")
            # Reset the counter
            self.requests_since_rotation = 0
            # Create a fresh session with new headers
            self.session = self._create_session()
        else:
            print("⚠️ Failed to rotate Tor identity, continuing with current identity")
    
    def _is_login_or_captcha_error(self, error_message):
        """Check if error suggests login or CAPTCHA"""
        login_indicators = ["login", "sign in", "captcha", "robot", "human", "verification"]
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in login_indicators)
        
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
        
        # Add alert statistics
        if hasattr(self, "alert_logger"):
            stats["alerts"] = self.alert_logger.get_alert_stats()
        
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
                }
                if field.name == 'input':
                    field_data['input_type'] = field.get('type', '')
                forms.append({
                    'action': form.get('action', ''),
                    'method': form.get('method', 'get'),
                    'fields': fields
                })
        return forms
    
    def _extract_images(self, base_url, soup):
        """Extract all images with src attributes"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if src:
                # Convert to absolute URL if needed
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                images.append({
                    'src': src,
                    'alt': img.get('alt', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                })
        return images
    
    def _extract_links(self, base_url, soup):
        """Extract all links from a page"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href and not href.startswith('#'):
                # Convert to absolute URL if needed
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                links.append({
                    'url': href,
                    'text': a.get_text(strip=True),
                    'is_onion': '.onion' in href
                })
        return links
    
    def _extract_hidden_elements(self, soup):
        """Extract potentially hidden elements"""
        hidden = []
        
        # Find elements with display:none or visibility:hidden
        for elem in soup.find_all(style=True):
            style = elem.get('style', '').lower()
            if 'display:none' in style or 'visibility:hidden' in style:
                hidden.append({
                    'type': elem.name,
                    'text': elem.get_text(strip=True),
                    'html': str(elem)
                })
        
        # Find elements with hidden classes
        hidden_classes = ['hidden', 'hide', 'invisible', 'collapsed']
        for css_class in hidden_classes:
            for elem in soup.find_all(class_=lambda c: c and css_class in c.split()):
                hidden.append({
                    'type': elem.name,
                    'text': elem.get_text(strip=True),
                    'html': str(elem)
                })
                
        return hidden
    
    def _find_all_links(self, base_url, soup):
        """Find all links in various formats"""
        links = set()
        
        # Standard links
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href and not href.startswith('#'):
                # Convert to absolute URL if needed
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                links.add(href)
                
        # Find URLs in text (look for onion domains)
        text = soup.get_text()
        import re
        onion_pattern = r'https?://[a-zA-Z0-9]{16,56}\.onion\b'
        for match in re.finditer(onion_pattern, text):
            links.add(match.group(0))
            
        return list(links)
    
    def import_keywords_from_csv(self, csv_file):
        """Import keywords from CSV file"""
        if self.keyword_detector:
            success = self.keyword_detector.load_keywords(csv_file)
            return success
        return False
    
    def toggle_category(self, category, enabled=True):
        """Enable or disable a category for classification"""
        if not self.classifier:
            return False
            
        if enabled:
            return self.classifier.enable_category(category)
        else:
            return self.classifier.disable_category(category)
    
    def get_categories(self):
        """Get list of available categories with enabled status"""
        if self.classifier:
            return self.classifier.get_category_list()
        return {}
    
    def set_scan_frequency(self, seconds):
        """Set time delay between requests"""
        if isinstance(seconds, (int, float)) and seconds > 0:
            self.config["scan_frequency"] = seconds
            return True
        return False
    
    def set_rotation_threshold(self, requests):
        """Set number of requests before rotating Tor identity"""
        if isinstance(requests, int) and requests > 0:
            self.config["rotation_threshold"] = requests
            self.rotation_threshold = requests
            return True
        return False 