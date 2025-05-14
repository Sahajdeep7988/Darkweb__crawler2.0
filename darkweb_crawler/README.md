# 🕸️ Dark Web Crawler

An enhanced dark web crawler designed for security research, with robust features for content analysis, keyword detection, and alerting.

## 📋 Features

- **Recursive Onion crawler** with depth & visited tracking
- **Keyword detection** from CSV files with NLP/fuzzy matching
- **Category classification** for various illicit content types (Drugs, Weapons, Fake IDs, etc.)
- **Real-time alert logging** with URL, snippet, timestamp, and category
- **Tor identity rotation** after configurable number of requests
- **Admin panel** with CSV import/export and configuration control
- **Smart use of Selenium + BeautifulSoup** for JS-heavy sites
- **Login/CAPTCHA detection** with graceful handling

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Tor Browser** (running in the background) or Tor service
- **Firefox** (for Selenium operation)

### Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Tor is running (Start Tor Browser or run Tor service)
4. Run the crawler:
   ```
   python run_crawler.py
   ```

## ⚙️ Configuration

The crawler uses configuration files in the `configs` directory:

- `crawler_config.json` - Main configuration
- `sites.json` - Seed URLs (can be imported via admin panel)
- `keywords.csv` - Keywords for detection
- `tor_settings.json` - Tor connection settings

## 🛠️ Admin Panel

Use the admin panel to control crawling, import/export data, and toggle categories:

```
python admin.py --help
```

### Common Operations

- **Import seed URLs**: `python admin.py --import-seeds urls.csv`
- **Import keywords**: `python admin.py --import-keywords keywords.csv`
- **Toggle categories**: `python admin.py --enable-category Weapons` or `--disable-category Weapons`
- **List categories**: `python admin.py --list-categories`
- **Set crawl depth**: `python admin.py --set-depth 3`
- **Set scan frequency**: `python admin.py --set-scan-frequency 5`
- **Set rotation threshold**: `python admin.py --set-rotation 10`
- **Export results**: `python admin.py --export-results results.csv`
- **Export alerts**: `python admin.py --export-alerts alerts.csv`
- **Start crawling**: `python admin.py --start-crawl`

## 🧩 Core Components

- **DarkWebCrawler** (`crawler/core.py`) - The main crawler logic
- **KeywordDetector** (`crawler/keywords.py`) - Handles keyword detection
- **CategoryClassifier** (`crawler/classifier.py`) - Classifies content into categories
- **AlertLogger** (`crawler/alerting.py`) - Logs alerts for suspicious content
- **TorManager** (`crawler/tor_manager.py`) - Manages Tor connectivity
- **SeleniumFetcher** (`crawler/selenium_fetcher.py`) - Handles browser automation

## 📂 Output Structure

- **Crawled data**: `outputs/scraped_data/results_TIMESTAMP.json`
- **Incremental data**: `outputs/scraped_data/incremental_TIMESTAMP.json`
- **Alerts**: `outputs/alerts/alerts_DATE.json`
- **Logs**: `outputs/logs/crawler_TIMESTAMP.log`

## 🔐 Security Notes

- This tool is for **security research only**
- Always run behind Tor for anonymity
- Firewall exceptions may be required for Tor connectivity
- Use caution when crawling .onion sites

## 📚 Advanced Usage

### Custom Categories

Create a `categories.json` file in the `configs` directory with custom categories:

```json
{
  "Custom_Category": {
    "severity": 3,
    "indicators": [
      "\\b(?:keyword1|keyword2|keyword3)\\b",
      "\\b(?:pattern1|pattern2)\\b"
    ]
  }
}
```

### Keyword CSV Format

Keywords CSV files should be in one of these formats:

1. Simple format:
   ```
   keyword,category
   cocaine,Drugs
   gun,Weapons
   ```

2. Category columns format:
   ```
   Drugs,Weapons,Fake_IDs
   cocaine,gun,passport
   heroin,rifle,license
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
