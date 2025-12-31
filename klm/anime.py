import smtplib
from threading import Thread
import time

def start_local_smtp_server(port=1025):
    """Démarre un mini serveur SMTP en arrière-plan"""
    from smtpd import SMTPServer
    import asyncore
    
    class LocalSMTPServer(SMTPServer):
        def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
            print(f"📨 Email reçu de {mailfrom}")
            print(f"   Pour: {rcpttos}")
            print(f"   Taille: {len(data)} octets")
            # Ici tu pourrais sauvegarder le mail dans un fichier
            return
    
    server = LocalSMTPServer(('localhost', port), None)
    
    def run_server():
        print(f"🖥️  Serveur SMTP démarré sur localhost:{port}")
        asyncore.loop(timeout=1)
    
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(1)  # Laisse le temps de démarrer
    return thread

# Utilisation
def send_email_no_auth():
    # Démarre le serveur
    start_local_smtp_server(1025)
    
    # Envoie via ce serveur
    with smtplib.SMTP('localhost', 1025) as server:
        server.sendmail(
            'moi@localhost',
            ['ton_email@protonmail.com'],
            'Subject: Donnees\n\nContenu ici'
        )
    print("✅ Email envoyé via serveur local")