#!/usr/bin/env python3
"""
Dark Web Crawler Admin Panel
----------------------------
Command-line admin interface for managing the dark web crawler.
"""

import argparse
import json
import os
import sys
import csv
from datetime import datetime
from crawler.core import DarkWebCrawler
from crawler.keywords import KeywordDetector
from crawler.classifier import CategoryClassifier

def setup_config():
    """Set up configuration file if not exists"""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "crawler_config.json")
    if not os.path.exists(config_path):
        default_config = {
            "start_urls": [],
            "max_pages": 50,
            "depth": 3,
            "scan_frequency": 5,
            "rotation_threshold": 10,
            "use_keywords": True,
            "use_classification": True,
            "keywords_file": os.path.join(config_dir, "keywords.csv"),
            "custom_categories_file": os.path.join(config_dir, "categories.json")
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        
        print(f"✅ Created default configuration at {config_path}")
    
    # Make sure the keywords directory exists
    keywords_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    os.makedirs(keywords_dir, exist_ok=True)
    
    return config_path

def load_config(config_path):
    """Load configuration from file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"⚠️ Error loading configuration: {str(e)}")
        print("Using default configuration...")
        return {}

def save_config(config, config_path):
    """Save configuration to file"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"✅ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"⚠️ Error saving configuration: {str(e)}")
        return False

def import_seed_urls(file_path, config, config_path):
    """Import seed URLs from a CSV or text file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    urls = []
    
    # Try CSV format first
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.lower().endswith('.csv'):
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        url = row[0].strip()
                        if url.startswith('http') and '.onion' in url:
                            urls.append(url)
            else:
                # Try as plain text file with one URL per line
                for line in f:
                    url = line.strip()
                    if url and url.startswith('http') and '.onion' in url:
                        urls.append(url)
    except Exception as e:
        print(f"⚠️ Error reading seed file: {str(e)}")
        return False
    
    if not urls:
        print("❌ No valid .onion URLs found in file")
        return False
    
    # Add URLs to config
    if 'start_urls' not in config:
        config['start_urls'] = []
    
    # Add new URLs without duplicates
    existing_urls = set(config['start_urls'])
    new_urls = [url for url in urls if url not in existing_urls]
    config['start_urls'].extend(new_urls)
    
    # Save updated config
    save_config(config, config_path)
    
    print(f"✅ Imported {len(new_urls)} new URLs (skipped {len(urls) - len(new_urls)} duplicates)")
    return True

def import_keywords(file_path, config):
    """Import keywords from a CSV file"""
    if not os.path.exists(file_path):
        print(f"❌ Keyword file not found: {file_path}")
        return False
    
    # Update config to use this keywords file
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    keywords_path = os.path.join(config_dir, "keywords.csv")
    
    # Copy file to the keywords directory
    try:
        import shutil
        shutil.copy2(file_path, keywords_path)
        print(f"✅ Copied keywords file to {keywords_path}")
        
        # Update config
        config['keywords_file'] = keywords_path
        config['use_keywords'] = True
        
        # Test loading keywords
        detector = KeywordDetector(keywords_path)
        categories = detector.get_categories()
        
        print(f"✅ Successfully loaded {len(categories)} keyword categories")
        return True
    except Exception as e:
        print(f"⚠️ Error importing keywords: {str(e)}")
        return False

def toggle_category(category, enabled, config, config_path):
    """Enable or disable a category"""
    # Get current category settings
    if 'enabled_categories' not in config:
        # Initialize with all categories enabled
        classifier = CategoryClassifier()
        all_categories = classifier.get_category_list()
        config['enabled_categories'] = list(all_categories.keys())
    
    if enabled:
        if category not in config['enabled_categories']:
            config['enabled_categories'].append(category)
            print(f"✅ Enabled category: {category}")
    else:
        if category in config['enabled_categories']:
            config['enabled_categories'].remove(category)
            print(f"✅ Disabled category: {category}")
    
    # Save updated config
    save_config(config, config_path)
    return True

def set_scan_frequency(seconds, config, config_path):
    """Set scan frequency (delay between requests)"""
    try:
        seconds = float(seconds)
        if seconds <= 0:
            print("❌ Scan frequency must be a positive number")
            return False
        
        config['scan_frequency'] = seconds
        save_config(config, config_path)
        print(f"✅ Set scan frequency to {seconds} seconds")
        return True
    except ValueError:
        print("❌ Invalid value for scan frequency")
        return False

def set_depth(depth, config, config_path):
    """Set crawl depth"""
    try:
        depth = int(depth)
        if depth <= 0:
            print("❌ Depth must be a positive integer")
            return False
        
        config['depth'] = depth
        save_config(config, config_path)
        print(f"✅ Set crawl depth to {depth}")
        return True
    except ValueError:
        print("❌ Invalid value for depth")
        return False

def set_rotation_threshold(threshold, config, config_path):
    """Set Tor identity rotation threshold (requests)"""
    try:
        threshold = int(threshold)
        if threshold <= 0:
            print("❌ Rotation threshold must be a positive integer")
            return False
        
        config['rotation_threshold'] = threshold
        save_config(config, config_path)
        print(f"✅ Set Tor identity rotation threshold to {threshold} requests")
        return True
    except ValueError:
        print("❌ Invalid value for rotation threshold")
        return False

def list_categories(config):
    """List available categories and their status"""
    crawler = DarkWebCrawler(config)
    categories = crawler.get_categories()
    
    print("\n📋 Available Categories:")
    print("=" * 50)
    for category, data in categories.items():
        status = "✅ Enabled" if data["enabled"] else "❌ Disabled"
        severity = data["severity"]
        print(f"{category} (Severity: {severity}) - {status}")
    print("=" * 50)

def export_results(output_path):
    """Export crawling results to a CSV file"""
    # Find the most recent results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "scraped_data")
    if not os.path.exists(output_dir):
        print("❌ No output directory found")
        return False
    
    result_files = [f for f in os.listdir(output_dir) if f.startswith("results_") and f.endswith(".json")]
    if not result_files:
        print("❌ No results found to export")
        return False
    
    # Sort by timestamp (newest first)
    result_files.sort(reverse=True)
    latest_file = os.path.join(output_dir, result_files[0])
    
    try:
        # Load the results
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Determine output file
        if not output_path:
            output_path = os.path.join(output_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        # Export to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["URL", "Title", "Timestamp", "Categories", "Severity", "Content"])
            
            # Write rows
            for result in results:
                url = result.get("url", "")
                title = result.get("title", "")
                timestamp = result.get("timestamp", "")
                
                # Get classification info
                categories = []
                severity = 0
                if "classification" in result:
                    for category, data in result["classification"].items():
                        categories.append(category)
                        severity = max(severity, data.get("severity", 0))
                
                # Combine text for content column
                content = ""
                if "headings" in result:
                    content += " ".join(result["headings"])
                if "paragraphs" in result:
                    content += " ".join(result["paragraphs"])
                
                writer.writerow([
                    url,
                    title,
                    timestamp,
                    "|".join(categories),
                    severity,
                    content[:1000]  # Limit content length
                ])
        
        print(f"✅ Exported {len(results)} results to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error exporting results: {str(e)}")
        return False

def export_alerts(output_path):
    """Export alerts to a CSV file"""
    # Find the most recent alerts
    alerts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "alerts")
    if not os.path.exists(alerts_dir):
        print("❌ No alerts directory found")
        return False
    
    alert_files = [f for f in os.listdir(alerts_dir) if f.endswith(".json")]
    if not alert_files:
        print("❌ No alerts found to export")
        return False
    
    # Sort by timestamp (newest first)
    alert_files.sort(reverse=True)
    latest_file = os.path.join(alerts_dir, alert_files[0])
    
    try:
        # Load the alerts
        with open(latest_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        
        # Determine output file
        if not output_path:
            output_path = os.path.join(alerts_dir, f"alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        # Export to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["URL", "Category", "Severity", "Timestamp", "Snippet"])
            
            # Write rows
            for alert in alerts:
                writer.writerow([
                    alert.get("url", ""),
                    alert.get("category", ""),
                    alert.get("severity", 0),
                    alert.get("timestamp", ""),
                    alert.get("snippet", "")
                ])
        
        print(f"✅ Exported {len(alerts)} alerts to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error exporting alerts: {str(e)}")
        return False

def start_crawl(config):
    """Start crawling with the current configuration"""
    if not config.get("start_urls"):
        print("❌ No start URLs configured. Use --import-seeds to add URLs first.")
        return False
    
    print("\n🕸️ Starting Dark Web Crawler")
    print("=" * 50)
    print(f"📌 Target URLs: {len(config.get('start_urls', []))} sites")
    print(f"🌳 Crawl Depth: {config.get('depth', 1)}")
    print(f"⏱️ Scan Frequency: {config.get('scan_frequency', 5)} seconds")
    print(f"🔄 Tor Rotation: Every {config.get('rotation_threshold', 10)} requests")
    print("=" * 50)
    
    # Create crawler instance with config
    crawler = DarkWebCrawler(config)
    
    # Start crawling
    try:
        results = crawler.crawl(
            start_urls=config.get("start_urls"),
            max_pages=config.get("max_pages", 50),
            depth=config.get("depth", 1)
        )
        
        if results:
            # Save results
            output_file = crawler.save_results(results)
            print(f"\n✅ Crawl completed! Results saved to {output_file}")
            return True
        else:
            print("\n⚠️ Crawl did not return any results.")
            return False
    except KeyboardInterrupt:
        print("\n⚠️ Crawl interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error during crawl: {str(e)}")
        return False

def main():
    """Main function to handle command-line arguments"""
    # Set up configuration
    config_path = setup_config()
    config = load_config(config_path)
    
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Dark Web Crawler Admin Panel')
    
    # Add arguments
    parser.add_argument('--import-seeds', metavar='FILE', help='Import seed URLs from CSV or text file')
    parser.add_argument('--import-keywords', metavar='FILE', help='Import keywords from CSV file')
    parser.add_argument('--enable-category', metavar='CATEGORY', help='Enable a specific category')
    parser.add_argument('--disable-category', metavar='CATEGORY', help='Disable a specific category')
    parser.add_argument('--list-categories', action='store_true', help='List all available categories')
    parser.add_argument('--export-results', metavar='FILE', nargs='?', const='auto', help='Export results to CSV file')
    parser.add_argument('--export-alerts', metavar='FILE', nargs='?', const='auto', help='Export alerts to CSV file')
    parser.add_argument('--set-scan-frequency', metavar='SECONDS', type=float, help='Set delay between requests')
    parser.add_argument('--set-depth', metavar='DEPTH', type=int, help='Set crawl depth')
    parser.add_argument('--set-rotation', metavar='REQUESTS', type=int, help='Set Tor identity rotation threshold')
    parser.add_argument('--start-crawl', action='store_true', help='Start crawling with current configuration')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Process arguments
    if args.import_seeds:
        import_seed_urls(args.import_seeds, config, config_path)
    
    if args.import_keywords:
        import_keywords(args.import_keywords, config)
    
    if args.enable_category:
        toggle_category(args.enable_category, True, config, config_path)
    
    if args.disable_category:
        toggle_category(args.disable_category, False, config, config_path)
    
    if args.list_categories:
        list_categories(config)
    
    if args.export_results is not None:
        export_results(None if args.export_results == 'auto' else args.export_results)
    
    if args.export_alerts is not None:
        export_alerts(None if args.export_alerts == 'auto' else args.export_alerts)
    
    if args.set_scan_frequency is not None:
        set_scan_frequency(args.set_scan_frequency, config, config_path)
    
    if args.set_depth is not None:
        set_depth(args.set_depth, config, config_path)
    
    if args.set_rotation is not None:
        set_rotation_threshold(args.set_rotation, config, config_path)
    
    if args.start_crawl:
        start_crawl(config)

if __name__ == "__main__":
    main() 