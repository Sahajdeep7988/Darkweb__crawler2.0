import os
import sys
import platform
import ctypes
import subprocess
import glob

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

def find_tor_browser_paths():
    """Find all potential Tor Browser installations"""
    tor_paths = []
    
    if platform.system() == 'Windows':
        # Common installation locations
        potential_locations = [
            os.path.expanduser("~\\Desktop\\Tor Browser"),
            os.path.expanduser("~\\Downloads\\Tor Browser"),
            os.path.expanduser("~\\AppData\\Local\\Tor Browser"),
            os.path.expanduser("~\\AppData\\Roaming\\Tor Browser"),
            "C:\\Program Files\\Tor Browser",
            "C:\\Program Files (x86)\\Tor Browser"
        ]
        
        # Add potential custom installation paths
        for drive in ['C:', 'D:', 'E:', 'F:']:
            potential_locations.extend(glob.glob(f"{drive}\\**\\Tor Browser\\Browser\\firefox.exe", recursive=True))
        
        # Check all potential locations
        for location in potential_locations:
            if os.path.isdir(location):
                firefox_path = os.path.join(location, "Browser", "firefox.exe")
                if os.path.exists(firefox_path):
                    tor_paths.append(firefox_path)
            elif os.path.isfile(location):
                tor_paths.append(location)
                
        # Try registry lookup
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Tor Browser") as key:
                install_location = winreg.QueryValueEx(key, "InstallLocation")[0]
                firefox_path = os.path.join(install_location, "Browser", "firefox.exe")
                if os.path.exists(firefox_path) and firefox_path not in tor_paths:
                    tor_paths.append(firefox_path)
        except:
            pass
            
    return tor_paths

def create_firewall_exceptions():
    """Create targeted firewall exceptions for Tor connectivity (Windows only)"""
    if platform.system() != 'Windows':
        print("❌ This script is for Windows only. Not applicable on this OS.")
        return False
        
    if not is_admin():
        print("\n❌ This script must be run as administrator to modify firewall rules.")
        print("   Please right-click on the script and select 'Run as administrator'")
        return False
        
    print("\n" + "=" * 80)
    print(" 🔧 Dark Web Crawler - Firewall Configuration Tool 🔧 ")
    print("=" * 80)
    print("\nThis tool creates targeted firewall exceptions for the Dark Web Crawler")
    print("It will only allow specific connections needed for the crawler to work with Tor")
    print("Your general firewall protection will remain active for all other applications\n")
        
    try:
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
            print("❌ Could not find Firefox installation.")
            print("   Please install Firefox and try again.")
            return False
            
        # Python executable path
        python_exe = sys.executable
        
        # Find Tor Browser installations
        tor_paths = find_tor_browser_paths()
        if tor_paths:
            print(f"✓ Found {len(tor_paths)} Tor Browser installation(s)")
        else:
            print("⚠️ No Tor Browser installation found. Will continue without Tor Browser rules.")
            print("   Install Tor Browser and run this script again for complete protection.")
        
        # Create highly targeted firewall rules
        rules = [
            # Allow Firefox to connect to Tor
            f'New-NetFirewallRule -DisplayName "DarkWebCrawler Firefox-Tor" -Direction Outbound -Program "{firefox_path}" -RemotePort 9050 -Protocol TCP -Action Allow',
            
            # Allow Python to connect to Tor
            f'New-NetFirewallRule -DisplayName "DarkWebCrawler Python-Tor" -Direction Outbound -Program "{python_exe}" -RemotePort 9050 -Protocol TCP -Action Allow',
        ]
        
        # Add rules for Tor Browser
        for i, tor_path in enumerate(tor_paths):
            rules.append(f'New-NetFirewallRule -DisplayName "Tor Browser {i+1}" -Direction Outbound -Program "{tor_path}" -Action Allow')
            rules.append(f'New-NetFirewallRule -DisplayName "Tor Browser In {i+1}" -Direction Inbound -Program "{tor_path}" -Action Allow')
        
        print("📋 Creating targeted firewall exceptions...")
        
        successful_rules = 0
        for rule in rules:
            try:
                # Use PowerShell to create the rule
                result = subprocess.run(["powershell", "-Command", rule], 
                               check=True, 
                               capture_output=True)
                
                # Print name of the rule that was created
                rule_name = rule.split('-DisplayName')[1].split('"')[1]
                print(f"✅ Created firewall rule: {rule_name}")
                successful_rules += 1
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create firewall rule: {e}")
                print(f"   Error output: {e.stderr.decode() if e.stderr else 'Unknown error'}")
                
        # Last resort - create a rule for the Tor executable itself if we found no Tor Browser
        if not tor_paths:
            try:
                tor_rule = 'New-NetFirewallRule -DisplayName "Tor Service" -Direction Outbound -Program "*tor.exe" -Action Allow'
                subprocess.run(["powershell", "-Command", tor_rule], check=True, capture_output=True)
                print(f"✅ Created fallback firewall rule: Tor Service")
                successful_rules += 1
            except:
                pass
                
        if successful_rules > 0:
            print("\n✅ Firewall exceptions successfully created!")
            print("   The Dark Web Crawler should now be able to connect to Tor while")
            print("   maintaining firewall protection for all other applications.")
            print("\n   To use: Start Tor Browser first, then run the crawler.")
            return True
        else:
            print("\n❌ Failed to create any firewall exceptions")
            return False
    except Exception as e:
        print(f"❌ Error creating firewall exceptions: {e}")
        return False

if __name__ == "__main__":
    create_firewall_exceptions() 