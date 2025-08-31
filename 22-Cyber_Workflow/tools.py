import requests
from bs4 import BeautifulSoup
import ssl
import socket
from datetime import datetime

def check_http_redirect(domain: str) -> str:
    """Vérifie si HTTP redirige vers HTTPS"""
    try:
        r = requests.get(f"http://{domain}", timeout=5, allow_redirects=True)
        if r.url.startswith("https://"):
            return "✅ HTTP redirects to HTTPS."
        else:
            return "❌ HTTP does not redirect securely. Final URL: {r.url}"
    except Exception as e:
        return f"Redirect check failed: {e}"

def check_github_mentions(domain: str) -> str:
    """Recherche les mentions GitHub du domaine"""
    try:
        query = f'"{domain}" site:github.com'
        return f"🔍 Search manually for GitHub mentions:\\nhttps://www.google.com/search?q={query.replace(' ', '+')}"
    except Exception as e:
        return f"GitHub mention check failed: {e}"

def check_ssl_certificate(domain: str) -> str:
    """Vérifie le certificat SSL"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.utcnow()).days
                return f"✅ SSL Certificate is valid. Expires in {days_left} days."
    except Exception as e:
        return f"SSL certificate check failed: {e}"

def check_api_endpoints(domain: str) -> str:
    """Vérifie les endpoints API communs"""
    common_paths = ["/api", "/api/v1", "/graphql", "/swagger", "/admin", "/api-docs"]
    found = []
    
    for path in common_paths:
        url = f"https://{domain}{path}"
        try:
            r = requests.get(url, timeout=3)
            if r.status_code in [200, 403, 401]:
                found.append(f"{url} - Status {r.status_code}")
        except:
            continue
    
    if found:
        return "⚠️ Possible API endpoints:\\n" + "\\n".join(found)
    else:
        return "✅ No common API endpoints found."

def check_cookie_flags(domain: str) -> str:
    """Vérifie les flags de sécurité des cookies"""
    try:
        r = requests.get(f"https://{domain}", timeout=5)
        cookies = r.headers.get("Set-Cookie", "")
        issues = []
        
        if cookies:
            if "Secure" not in cookies:
                issues.append("Missing 'Secure'")
            if "HttpOnly" not in cookies:
                issues.append("Missing 'HttpOnly'")
        
        if issues:
            return "⚠️ Cookie flags issue: " + ", ".join(issues)
        return "✅ Cookies have Secure and HttpOnly flags."
    except Exception as e:
        return f"Cookie security check failed: {e}"

def check_security_headers(domain: str) -> str:
    """Vérifie les en-têtes de sécurité"""
    try:
        url = f"https://{domain}"
        response = requests.get(url, timeout=5)
        headers = response.headers
        
        results = []
        required = ['Content-Security-Policy', 'X-Frame-Options', 'Strict-Transport-Security']
        
        for h in required:
            if h in headers:
                results.append(f"✅ {h} found")
            else:
                results.append(f"❌ {h} missing")
        
        return "\\n".join(results)
    except Exception as e:
        return f"Header check failed: {e}"

def check_common_directories(domain: str) -> str:
    """Vérifie les répertoires communs"""
    url_base = f"https://{domain}"
    wordlist = ["/admin", "/login", "/config", "/.git", "/backup"]
    found = []
    
    for path in wordlist:
        try:
            full_url = url_base + path
            r = requests.get(full_url, timeout=3)
            if r.status_code in [200, 301, 403]:
                found.append(f"🔍 Found: {full_url} [{r.status_code}]")
        except:
            continue
    
    return "\\n".join(found) if found else "No common directories found."

def find_js_urls(domain: str) -> str:
    """Trouve les fichiers JavaScript"""
    try:
        url = f"https://{domain}"
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        js_urls = []
        
        for script in soup.find_all("script", src=True):
            src = script["src"]
            if src.startswith("http"):
                js_urls.append(src)
            else:
                js_urls.append(f"{url.rstrip('/')}/{src.lstrip('/')}")
        
        return "\\n".join(js_urls) if js_urls else "No JS files found."
    except Exception as e:
        return f"JS scan failed: {e}"

def check_robots_txt(domain: str) -> str:
    """Vérifie le fichier robots.txt"""
    try:
        url = f"https://{domain}/robots.txt"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return f"✅ robots.txt found:\\n{r.text[:500]}"
        else:
            return f"❌ robots.txt not found (status {r.status_code})"
    except Exception as e:
        return f"robots.txt check failed: {e}"

def check_sitemap(domain: str) -> str:
    """Vérifie le fichier sitemap.xml"""
    try:
        url = f"https://{domain}/sitemap.xml"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return f"✅ sitemap.xml found:\\n{r.text[:500]}"
        else:
            return f"❌ sitemap.xml not found (status {r.status_code})"
    except Exception as e:
        return f"sitemap check failed: {e}"

def check_env_exposure(domain: str) -> str:
    """Vérifie l'exposition du fichier .env"""
    try:
        url = f"https://{domain}/.env"
        r = requests.get(url, timeout=3)
        if "APP_KEY" in r.text or "DB_PASSWORD" in r.text:
            return f"⚠️ Exposed .env file found:\\n{r.text[:300]}"
        elif r.status_code == 200:
            return "⚠️ .env file exists but no sensitive data detected."
        else:
            return "✅ .env file not accessible."
    except Exception as e:
        return f".env check failed: {e}"

def check_server_header(domain: str) -> str:
    """Vérifie l'en-tête Server"""
    try:
        url = f"https://{domain}"
        r = requests.get(url, timeout=5)
        server = r.headers.get("Server", "Not found")
        return f"🔍 Server header: {server}"
    except Exception as e:
        return f"Server header check failed: {e}"

# Fonction principale pour exécuter tous les tests
def run_security_scan(domain: str):
    """Exécute un scan de sécurité complet"""
    print(f"=== Security Scan for {domain} ===\\n")
    
    checks = [
        ("HTTP to HTTPS Redirect", check_http_redirect),
        ("SSL Certificate", check_ssl_certificate),
        ("Security Headers", check_security_headers),
        ("Cookie Security", check_cookie_flags),
        ("API Endpoints", check_api_endpoints),
        ("Common Directories", check_common_directories),
        ("JavaScript Files", find_js_urls),
        ("robots.txt", check_robots_txt),
        ("sitemap.xml", check_sitemap),
        ("Environment File", check_env_exposure),
        ("Server Header", check_server_header),
        ("GitHub Mentions", check_github_mentions)
    ]
    
    for check_name, check_function in checks:
        print(f"--- {check_name} ---")
        result = check_function(domain)
        print(result)
        print()

# Exemple d'utilisation
if __name__ == "__main__":
    domain = input("Enter domain to scan: ")
    run_security_scan(domain)