import subprocess
import os
import json
import shutil
import urllib.request
import zipfile

def run_cmd(cmd, capture_output=False, shell=False):
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True, shell=shell)
    if capture_output:
        return result.stdout.strip()
    return None

# Update system
run_cmd(["sudo", "apt", "update"])
run_cmd(["sudo", "apt", "-y", "upgrade"])
run_cmd(["sudo", "apt", "install", "-y", "unzip", "certbot", "python3-pip"])
run_cmd(["pip3", "install", "requests"])

# Download GoPhish
github_api_url = "https://api.github.com/repos/gophish/gophish/releases/latest"
print("Fetching latest GoPhish release URL...")
with urllib.request.urlopen(github_api_url) as response:
    data = json.loads(response.read().decode())
    asset = next(
        (a for a in data['assets'] if "linux" in a['name'] and "64" in a['name'] and a['name'].endswith(".zip")),
        None
    )
    if asset is None:
        raise Exception("Could not find suitable GoPhish asset")
    download_url = asset['browser_download_url']

zip_file = "/tmp/gophish.zip"
print(f"Downloading GoPhish from {download_url}...")
urllib.request.urlretrieve(download_url, zip_file)

gophish_dir = "/opt/gophish"
if os.path.exists(gophish_dir):
    shutil.rmtree(gophish_dir)

os.makedirs(gophish_dir, exist_ok=True)
with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(gophish_dir)

# Ask domain
domain = input("Enter your domain for SSL certificate (e.g., phishing.example.com): ")

# Run certbot with Infomaniak DNS hook
hook_script = "/path/to/infomaniak_dns_hook.py"  # <-- Update this path!
run_cmd([
    "sudo", "certbot", "certonly",
    "--manual",
    "--preferred-challenges", "dns",
    "--manual-auth-hook", hook_script,
    "--manual-cleanup-hook", hook_script,
    "-d", domain
])

cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"

if not (os.path.isfile(cert_path) and os.path.isfile(key_path)):
    raise FileNotFoundError("Certificate files not found. Check Certbot output.")

# Modify config.json
config_file = os.path.join(gophish_dir, "config.json")
with open(config_file, 'r') as f:
    config = json.load(f)

config['admin_server']['listen_url'] = "0.0.0.0:3333"
config['admin_server']['use_tls'] = True
config['admin_server']['cert_path'] = cert_path
config['admin_server']['key_path'] = key_path

with open(config_file, 'w') as f:
    json.dump(config, f, indent=4)

print("config.json updated.")

# Launch GoPhish
gophish_binary = os.path.join(gophish_dir, "gophish")
log_file = os.path.join(gophish_dir, "gophish.log")

print(f"Starting GoPhish... Logs at {log_file}")
with open(log_file, "w") as f:
    subprocess.Popen([gophish_binary], cwd=gophish_dir, stdout=f, stderr=subprocess.STDOUT)

print("GoPhish started. Check log for admin credentials.")
