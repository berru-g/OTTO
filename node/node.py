# cryptomixer_node.py
"""
Node pour un mixer de crypto décentralisé sur réseau local
Implémentation simplifiée de CoinJoin/Wasabi/JoinMarket
"""
import hashlib
import json
import secrets
from typing import Dict, List, Tuple
from datetime import datetime
import socket
import threading
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import base64

class CryptoTx:
    """Transaction cryptographique de base"""
    
    def __init__(self, txid: str = None):
        self.txid = txid or self.generate_txid()
        self.inputs: List[Dict] = []
        self.outputs: List[Dict] = []
        self.signatures: List[str] = []
        self.timestamp = datetime.now().isoformat()
        self.mix_round = 0
        
    def generate_txid(self) -> str:
        """Génère un TXID unique"""
        random_data = secrets.token_bytes(32) + str(datetime.now().timestamp()).encode()
        return hashlib.sha256(random_data).hexdigest()[:64]
    
    def add_input(self, prev_txid: str, vout: int, amount: float, pubkey: str):
        """Ajoute une entrée à la transaction"""
        self.inputs.append({
            'prev_txid': prev_txid,
            'vout': vout,
            'amount': amount,
            'pubkey': pubkey
        })
    
    def add_output(self, address: str, amount: float):
        """Ajoute une sortie à la transaction"""
        self.outputs.append({
            'address': address,
            'amount': amount
        })
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'txid': self.txid,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'signatures': self.signatures,
            'timestamp': self.timestamp,
            'mix_round': self.mix_round
        }

class MixerNode:
    """
    Node d'un réseau de mixing décentralisé
    Implémente le protocole CoinJoin de base
    """
    
    def __init__(self, node_id: str = None, port: int = 8333):
        self.node_id = node_id or self.generate_node_id()
        self.port = port
        self.peers: List[str] = []  # Liste des IPs des autres nodes
        self.pending_transactions: Dict[str, CryptoTx] = {}
        self.completed_mixes: List[Dict] = []
        
        # Clés pour signatures
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        
        # Anonymisation
        self.tor_proxy = None  # À configurer si tu veux Tor
        self.mix_fee = 0.001  # 0.1% de frais
        
        print(f"🔐 Node Mixer démarré: {self.node_id}")
        print(f"📍 Port: {self.port}")
        print(f"📡 Clé publique: {self.get_pubkey_hex()}")
    
    def generate_node_id(self) -> str:
        """Génère un ID unique pour le node"""
        random_bytes = secrets.token_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:16]
    
    def get_pubkey_hex(self) -> str:
        """Retourne la clé publique en hex"""
        return self.public_key.to_string().hex()
    
    def create_coinjoin_proposal(self, inputs: List[Dict], outputs: List[Dict]) -> CryptoTx:
        """
        Crée une proposition de CoinJoin
        
        inputs: [
            {'prev_txid': 'abc...', 'vout': 0, 'amount': 1.0, 'pubkey': 'pubkey_hex'}
        ]
        outputs: [
            {'address': 'bc1q...', 'amount': 0.999},  # Montant - frais
            {'address': 'change_address', 'amount': 0.001}  # Frais
        ]
        """
        tx = CryptoTx()
        
        for inp in inputs:
            tx.add_input(
                prev_txid=inp['prev_txid'],
                vout=inp['vout'],
                amount=inp['amount'],
                pubkey=inp['pubkey']
            )
        
        for out in outputs:
            tx.add_output(
                address=out['address'],
                amount=out['amount']
            )
        
        # Signe la transaction
        tx_data = json.dumps(tx.to_dict(), sort_keys=True).encode()
        signature = self.private_key.sign(tx_data)
        tx.signatures.append(base64.b64encode(signature).decode())
        
        self.pending_transactions[tx.txid] = tx
        return tx
    
    def verify_signature(self, tx: CryptoTx, pubkey_hex: str) -> bool:
        """Vérifie une signature sur une transaction"""
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(pubkey_hex), curve=SECP256k1)
            tx_dict = tx.to_dict()
            tx_dict.pop('signatures', None)  # Retire les signatures pour vérification
            tx_data = json.dumps(tx_dict, sort_keys=True).encode()
            
            if tx.signatures:
                signature = base64.b64decode(tx.signatures[0])
                return vk.verify(signature, tx_data)
        except:
            return False
        return False
    
    def mix_transactions(self, transactions: List[CryptoTx]) -> CryptoTx:
        """
        Mélange plusieurs transactions en une
        C'est le cœur du CoinJoin
        """
        if len(transactions) < 2:
            raise ValueError("Besoin d'au moins 2 transactions pour mixer")
        
        # Vérifie que les montants sont égaux (condition CoinJoin)
        amounts = []
        for tx in transactions:
            total_input = sum(inp['amount'] for inp in tx.inputs)
            total_output = sum(out['amount'] for out in tx.outputs)
            amounts.append(total_input)
            
            # Vérifie que input ≈ output (aux frais près)
            if abs(total_input - total_output) > self.mix_fee * 2:
                raise ValueError(f"Transaction {tx.txid} déséquilibrée")
        
        # Tous les montants doivent être identiques pour un bon mix
        if len(set(round(a, 8) for a in amounts)) > 1:
            print("⚠️ Montants différents, mixage partiel possible")
        
        # Crée une transaction mixée
        mixed_tx = CryptoTx()
        mixed_tx.mix_round = max(tx.mix_round for tx in transactions) + 1
        
        # Agrège tous les inputs
        for tx in transactions:
            for inp in tx.inputs:
                mixed_tx.inputs.append(inp)
        
        # Mélange les outputs aléatoirement
        all_outputs = []
        for tx in transactions:
            all_outputs.extend(tx.outputs)
        
        # Randomize pour briser les liens
        secrets.SystemRandom().shuffle(all_outputs)
        mixed_tx.outputs = all_outputs
        
        # Collecte les signatures
        for tx in transactions:
            if tx.signatures:
                mixed_tx.signatures.extend(tx.signatures)
        
        print(f"✅ {len(transactions)} transactions mixées en round {mixed_tx.mix_round}")
        print(f"   Inputs: {len(mixed_tx.inputs)}, Outputs: {len(mixed_tx.outputs)}")
        
        return mixed_tx
    
    def start_network_listener(self):
        """Démarre le serveur P2P pour écouter les autres nodes"""
        def listener_thread():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('0.0.0.0', self.port))
            server.listen(5)
            
            print(f"📡 Node en écoute sur port {self.port}")
            
            while True:
                client, addr = server.accept()
                threading.Thread(
                    target=self.handle_peer_connection,
                    args=(client, addr)
                ).start()
        
        thread = threading.Thread(target=listener_thread, daemon=True)
        thread.start()
    
    def handle_peer_connection(self, client_socket, addr):
        """Gère une connexion d'un autre node"""
        try:
            data = client_socket.recv(4096).decode()
            message = json.loads(data)
            
            msg_type = message.get('type')
            
            if msg_type == 'PEER_DISCOVERY':
                # Un nouveau node se présente
                peer_ip = addr[0]
                if peer_ip not in self.peers:
                    self.peers.append(peer_ip)
                    print(f"👥 Nouveau peer: {peer_ip}")
                
                # Répond avec notre liste de peers
                response = {
                    'type': 'PEER_LIST',
                    'peers': self.peers,
                    'node_id': self.node_id
                }
                client_socket.send(json.dumps(response).encode())
                
            elif msg_type == 'TX_PROPOSAL':
                # Proposition de transaction à mixer
                tx_data = message['transaction']
                tx = CryptoTx(tx_data['txid'])
                tx.inputs = tx_data['inputs']
                tx.outputs = tx_data['outputs']
                tx.signatures = tx_data.get('signatures', [])
                
                # Vérifie et stocke
                if self.verify_transaction(tx):
                    self.pending_transactions[tx.txid] = tx
                    print(f"📨 Proposition TX reçue: {tx.txid[:16]}...")
                    
                    # Check si on a assez de TX pour mixer
                    if len(self.pending_transactions) >= 2:
                        self.attempt_mix()
                
            elif msg_type == 'READY_TO_MIX':
                # Un node est prêt à mixer
                print(f"🔄 Node {addr[0]} prêt pour mixage")
                
        except Exception as e:
            print(f"❌ Erreur avec {addr[0]}: {e}")
        finally:
            client_socket.close()
    
    def verify_transaction(self, tx: CryptoTx) -> bool:
        """Vérifie une transaction reçue"""
        # Vérifie les signatures
        for i, inp in enumerate(tx.inputs):
            if i < len(tx.signatures):
                if not self.verify_signature(tx, inp['pubkey']):
                    print(f"⚠️ Signature invalide pour input {i}")
                    return False
        
        # Vérifie les montants
        input_sum = sum(inp['amount'] for inp in tx.inputs)
        output_sum = sum(out['amount'] for out in tx.outputs)
        
        if output_sum > input_sum:
            print(f"⚠️ Output > Input: {output_sum} > {input_sum}")
            return False
        
        return True
    
    def attempt_mix(self):
        """Tente de mixer les transactions en attente"""
        if len(self.pending_transactions) < 2:
            return
        
        print(f"🔄 Tentative de mixage avec {len(self.pending_transactions)} TX...")
        
        # Sélectionne 2 transactions aléatoires
        tx_ids = list(self.pending_transactions.keys())
        selected = secrets.SystemRandom().sample(tx_ids, min(2, len(tx_ids)))
        
        transactions = [self.pending_transactions[tx_id] for tx_id in selected]
        
        try:
            mixed_tx = self.mix_transactions(transactions)
            
            # Enregistre le mix
            mix_record = {
                'timestamp': datetime.now().isoformat(),
                'input_txs': selected,
                'output_tx': mixed_tx.txid,
                'round': mixed_tx.mix_round,
                'amount': sum(inp['amount'] for inp in mixed_tx.inputs)
            }
            
            self.completed_mixes.append(mix_record)
            
            # Nettoie les TX mixées
            for tx_id in selected:
                del self.pending_transactions[tx_id]
            
            # Broadcast aux peers
            self.broadcast_mix(mixed_tx)
            
            # Sauvegarde
            self.save_mix_record(mix_record)
            
        except Exception as e:
            print(f"❌ Mixage échoué: {e}")
    
    def broadcast_mix(self, mixed_tx: CryptoTx):
        """Diffuse la transaction mixée aux peers"""
        message = {
            'type': 'MIX_COMPLETE',
            'transaction': mixed_tx.to_dict(),
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat()
        }
        
        for peer in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((peer, self.port))
                sock.send(json.dumps(message).encode())
                sock.close()
            except:
                print(f"⚠️ Impossible de contacter peer {peer}")
    
    def save_mix_record(self, record: Dict):
        """Sauvegarde un enregistrement de mix"""
        filename = f"mix_history_{datetime.now().strftime('%Y%m')}.json"
        
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
        except:
            history = []
        
        history.append(record)
        
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
    
    def connect_to_peer(self, peer_ip: str):
        """Se connecte à un autre node"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, self.port))
            
            # Envoie notre info
            message = {
                'type': 'PEER_DISCOVERY',
                'node_id': self.node_id,
                'port': self.port,
                'pubkey': self.get_pubkey_hex()
            }
            
            sock.send(json.dumps(message).encode())
            
            # Réception réponse
            response = sock.recv(4096).decode()
            data = json.loads(response)
            
            if data.get('type') == 'PEER_LIST':
                # Ajoute les nouveaux peers
                for peer in data['peers']:
                    if peer not in self.peers and peer != socket.gethostbyname(socket.gethostname()):
                        self.peers.append(peer)
                
                print(f"📡 Connecté à {peer_ip}, {len(data['peers'])} peers connus")
            
            sock.close()
            return True
            
        except Exception as e:
            print(f"❌ Connexion échouée à {peer_ip}: {e}")
            return False
    
    def start_mixer_dashboard(self):
        """Interface console pour le mixer"""
        import time
        
        print("\n" + "="*60)
        print("🔐 CRYPTO MIXER NODE - DASHBOARD")
        print("="*60)
        
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
            print(f"📊 Stats:")
            print(f"  • Node ID: {self.node_id[:16]}...")
            print(f"  • Peers: {len(self.peers)}")
            print(f"  • TX en attente: {len(self.pending_transactions)}")
            print(f"  • Mixs complétés: {len(self.completed_mixes)}")
            print(f"  • Port: {self.port}")
            
            print("\n📋 Commandes:")
            print("  list    - Lister les TX en attente")
            print("  mixnow  - Forcer un mixage")
            print("  peers   - Afficher les peers")
            print("  connect IP - Se connecter à un peer")
            print("  quit    - Quitter")
            
            cmd = input("\n> ").strip().lower()
            
            if cmd == "list":
                print("\n📨 Transactions en attente:")
                for txid, tx in self.pending_transactions.items():
                    print(f"  • {txid[:16]}... ({len(tx.inputs)} inputs)")
                    
            elif cmd == "mixnow":
                self.attempt_mix()
                
            elif cmd == "peers":
                print("\n👥 Peers connectés:")
                for peer in self.peers:
                    print(f"  • {peer}")
                    
            elif cmd.startswith("connect "):
                peer_ip = cmd.split(" ")[1]
                self.connect_to_peer(peer_ip)
                
            elif cmd == "quit":
                print("👋 Arrêt du node...")
                break
            
            time.sleep(1)

# Exemple d'utilisation
def main():
    """Lance un node de mixer"""
    
    print("""
    ╔══════════════════════════════════════════════════╗
    ║           NODE MIXER CRYPTO - LOCAL              ║
    ║         Implémentation CoinJoin simplifiée       ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Configuration
    port = int(input("Port (défaut: 8333): ") or "8333")
    node_id = input("Node ID (laisser vide pour auto): ") or None
    
    # Création du node
    node = MixerNode(node_id=node_id, port=port)
    
    # Démarre les services
    node.start_network_listener()
    
    # Se connecte à des peers existants (optionnel)
    initial_peers = input("Peers initiaux (IPs séparées par virgule): ")
    if initial_peers:
        for peer_ip in initial_peers.split(','):
            peer_ip = peer_ip.strip()
            if peer_ip:
                node.connect_to_peer(peer_ip)
    
    # Lance le dashboard
    node.start_mixer_dashboard()

if __name__ == "__main__":
    # Installation des dépendances nécessaires
    print("Installation des dépendances:")
    print("pip install ecdsa")
    
    main()