# Dark Web Crawler - Security Research Tool

A secure and ethical dark web crawler developed for cybersecurity research, designed to operate with enhanced security measures and firewall protection enabled.

## 🔒 Project Overview

This tool was developed for the Chandigarh Police and Infosys Cybersecurity Hackathon as an **ethical security research tool**. It's designed to assist security researchers and law enforcement in monitoring and analyzing dark web content for legitimate security purposes.

## ⚠️ Ethical Use Statement

This software is intended **ONLY** for:
- Legitimate security research
- Law enforcement investigations
- Educational purposes

The developers of this tool do not condone or support any illegal activities. Users are responsible for ensuring their use of this tool complies with all applicable laws and regulations.

## 🔍 Key Features

- **Enhanced Security Operation**: Works with security firewalls enabled
- **Stealth Crawling**: Disables JavaScript, WebRTC, and other potential leak vectors
- **Hidden Content Detection**: Extracts hidden elements and expandable content
- **Real-time Data Extraction**: Provides incremental data as it's discovered
- **Tor Integration**: Safe routing through the Tor network
- **Comprehensive Data Collection**: Extracts headings, paragraphs, tables, forms, and more

## 🚀 Quick Start (Windows)

### Prerequisites

1. **Tor Browser**: Must be installed and running during crawling
2. **Firefox**: Must be installed (separate from Tor Browser)
3. **Python 3.8+**: With pip for package management

### Installation

```bash
# Clone the repository (private access only)
git clone https://github.com/YOUR_USERNAME/darkweb_crawler.git
cd darkweb_crawler

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

## 🔧 Technical Details

This crawler uses a combination of techniques to safely explore the dark web:

1. **Firefox/Selenium**: Uses a headless Firefox browser with enhanced security
2. **Tor Proxy**: Routes all traffic through the Tor network
3. **Content Extraction**: Employs BeautifulSoup for comprehensive HTML parsing
4. **Firewall Compatibility**: Creates targeted exceptions without disabling security
5. **Security Hardening**: Disables high-risk browser features

## 📊 Output Format

Results are saved in JSON format with these files:
- `incremental_[timestamp].json`: Real-time updates as pages are crawled
- `results_[timestamp].json`: Complete results after crawling finishes
- `results_[timestamp]_summary.json`: Statistical overview of findings

## 🛡️ Security Notes

- Always keep your firewall enabled for maximum protection
- The crawler uses targeted exceptions rather than disabling security
- JavaScript is disabled to prevent malicious code execution
- For maximum security, use on a dedicated machine or virtual machine

## 📝 License

This project is for authorized use only and is not licensed for public distribution.

## 📧 Contact

For authorized use inquiries, contact: [Contect no:- +91 7988168548   ,   Email:-sahajdeepsingh404@gmail.com] 
