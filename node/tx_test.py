# simulation_tx.py
node = MixerNode()

# Crée une transaction test
inputs = [{
    'prev_txid': 'a'*64,
    'vout': 0,
    'amount': 1.0,
    'pubkey': node.get_pubkey_hex()
}]

outputs = [{
    'address': 'bc1qtest123',
    'amount': 0.999
}]

tx = node.create_coinjoin_proposal(inputs, outputs)