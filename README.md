# Dark Web Crawler - Enhanced Security Research Tool

A secure and ethical dark web crawler developed for cybersecurity research, designed to operate with robust security measures and comprehensive data extraction capabilities.

## 🔒 Project Overview

This advanced dark web crawler was developed for security research and monitoring purposes. It's designed to assist security researchers, analysts, and relevant authorities in safely navigating and extracting data from the dark web for legitimate security and research purposes.

## ⚠️ Ethical Use Statement

This software is intended **ONLY** for:
- Legitimate security research
- Authorized investigations
- Educational purposes
- Cybersecurity monitoring

The developers of this tool do not condone or support any illegal activities. Users are responsible for ensuring their use of this tool complies with all applicable laws and regulations.

## 🔍 Key Features

- **Enhanced Security Operation**: Works with security firewalls enabled
- **Comprehensive Data Extraction**: Extracts visible and hidden content including:
  - Headings, paragraphs, tables, and links
  - Forms and input fields
  - Hidden elements and expandable content
  - Images and media references
- **Dynamic Content Handling**: Scrolls pages and expands collapsed content
- **Stealth Crawling**: Disables JavaScript, WebRTC, and other potential leak vectors
- **Tor Integration**: Safe routing through the Tor network
- **Real-time Data Collection**: Provides incremental data as it's discovered
- **Robust Error Handling**: Graceful recovery from connection issues
- **Windows Firewall Compatible**: Creates targeted exceptions without compromising security

## 🚀 Quick Start (Windows)

### Prerequisites

1. **Tor Browser**: Must be installed and running during crawling
2. **Firefox**: Must be installed (separate from Tor Browser)
3. **Python 3.8+**: With pip for package management

### Installation

```bash
# Clone the repository
git clone https://github.com/Sahajdeep7988/Darkweb__crawler2.0.git
cd Darkweb__crawler2.0

# Install requirements
pip install -r requirements.txt
```

### Running with Enhanced Security

The easiest way to run with proper security settings:

1. Right-click on `SETUP_AND_RUN.bat` and select "Run as administrator"
2. Follow the guided setup process

Alternatively, use the admin management tool for more options:
```
# Run as administrator
manage.bat
```

### Manual Setup and Running

If you prefer to manually set up each component:

1. **Fix Driver Installation**:
   ```
   python fix_drivers.py
   ```

2. **Configure Firewall** (requires admin privileges):
   ```
   python setup_firewall.py
   ```

3. **Start Tor Browser** and keep it running in the background

4. **Run the Crawler**:
   ```
   python run_crawler.py
   ```

## 🎯 Configuring Target Sites

Edit the `configs/sites.json` file to specify which sites to crawl:

```json
{
    "sites": [
        "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/",
        "http://othersiteexample.onion/"
    ],
    "max_pages": 20,
    "depth": 5
}
```

## 🔧 Technical Details

This crawler uses a combination of techniques for safe and effective dark web exploration:

1. **Firefox/Selenium Integration**: Uses a headless Firefox browser with enhanced security settings
2. **BeautifulSoup Integration**: Advanced HTML parsing for comprehensive data extraction
3. **Tor Proxy Routing**: All traffic securely routed through the Tor network
4. **Security Hardening**:
   - Disables JavaScript by default
   - Blocks WebRTC to prevent IP leaks
   - Enhanced privacy settings
   - No cookies or local storage
5. **Firewall Compatibility**: Creates targeted exceptions without disabling security
6. **Comprehensive Data Extraction**: Identifies and extracts content from complex page structures

## 📊 Output Format

Results are saved in JSON format with these files:
- `incremental_[timestamp].json`: Real-time updates as pages are crawled
- `results_[timestamp].json`: Complete results after crawling finishes

The output includes:
- Page title and URL
- Extracted text content (headings, paragraphs)
- Links found (both visible and hidden)
- Form elements
- Hidden content
- Metadata and timestamps

## 🛡️ Security Notes and Troubleshooting

- **Always keep your firewall enabled** for maximum protection
- Ensure Tor Browser is running before starting the crawler
- If you encounter connection issues:
  1. Check if Tor Browser is running
  2. Verify that Windows Firewall isn't blocking connections
  3. Try running the setup script with administrator privileges
  4. Check the logs in `outputs/logs` directory

## 📦 Project Structure

```
darkweb_crawler/
├── configs/               # Configuration files
│   ├── sites.json         # Target sites
│   └── tor_settings.json  # Tor configuration
├── crawler/               # Core crawler modules
│   ├── core.py            # Main crawler logic
│   ├── selenium_fetcher.py # Browser automation
│   └── tor_manager.py     # Tor connectivity
├── drivers/               # Browser drivers
├── outputs/               # Results and logs
│   ├── logs/              # Runtime logs
│   └── scraped_data/      # JSON output files
├── SETUP_AND_RUN.bat      # One-click setup and run
├── manage.bat             # Admin management tool
├── fix_drivers.py         # Driver installation utility
├── setup_firewall.py      # Firewall configuration
└── run_crawler.py         # Main execution script
```

## 💻 Development and Customization

To extend the crawler's functionality:

1. Add custom extraction logic in `crawler/selenium_fetcher.py`
2. Modify crawling parameters in `crawler/core.py`
3. Adjust output formatting in the save methods

## 📝 License

This project is for authorized use only. All rights reserved.

## 📧 Contact

For questions, support, or authorized use inquiries:

- **Developer**: Sahajdeep Singh
- **Email**: sahajdeepsingh404@gmail.com
- **Phone**: +91 7988168548
- **GitHub**: [https://github.com/Sahajdeep7988](https://github.com/Sahajdeep7988)
- **Repository**: [https://github.com/Sahajdeep7988/Darkweb__crawler2.0](https://github.com/Sahajdeep7988/Darkweb__crawler2.0)
