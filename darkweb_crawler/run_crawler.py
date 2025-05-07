import json
from crawler.core import DarkWebCrawler
from crawler.utils import setup_logging
from datetime import datetime

def main():
    setup_logging()
    
    # Load configuration
    with open('configs/sites.json') as f:
        sites_config = json.load(f)
    
    print("🚀 Starting Dark Web Crawler")
    print(f"📌 Target URLs: {len(sites_config['sites'])}")
    
    crawler = DarkWebCrawler()
    results = crawler.crawl(
        start_urls=sites_config['sites'],
        max_pages=sites_config.get('max_pages', 20),
        depth=sites_config.get('depth', 1)
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/scraped_data/results_{timestamp}.json"
    crawler.save_results(results, output_file)
    
    print(f"✅ Crawl completed! Results saved to {output_file}")
    print(f"📊 Total pages crawled: {len(results)}")

if __name__ == "__main__":
    main()    



