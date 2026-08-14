import urllib.parse, http.server, webbrowser, threading, requests, sys, os

APP_ID = input("ID de tu app Pinterest (1575463): ").strip() or "1575463"
APP_SECRET = input("Pega la clave secreta de Pinterest (la que empieza por shpss_...): ").strip()

REDIRECT_URI = "http://localhost:8888/callback"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
code_holder = {"code": None}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            code_holder["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type","text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Listo, vuelve al Terminal</h2>")
    def log_message(self, *a): pass

auth_url = f"https://www.pinterest.com/oauth/?client_id={APP_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope={SCOPES}"
t = threading.Thread(target=lambda: http.server.HTTPServer(("localhost",8888),Handler).handle_request())
t.daemon = True
t.start()
webbrowser.open(auth_url)
print("Acepta los permisos en el navegador...")
t.join(timeout=120)

if not code_holder["code"]:
    print("No se recibió autorización")
    sys.exit(1)

r = requests.post("https://api.pinterest.com/v5/oauth/token",
    auth=(APP_ID, APP_SECRET),
    data={"grant_type":"authorization_code","code":code_holder["code"],"redirect_uri":REDIRECT_URI},
    headers={"Content-Type":"application/x-www-form-urlencoded"})

token = r.json().get("access_token","")
if token:
    print(f"\nTOKEN: {token}\n")
    content = open(".env").read()
    lines = [f"PINTEREST_ACCESS_TOKEN={token}" if l.startswith("PINTEREST_ACCESS_TOKEN=") else l for l in content.splitlines()]
    open(".env","w").write("\n".join(lines))
    print("Token guardado en .env")
else:
    print(f"Error: {r.text}")
