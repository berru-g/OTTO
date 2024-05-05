import os
from cryptography.fernet import Fernet

# Fonction pour effacer l'écran du terminal
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Fonction pour afficher l'interface utilisateur d'accueil
def display_welcome():
    clear_screen()
    print("Bienvenue dans votre gestionnaire de mots de passe !")
    print("Pour commencer, veuillez enregistrer un identifiant et un mot de passe maître.")
    print("Pour enregistrer un nouveau mot de passe, entrez 'add'.")
    print("Pour quitter, entrez 'quit' à tout moment.")

# Fonction pour enregistrer un identifiant et un mot de passe maître
def register_master_password():
    print("Enregistrement du mot de passe maître...")
    username = input("Veuillez entrer un identifiant : ")
    master_password = input("Veuillez entrer un mot de passe maître : ")
    key = Fernet.generate_key()
    encrypted_master_password = encrypt_password(key, master_password)
    # Ici, tu peux enregistrer l'identifiant et le mot de passe maître chiffré dans un fichier ou une base de données sécurisée
    print("Identifiant et mot de passe maître enregistrés avec succès !")
    return key

# Fonction pour enregistrer un nouveau mot de passe
def add_password(key):
    print("Enregistrement d'un nouveau mot de passe...")
    service_name = input("Nom du service ou du site : ")
    password = input("Mot de passe : ")
    encrypted_password = encrypt_password(key, password)
    # Ici, tu peux enregistrer le nom du service et le mot de passe chiffré de manière sécurisée
    print("Mot de passe enregistré avec succès !")

# Fonction pour chiffrer un mot de passe avec une clé donnée
def encrypt_password(key, password):
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(password.encode())

# Fonction pour déchiffrer un mot de passe avec une clé donnée
def decrypt_password(key, encrypted_password):
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_password).decode()

# Fonction principale pour exécuter le programme
def main():
    display_welcome()
    key = register_master_password()
    while True:
        user_input = input(": ")
        if user_input == "add":
            add_password(key)
        elif user_input == "quit":
            break

if __name__ == "__main__":
    main()
