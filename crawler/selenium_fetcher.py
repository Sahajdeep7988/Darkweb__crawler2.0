from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import os
import random
import platform
import socket
import zipfile
import urllib.request
import shutil
import subprocess
import sys

class SeleniumFetcher:
    def __init__(self):
        self.driver = None
        self.driver_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "drivers")
        if not os.path.exists(self.driver_dir):
            os.makedirs(self.driver_dir)
    
    def init_browser(self):
        """Initialize Firefox browser with Tor proxy settings and security measures"""
        # Check if Tor is running first
        tor_status, tor_error = self._is_tor_running()
        if not tor_status:
            print("\n❌ Tor is not running on port 9050 or is blocked by Windows Firewall.")
            
            if tor_error == "timeout":
                print("🔥 Windows Firewall is likely blocking Tor connections. Try these solutions:")
                print("   1. Run this script as administrator to automatically create targeted firewall rules")
                print("   2. Manually add these specific exceptions to Windows Firewall:")
                print("      - Allow Firefox outbound connections to port 9050 (TCP)")
                print("      - Allow Python outbound connections to port 9050 (TCP)")
                print("   3. Make sure Tor is actually running (Tor Browser or Tor service)")
            elif tor_error == "refused":
                print("🔍 Tor service is not running. Please start Tor:")
                print("   1. Start Tor Browser and keep it running in the background, or")
                print("   2. Use Tor Expert Bundle to run Tor as a service")
            else:
                print("🔥 Windows Firewall may be blocking Tor connections. Try these solutions:")
                print("   1. Make sure Tor service is running: Open Tor Browser or Tor Expert Bundle")
                print("   2. Allow Tor through Windows Firewall:")
                print("      - Open Windows Security > Firewall & Network Protection")
                print("      - Click 'Allow an app through firewall'")
                print("      - Find Tor in the list or add it manually")
                print("   3. Try running this script as administrator\n")
            
            # Attempt to check if Tor is actually running but blocked
            if self._check_tor_process_running():
                print("✅ Tor process is running but connections are blocked by firewall!")
                print("   This confirms the issue is with the firewall, not Tor itself.")
                
            return None
            
        # Use only Firefox with Tor for maximum safety
        driver = self._init_firefox()
        return driver
    
    def _is_tor_running(self):
        """Check if Tor is running on port 9050
        Returns: (is_running, error_type)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Set timeout to 5 seconds
            result = sock.connect_ex(('127.0.0.1', 9050))
            sock.close()
            
            if result == 0:
                # Connection successful
                return True, None
                
            elif result == 10061:  # Connection refused
                # Tor is not running (no process listening on port)
                return False, "refused"
                
            elif result == 10060:  # Connection timed out
                # Could be firewall blocking
                return False, "timeout"
                
            else:
                # Other error
                return False, f"socket_error_{result}"
                
        except socket.timeout:
            # Connection timed out - likely firewall blocking
            return False, "timeout"
        except socket.error as e:
            print(f"🔥 Socket error checking Tor: {e}")
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def _check_tor_process_running(self):
        """Check if Tor process is running even if ports are blocked"""
        try:
            if platform.system() == "Windows":
                # On Windows, check for tor.exe in process list
                result = subprocess.run(["tasklist", "/fi", "imagename eq tor.exe"], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE, 
                                       text=True)
                if "tor.exe" in result.stdout:
                    return True
                    
                # Also check for firefox.exe with Tor in the command line args
                result = subprocess.run(["wmic", "process", "where", "name='firefox.exe'", "get", "CommandLine"], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE, 
                                       text=True)
                if "Tor" in result.stdout:
                    return True
            else:
                # On Linux/macOS use ps command
                result = subprocess.run(["ps", "aux"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True)
                if "tor " in result.stdout:
                    return True
            
            return False
        except Exception as e:
            print(f"⚠️ Could not check for Tor process: {e}")
            return False
    
    def _download_geckodriver(self):
        """Download GeckoDriver manually"""
        try:
            print("📥 Downloading GeckoDriver manually...")
            system = platform.system()
            bits = platform.architecture()[0]
            
            # Use fixed version to avoid GitHub API rate limits
            geckodriver_version = "v0.31.0"
            
            if system == "Windows":
                if bits == "64bit":
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-win64.zip"
                else:
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-win32.zip"
            elif system == "Darwin":  # macOS
                if "arm" in platform.processor().lower():
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-macos-aarch64.tar.gz"
                else:
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-macos.tar.gz"
            else:  # Linux
                if bits == "64bit":
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-linux64.tar.gz"
                else:
                    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-linux32.tar.gz"
            
            # Use a secure connection for downloading
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
            }
            
            zip_path = os.path.join(self.driver_dir, "geckodriver.zip")
            driver_path = os.path.join(self.driver_dir, "geckodriver.exe" if system == "Windows" else "geckodriver")
            
            # Check if we already have the driver
            if os.path.exists(driver_path):
                print(f"✅ Using existing GeckoDriver at {driver_path}")
                return driver_path
            
            # Create a request with secure headers
            print(f"🔗 Downloading from {url}")
            req = urllib.request.Request(url, headers=headers)
            
            try:
                # Download the file with a timeout
                with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, 'wb') as out_file:
                    out_file.write(response.read())
            except urllib.error.URLError as e:
                if isinstance(e.reason, socket.timeout):
                    print("❌ Download timed out - possible firewall issue")
                    print("🔥 Windows Firewall may be blocking the download.")
                    print("   Try manually downloading GeckoDriver from:")
                    print(f"   {url}")
                    print(f"   And place it in: {self.driver_dir}")
                    return None
                elif "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
                    print("❌ SSL certificate verification failed")
                    print("🔥 This could be due to a firewall, proxy, or antivirus intercepting SSL connections")
                    return None
                else:
                    print(f"❌ Download failed: {e}")
                    return None
            except Exception as e:
                print(f"❌ Error downloading: {e}")
                return None
            
            # Extract the file
            try:
                if system == "Windows":
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(self.driver_dir)
                else:
                    import tarfile
                    with tarfile.open(zip_path, "r:gz") as tar:
                        tar.extractall(self.driver_dir)
            except Exception as e:
                print(f"❌ Error extracting: {e}")
                return None
            
            # Make executable on non-Windows systems
            if system != "Windows":
                os.chmod(driver_path, 0o755)
                
            # Clean up zip file
            os.remove(zip_path)
            
            print(f"✅ GeckoDriver downloaded to {driver_path}")
            return driver_path
            
        except Exception as e:
            print(f"❌ Error downloading GeckoDriver: {str(e)}")
            return None
    
    def _init_firefox(self):
        """Initialize Firefox with Tor proxy and maximum security settings"""
        try:
            print("🦊 Initializing Firefox with Tor proxy (enhanced security)...")
            
            options = FirefoxOptions()
            options.headless = True  # Run headless browser (no GUI)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Find Firefox binary location based on OS
            firefox_path = self._find_firefox_path()
            if firefox_path:
                print(f"🦊 Found Firefox at: {firefox_path}")
                options.binary_location = firefox_path
            else:
                print("❌ Firefox not found. Please install Firefox browser.")
                print("🔗 Download from: https://www.mozilla.org/firefox/new/")
                return None
            
            # Setup Tor proxy settings
            options.set_preference('network.proxy.type', 1)
            options.set_preference('network.proxy.socks', '127.0.0.1')
            options.set_preference('network.proxy.socks_port', 9050)
            options.set_preference('network.proxy.socks_remote_dns', True)
            
            # Enhanced Security Settings for Dark Web
            
            # Disable JavaScript (essential for dark web security)
            options.set_preference('javascript.enabled', False)
            
            # Disable WebRTC to prevent IP leaks
            options.set_preference('media.peerconnection.enabled', False)
            options.set_preference('media.navigator.enabled', False)
            options.set_preference('media.peerconnection.turn.disable', True)
            options.set_preference('media.peerconnection.use_document_iceservers', False)
            options.set_preference('media.peerconnection.video.enabled', False)
            options.set_preference('media.peerconnection.identity.timeout', 1)
            
            # Disable WebGL for security
            options.set_preference('webgl.disabled', True)
            
            # Disable cache to prevent data persistence
            options.set_preference('browser.cache.disk.enable', False)
            options.set_preference('browser.cache.memory.enable', False)
            options.set_preference('browser.cache.offline.enable', False)
            options.set_preference('network.cookie.lifetimePolicy', 2)
            options.set_preference('network.cookie.thirdparty.sessionOnly', True)
            
            # Disable Autofill
            options.set_preference('browser.formfill.enable', False)
            options.set_preference('signon.rememberSignons', False)
            
            # Privacy settings
            options.set_preference('places.history.enabled', False)
            options.set_preference('privacy.clearOnShutdown.offlineApps', True)
            options.set_preference('privacy.clearOnShutdown.passwords', True)
            options.set_preference('privacy.clearOnShutdown.siteSettings', True)
            options.set_preference('privacy.sanitize.sanitizeOnShutdown', True)
            
            # User-Agent spoofing for greater anonymity
            options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0')
            
            # Disable Flash and other plugins
            options.set_preference('plugin.state.flash', 0)
            options.set_preference('plugin.state.java', 0)
            
            # Get driver path - AVOID using GeckoDriverManager which hits GitHub API
            driver_path = os.path.join(self.driver_dir, "geckodriver.exe" if platform.system() == "Windows" else "geckodriver")
            
            # If driver doesn't exist, try to download it directly
            if not os.path.exists(driver_path):
                driver_path = self._download_geckodriver()
                
                # If download failed and we're still missing the driver
                if not os.path.exists(driver_path):
                    print("❌ GeckoDriver not found. Please run the fix_drivers.py script first.")
                    print("   Run: python fix_drivers.py")
                    return None
            
            try:
                # Create service with our downloaded driver
                service = FirefoxService(executable_path=driver_path)
                
                driver = webdriver.Firefox(service=service, options=options)
                driver.set_page_load_timeout(120)  # Longer timeout for Tor
                print("✅ Firefox initialized with enhanced security!")
                
                return driver
            except WebDriverException as e:
                if "process unexpectedly closed" in str(e):
                    print("❌ Firefox process was terminated - possible firewall or antivirus interference")
                    print("🔥 Windows Firewall may be blocking Firefox from connecting to Tor")
                    print("   1. Add these specific firewall exceptions (without disabling the whole firewall):")
                    print("     a. Run PowerShell as administrator")
                    print('     b. Run: New-NetFirewallRule -DisplayName "Allow Firefox Tor" -Direction Outbound -Program "' + firefox_path + '" -RemotePort 9050 -Protocol TCP -Action Allow')
                    print('     c. Run: New-NetFirewallRule -DisplayName "Allow Python Tor" -Direction Outbound -Program "' + sys.executable + '" -RemotePort 9050 -Protocol TCP -Action Allow')
                    print("   2. Or create these exceptions manually:")
                    print("     - Windows Security → Firewall & Network Protection → Allow an app through firewall")
                    print("     - Add Firefox and Python, ensuring private networks are checked")
                    print("   3. Try running the script as administrator")
                    return None
                else:
                    print(f"❌ WebDriver error: {e}")
                    return None
            
        except Exception as e:
            print(f"❌ Error initializing Firefox: {str(e)}")
            if "No such file or directory" in str(e) and "geckodriver" in str(e):
                print("🔥 GeckoDriver not found in PATH or could not be downloaded")
                print("   Try running fix_drivers.py manually:")
                print("   1. Run: python fix_drivers.py")
                print(f"   2. It will download and install GeckoDriver to: {self.driver_dir}")
            elif "Permission denied" in str(e):
                print("🔥 Permission denied - try running as administrator")
            return None
    
    def _find_firefox_path(self):
        """Find Firefox installation path based on OS"""
        system = platform.system()
        
        # Common Firefox paths by OS
        if system == "Windows":
            potential_paths = [
                os.path.expandvars("%ProgramFiles%\\Mozilla Firefox\\firefox.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Mozilla Firefox\\firefox.exe"),
                os.path.expandvars("%LocalAppData%\\Mozilla Firefox\\firefox.exe"),
                os.path.expanduser("~\\AppData\\Local\\Mozilla Firefox\\firefox.exe"),
                "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
            ]
        elif system == "Darwin":  # macOS
            potential_paths = [
                "/Applications/Firefox.app/Contents/MacOS/firefox",
                os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS/firefox")
            ]
        else:  # Linux and others
            potential_paths = [
                "/usr/bin/firefox",
                "/usr/local/bin/firefox",
                "/snap/bin/firefox",
                os.path.expanduser("~/.local/bin/firefox")
            ]
            
        # Check each path
        for path in potential_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def fetch_with_scrolling(self, url, timeout=120):
        """Fetch full page content with scrolling to reveal lazy-loaded content"""
        if not self.driver:
            self.driver = self.init_browser()
            
        if not self.driver:
            return {"error": "Failed to initialize Firefox browser. Make sure Tor is running and Firefox is installed.", "url": url}
            
        try:
            print(f"🧅 Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to initially load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Safety check for malicious content (simple check)
            if self._check_for_suspicious_content():
                print(f"⚠️ Warning: Potentially malicious content detected at {url}")
            
            # Scroll down to load any lazy loaded content
            self.scroll_to_bottom(self.driver)
            
            # Click on "Show More" or "Load More" buttons if present
            self.click_show_more_buttons(self.driver)
            
            # Expand any collapsed content
            self.expand_collapsed_content(self.driver)
            
            # Extract page data
            page_data = {
                "url": url,
                "title": self.driver.title,
                "html": self.driver.page_source,
                "text": self.driver.find_element(By.TAG_NAME, "body").text
            }
            
            return page_data
            
        except TimeoutException:
            return {"error": "Timeout while loading page", "url": url}
        except WebDriverException as e:
            if "Reached error page" in str(e) and "about:neterror" in str(e):
                return {"error": "Network error - Tor may be blocked by firewall", "url": url}
            else:
                return {"error": f"WebDriver error: {str(e)}", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}
            
    def _check_for_suspicious_content(self):
        """Simple check for potentially malicious content"""
        try:
            # Check for common dangerous page characteristics
            page_source = self.driver.page_source.lower()
            suspicious_patterns = [
                "download now", "install plugin", "allow notifications",
                "enable javascript", "enable flash", "download extension",
                "install now", "enable java"
            ]
            
            return any(pattern in page_source for pattern in suspicious_patterns)
        except:
            return False
    
    def scroll_to_bottom(self, driver):
        """Scroll to bottom of page incrementally to load lazy content"""
        # Get initial height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down incrementally
        for _ in range(5):  # Adjust the number of scroll attempts as needed
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content to load
            time.sleep(random.uniform(1.0, 2.0))
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # Break if no more content loaded
            if new_height == last_height:
                break
                
            last_height = new_height
    
    def click_show_more_buttons(self, driver):
        """Click on "Show More" or similar buttons"""
        # Common button text patterns that indicate expandable content
        button_patterns = [
            "Show More", "Load More", "View More", "See More", 
            "Show All", "Expand", "More", "Read More"
        ]
        
        # Try to find and click buttons with these texts
        for pattern in button_patterns:
            try:
                # Look for buttons by text
                buttons = driver.find_elements(By.XPATH, 
                    f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]")
                
                # Also look for anchor tags that might be used as buttons
                buttons += driver.find_elements(By.XPATH, 
                    f"//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]")
                
                # Click each button
                for button in buttons[:5]:  # Limit to first 5 to avoid infinite loops
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            time.sleep(random.uniform(1.0, 2.0))
                    except:
                        continue
            except:
                continue
    
    def expand_collapsed_content(self, driver):
        """Expand collapsed/hidden content sections"""
        # Try to find and click elements that might expand hidden content
        try:
            # Common selectors for expandable elements
            selectors = [
                ".expander", ".expandable", ".toggle", ".accordion", 
                "[aria-expanded='false']", "[data-expanded='false']",
                ".collapsed", ".folded"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:10]:  # Limit to first 10
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                time.sleep(0.5)
                        except:
                            continue
                except:
                    continue
        except:
            pass

    def close(self):
        """Close the browser with cleanup"""
        if self.driver:
            # Clear any sensitive data
            try:
                self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            except:
                pass
                
            self.driver.quit()
            self.driver = None


# Global fetcher instance to reuse
_fetcher = None

def fetch_full_content(url, timeout=120):
    """Fetch full content using Firefox with Tor proxy"""
    global _fetcher
    
    try:
        if _fetcher is None:
            _fetcher = SeleniumFetcher()
            
        result = _fetcher.fetch_with_scrolling(url, timeout)
        
        # If there was an error, try to reinitialize the fetcher once
        if "error" in result and _fetcher.driver:
            _fetcher.close()
            _fetcher = SeleniumFetcher()
            result = _fetcher.fetch_with_scrolling(url, timeout)
            
        return result
    except Exception as e:
        # Make sure to clean up in case of any failure
        if _fetcher:
            _fetcher.close()
            _fetcher = None
        return {"error": str(e), "url": url}
