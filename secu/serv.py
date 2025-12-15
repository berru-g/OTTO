from zeroconf import Zeroconf, ServiceInfo
import socket

# Crée un service Android-like
service = ServiceInfo(
    '_androidtvremote._tcp.local.',
    'Android TV Remote Service._androidtvremote._tcp.local.',
    addresses=[socket.inet_aton('192.168.1.0')],
    port=6466,
    properties={}
)

zeroconf = Zeroconf()
zeroconf.register_service(service)
print('Appât actif! Les Android vont se révéler...')
input('Appuye sur Entrée pour arrêter')
zeroconf.unregister_service(service)