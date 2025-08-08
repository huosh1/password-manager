#!/usr/bin/env python3
"""
Module de synchronisation avec Dropbox
"""

import json
import os
import dropbox
from dropbox.exceptions import ApiError, AuthError

class DropboxSync:
    def __init__(self, config_file="config.json"):
        """Initialise la connexion Dropbox"""
        self.dbx = None
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration Dropbox"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('dropbox_token')
                    
                    if token:
                        self.dbx = dropbox.Dropbox(token)
                    else:
                        print("⚠️  Token Dropbox manquant dans config.json")
            else:
                print("⚠️  Fichier config.json introuvable")
                self._create_config_template()
        
        except Exception as e:
            print(f"⚠️  Erreur chargement config: {e}")
    
    def _create_config_template(self):
        """Crée un template de configuration"""
        config_template = {
            "dropbox_token": "VOTRE_TOKEN_DROPBOX_ICI",
            "remote_path": "/passwords.db"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_template, f, indent=2)
        
        print(f"📄 Template {self.config_file} créé. Ajoutez votre token Dropbox.")
    
    def download(self, local_file, remote_path=None):
        """Télécharge un fichier depuis Dropbox"""
        if not self.dbx:
            return False
        
        if remote_path is None:
            remote_path = f"/{local_file}"
        
        try:
            with open(local_file, 'wb') as f:
                metadata, response = self.dbx.files_download(remote_path)
                f.write(response.content)
            return True
            
        except ApiError as e:
            if e.error.is_path_lookup() and e.error.get_path_lookup().is_not_found():
                # Fichier n'existe pas sur Dropbox, c'est normal pour le premier lancement
                return False
            else:
                raise e
        except AuthError:
            print("❌ Erreur d'authentification Dropbox")
            return False
    
    def upload(self, local_file, remote_path=None):
        """Upload un fichier vers Dropbox"""
        if not self.dbx:
            return False
        
        if not os.path.exists(local_file):
            print(f"❌ Fichier local {local_file} introuvable")
            return False
        
        if remote_path is None:
            remote_path = f"/{local_file}"
        
        try:
            with open(local_file, 'rb') as f:
                file_content = f.read()
                
                # Upload avec overwrite
                self.dbx.files_upload(
                    file_content,
                    remote_path,
                    mode=dropbox.files.WriteMode('overwrite')
                )
            return True
            
        except AuthError:
            print("❌ Erreur d'authentification Dropbox")
            return False
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            return False