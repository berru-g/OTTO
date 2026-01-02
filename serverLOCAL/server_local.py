# server local sur port 8080
# redirection auto 1s sur landing_url
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import json
from datetime import datetime

LANDING_URL = "https://berru-g.github.io/OTTO/SMBchat/SMBchatV2/"

class WelcomeRedirectHandler(BaseHTTPRequestHandler):
    """Page d'accueil simple qui redirige après affichage"""
    
    def do_GET(self):
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', '')
        
        # Détecte Android
        is_android = 'Android' in user_agent
        device_type = 'Android' if is_android else 'Autre'
        
        # Log structuré
        log_entry = {
            'time': datetime.now().isoformat(),
            'ip': client_ip,
            'device': device_type,
            'agent': user_agent[:100],
            'path': self.path
        }
        
        print(f"📱 {device_type} connecté depuis {client_ip}")
        print(f"📱 {user_agent[:100]} agent {self.path} path")
        
        # Sauvegarde JSON
        with open("network_logs.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Page d'accueil personnalisée
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome - Berru-G Network</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #0f172a;
                    color: #e2e8f0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                }}
                .card {{
                    background: #1e293b;
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 500px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                    border: 1px solid #334155;
                }}
                h1 {{
                    color: #60a5fa;
                    margin-bottom: 10px;
                }}
                .ip-display {{
                    background: #334155;
                    padding: 10px 20px;
                    border-radius: 10px;
                    font-family: monospace;
                    margin: 20px 0;
                }}
                .countdown {{
                    font-size: 2em;
                    color: #34d399;
                    margin: 20px 0;
                }}
                .btn {{
                    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    font-size: 1.1em;
                    cursor: pointer;
                    margin-top: 20px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 0.8em;
                    opacity: 0.7;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Bienvenue sur le réseau local</h1>
                <p>Vous allez etre redirigé vers un logiciel à installer pour que nous puissions communiquer.</p>
                
                <div class="ip-display">
                    📍 IP: {client_ip}
                </div>
                
                <p>Redirection automatique vers la landing page...</p>
                
                <div class="countdown" id="countdown">10</div>
                
                <a href="{LANDING_URL}" class="btn" id="redirectBtn">
                    Accéder maintenant →
                </a>
                
                <div class="footer">
                    <p>Serveur local • {datetime.now().strftime("%H:%M:%S")}</p>
                </div>
            </div>
            
            <script>
            // Compte à rebours
            let count = 10;
            const countdownEl = document.getElementById('countdown');
            const btn = document.getElementById('redirectBtn');
            
            const timer = setInterval(() => {{
                count--;
                countdownEl.textContent = count;
                
                if (count <= 0) {{
                    clearInterval(timer);
                    window.location.href = "{LANDING_URL}";
                }}
            }}, 1000);
            
            // Track le click manuel
            btn.addEventListener('click', () => {{
                fetch('/_log?action=manual_click');
            }});
            </script>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

if __name__ == "__main__":
    PORT = 8080
    local_ip = socket.gethostbyname(socket.gethostname())
    
    print("="*60)
    print("SERVEUR LOCAL 80 + REDIRECTION")
    print("="*60)
    print(f"📡 Adresse locale: http://{local_ip}:{PORT}")
    print(f"🎯 Landing finale: {LANDING_URL}")
    print(f"📊 Logs: network_logs.json")
    print("\n✨ Les utilisateurs voient une page d'accueil avant redirection")
    print("="*60)
    
    server = HTTPServer(('0.0.0.0', PORT), WelcomeRedirectHandler)
    server.serve_forever()