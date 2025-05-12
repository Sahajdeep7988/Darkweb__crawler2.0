import os
import sys
import platform
import zipfile
import urllib.request
import shutil
from urllib.error import URLError
import subprocess

def download_geckodriver():
    """Download GeckoDriver directly without using GitHub API"""
    print("\n" + "=" * 80)
    print(" 🔧 GeckoDriver Downloader - Fixing GitHub API Rate Limit Issues 🔧 ")
    print("=" * 80)
    print("\nThis tool will download GeckoDriver directly, bypassing GitHub API rate limits\n")
    
    # Create drivers directory if it doesn't exist
    driver_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drivers")
    if not os.path.exists(driver_dir):
        os.makedirs(driver_dir)
    
    # Determine system and architecture
    system = platform.system()
    bits = platform.architecture()[0]
    
    # Use fixed version to avoid GitHub API rate limits
    geckodriver_version = "v0.31.0"
    
    if system == "Windows":
        if bits == "64bit":
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-win64.zip"
            driver_name = "geckodriver.exe"
        else:
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-win32.zip"
            driver_name = "geckodriver.exe"
    elif system == "Darwin":  # macOS
        if "arm" in platform.processor().lower():
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-macos-aarch64.tar.gz"
        else:
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-macos.tar.gz"
        driver_name = "geckodriver"
    else:  # Linux
        if bits == "64bit":
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-linux64.tar.gz"
        else:
            url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-linux32.tar.gz"
        driver_name = "geckodriver"
    
    # Use a secure connection for downloading
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    
    zip_path = os.path.join(driver_dir, "geckodriver.zip")
    driver_path = os.path.join(driver_dir, driver_name)
    
    # Check if we already have the driver
    if os.path.exists(driver_path):
        print(f"✅ GeckoDriver already exists at {driver_path}")
        choice = input("Do you want to re-download it anyway? (y/n): ").lower()
        if choice != 'y':
            return driver_path
    
    # Create a request with secure headers
    print(f"🔗 Downloading from {url}")
    req = urllib.request.Request(url, headers=headers)
    
    try:
        # Download the file with a timeout
        with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, 'wb') as out_file:
            print("⬇️ Downloading...")
            data = response.read()
            out_file.write(data)
            print(f"✅ Downloaded {len(data)/1024:.1f} KB")
            
    except URLError as e:
        if "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
            print("❌ SSL certificate verification failed. Trying alternative download method...")
            try:
                if system == "Windows":
                    # Use PowerShell as alternative
                    ps_cmd = f'(New-Object Net.WebClient).DownloadFile("{url}", "{zip_path}")'
                    subprocess.run(["powershell", "-Command", ps_cmd], check=True)
                    print("✅ PowerShell download successful")
                else:
                    # Use curl as alternative
                    subprocess.run(["curl", "-L", "-o", zip_path, url], check=True)
                    print("✅ curl download successful")
            except Exception as alt_e:
                print(f"❌ Alternative download also failed: {alt_e}")
                print(f"🔧 Please download GeckoDriver manually from: {url}")
                print(f"   And place it in: {driver_dir}")
                return None
        else:
            print(f"❌ Download failed: {e}")
            print(f"🔧 Please download GeckoDriver manually from: {url}")
            print(f"   And place it in: {driver_dir}")
            return None
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return None
    
    # Extract the file
    try:
        print("📂 Extracting files...")
        if system == "Windows":
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(driver_dir)
        else:
            import tarfile
            with tarfile.open(zip_path, "r:gz") as tar:
                tar.extractall(driver_dir)
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return None
    
    # Make executable on non-Windows systems
    if system != "Windows":
        os.chmod(driver_path, 0o755)
        
    # Clean up zip file
    try:
        os.remove(zip_path)
    except:
        pass
    
    print(f"✅ GeckoDriver successfully installed to {driver_path}")
    print("   You can now run the crawler without GitHub API rate limit issues")
    return driver_path

if __name__ == "__main__":
    download_geckodriver() 