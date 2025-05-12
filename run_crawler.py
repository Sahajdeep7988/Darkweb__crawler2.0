import json
import os
import platform
import sys
import ctypes
from crawler.core import DarkWebCrawler
from crawler.utils import setup_logging
from datetime import datetime

def ensure_output_dirs():
    """Ensure output directories exist"""
    dirs = [
        'outputs/scraped_data',
        'outputs/logs'
    ]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

def is_admin():
    """Check if the script is running with admin/root privileges"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # For Unix systems, check if effective user ID is 0 (root)
            return os.geteuid() == 0
    except:
        return False

def check_firewall_status():
    """Check if Windows Firewall is enabled"""
    if platform.system() != 'Windows':
        return None  # Not applicable for non-Windows systems
        
    try:
        # Use PowerShell to check firewall status
        import subprocess
        result = subprocess.run(
            ["powershell", "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"],
            capture_output=True,
            text=True
        )
        
        # Check if at least one firewall profile is enabled
        if "True" in result.stdout:
            return True
        return False
    except:
        return None  # Unable to determine

def create_firewall_exceptions():
    """Create targeted firewall exceptions for Tor connectivity (Windows only)"""
    if platform.system() != 'Windows':
        return False  # Not applicable on non-Windows systems
        
    if not is_admin():
        print("\n⚠️ Not running as administrator - cannot create firewall exceptions")
        print("   Consider running as administrator to create targeted firewall rules")
        return False
        
    try:
        import subprocess
        
        # Find Firefox path
        firefox_paths = [
            os.path.expandvars("%ProgramFiles%\\Mozilla Firefox\\firefox.exe"),
            os.path.expandvars("%ProgramFiles(x86)%\\Mozilla Firefox\\firefox.exe"),
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
        ]
        
        firefox_path = None
        for path in firefox_paths:
            if os.path.exists(path):
                firefox_path = path
                break
                
        if not firefox_path:
            print("❌ Could not find Firefox installation to create firewall rule")
            return False
            
        # Python executable path
        python_exe = sys.executable
        
        # Create highly targeted firewall rules (only for port 9050 used by Tor)
        rules = [
            # Allow Firefox to connect to Tor
            f'New-NetFirewallRule -DisplayName "DarkWebCrawler Firefox-Tor" -Direction Outbound -Program "{firefox_path}" -RemotePort 9050 -Protocol TCP -Action Allow',
            
            # Allow Python to connect to Tor
            f'New-NetFirewallRule -DisplayName "DarkWebCrawler Python-Tor" -Direction Outbound -Program "{python_exe}" -RemotePort 9050 -Protocol TCP -Action Allow'
        ]
        
        print("\n🔧 Creating targeted firewall exceptions for Tor connections...")
        
        for rule in rules:
            try:
                # Use PowerShell to create the rule
                subprocess.run(["powershell", "-Command", rule], 
                               check=True, 
                               capture_output=True)
                print(f"✅ Created firewall rule: {rule.split('-DisplayName')[1].split('-Direction')[0].strip()}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create firewall rule: {e}")
                print(f"   Error output: {e.stderr.decode() if e.stderr else 'Unknown error'}")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Error creating firewall exceptions: {e}")
        return False

def main():
    setup_logging()
    ensure_output_dirs()
    
    # Show banner
    print("\n" + "=" * 80)
    print(" 🕸️  Dark Web Crawler - Enhanced Security Version 🕸️ ")
    print("=" * 80)
    
    # Check if running as admin (recommended for firewall access)
    if not is_admin():
        print("\n⚠️  WARNING: Not running with administrator privileges")
        print("   Some features may not work correctly, especially with firewall issues")
        print("   Consider running this script as administrator for better compatibility\n")
    
    # Check firewall status on Windows and try to create exceptions if needed
    firewall_status = check_firewall_status()
    if firewall_status:
        print("\n⚠️  FIREWALL NOTICE: Windows Firewall is enabled")
        
        # Try to create firewall exceptions if running as admin
        if is_admin():
            if create_firewall_exceptions():
                print("✅ Created targeted firewall exceptions for Tor connectivity")
                print("   The crawler should now be able to connect to Tor while keeping firewall protection")
            else:
                print("❌ Failed to create automatic firewall exceptions")
                print("   You may need to manually add exceptions for Firefox and Python in Windows Firewall")
        else:
            print("   This may block Tor connections or driver downloads")
            print("   Run this script as administrator to automatically create targeted exceptions")
            print("   Or manually add Firefox and Python to the Windows Firewall exceptions\n")
    
    # Load configuration
    try:
        with open('configs/sites.json') as f:
            sites_config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: configs/sites.json not found")
        print("   Please create this file with your target sites")
        return
    except json.JSONDecodeError:
        print("❌ Error: configs/sites.json is not valid JSON")
        return
    
    print("🚀 Starting Dark Web Crawler")
    print(f"📌 Target URLs: {len(sites_config['sites'])}")
    print(f"🔍 Max Pages: {sites_config.get('max_pages', 20)}")
    print(f"🌳 Crawl Depth: {sites_config.get('depth', 1)}")
    print("🧠 Enhanced Mode: Using Firefox with Tor for deep content extraction")
    print("🔒 Security: JavaScript disabled, WebRTC blocked, enhanced privacy settings")
    
    # Double-check if any URLs were provided
    if not sites_config['sites']:
        print("❌ Error: No target URLs specified in configs/sites.json")
        return
    
    crawler = DarkWebCrawler()
    try:
        print(f"\n💾 REAL-TIME DATA: Check the incremental file for results as they're found:")
        print(f"   {crawler.incremental_file}")
        print("   This file updates after each successful page crawl\n")
        
        results = crawler.crawl(
            start_urls=sites_config['sites'],
            max_pages=sites_config.get('max_pages', 20),
            depth=sites_config.get('depth', 1)
        )
        
        # Check if we got any results
        if not results:
            print("\n❌ No results obtained. This could be due to:")
            print("   - Tor not running or blocked by firewall")
            print("   - Firefox not installed or blocked")
            print("   - Issues with GeckoDriver")
            print("   - Network connectivity problems")
            print("   Please check the error messages above for specific issues.")
            return
            
        # Save results
        output_file = crawler.save_results(results)
        
        # Generate statistics
        stats = {
            'total_pages_crawled': len(results),
            'total_links_found': sum(len(page.get('links', [])) for page in results),
            'content_size_bytes': sum(len(str(page)) for page in results),
            'hidden_elements_found': sum(len(page.get('hidden_content', [])) for page in results),
            'timestamp': crawler.timestamp
        }
        
        # Print statistics
        print("\n📊 Crawl Statistics:")
        print(f"✅ Total pages crawled: {stats['total_pages_crawled']}")
        print(f"🔗 Total links found: {stats['total_links_found']}")
        print(f"👻 Hidden elements found: {stats['hidden_elements_found']}")
        print(f"💾 Content size: {stats['content_size_bytes'] / (1024*1024):.2f} MB")
        print(f"\n✅ Crawl completed! Results saved to {output_file}")
        print(f"   Incremental results available at {crawler.incremental_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Crawl interrupted by user")
        print(f"   Partial results are still available in the incremental file: {crawler.incremental_file}")
    except Exception as e:
        print(f"\n❌ Error during crawl: {str(e)}")
        print("   Please check the error messages above for specific issues.")
        print(f"   Check for partial results in: {crawler.incremental_file}")

if __name__ == "__main__":
    main()    



