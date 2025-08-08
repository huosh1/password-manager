#!/usr/bin/env python3
"""
Module de chiffrement/déchiffrement avec Fernet
"""

import hashlib
import base64
from cryptography.fernet import Fernet

class PasswordCrypto:
    def __init__(self, master_password):
        """Initialise le chiffrement avec le master password"""
        self.fernet = self._create_fernet(master_password)
    
    def _create_fernet(self, password):
        """Crée une clé Fernet à partir du master password"""
        # Dérive une clé de 32 bytes à partir du mot de passe
        key_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            b'salt_for_password_manager',  # Salt fixe pour simplicité
            100000  # 100k itérations
        )
        
        # Encode en base64 pour Fernet
        key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(key)
    
    def encrypt(self, plaintext):
        """Chiffre un texte"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        encrypted = self.fernet.encrypt(plaintext)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, ciphertext):
        """Déchiffre un texte"""
        if isinstance(ciphertext, str):
            ciphertext = ciphertext.encode('utf-8')
        
        encrypted_data = base64.urlsafe_b64decode(ciphertext)
        decrypted = self.fernet.decrypt(encrypted_data)
        return decrypted.decode('utf-8')