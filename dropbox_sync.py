#!/usr/bin/env python3
"""
Module de synchronisation avec Dropbox - Version Refresh Token
"""

import json
import os
import dropbox
from dropbox.exceptions import ApiError, AuthError

class DropboxSync:
    def __init__(self, config_file="config.json"):
        """Initialise la connexion Dropbox avec Refresh Token"""
        self.dbx = None
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration Dropbox avec Refresh Token"""
        try:
            # PRIORITÉ 1: Variables d'environnement (pour Render/production)
            env_app_key = os.environ.get('DROPBOX_APP_KEY')
            env_app_secret = os.environ.get('DROPBOX_APP_SECRET') 
            env_refresh_token = os.environ.get('DROPBOX_REFRESH_TOKEN')
            
            if all([env_app_key, env_app_secret, env_refresh_token]):
                print("🌍 Using Environment Variables (production)")
                self.dbx = dropbox.Dropbox(
                    oauth2_refresh_token=env_refresh_token,
                    app_key=env_app_key,
                    app_secret=env_app_secret
                )
                return
            
            # PRIORITÉ 2: Fichier config.json (pour développement local)
            if os.path.exists(self.config_file):
                print(f"📄 Reading config file: {self.config_file}")
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Nouvelle méthode : Refresh Token
                    app_key = config.get('app_key')
                    app_secret = config.get('app_secret')
                    refresh_token = config.get('refresh_token')
                    
                    if all([app_key, app_secret, refresh_token]):
                        print("🔄 Using Refresh Token from config.json")
                        self.dbx = dropbox.Dropbox(
                            oauth2_refresh_token=refresh_token,
                            app_key=app_key,
                            app_secret=app_secret
                        )
                        return
                    
                    # Ancienne méthode : Access Token (fallback)
                    access_token = config.get('dropbox_token')
                    if access_token:
                        print("⚠️  Using old Access Token (will expire)")
                        self.dbx = dropbox.Dropbox(access_token)
                        return
                    
                    print("❌ No valid Dropbox credentials in config.json")
            else:
                print("⚠️  Config file not found, creating template")
                self._create_config_template()
        
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            print("💡 Try using environment variables instead")
    
    def _create_config_template(self):
        """Crée un template de configuration avec Refresh Token"""
        config_template = {
            "app_key": "VOTRE_APP_KEY_ICI",
            "app_secret": "VOTRE_APP_SECRET_ICI", 
            "refresh_token": "VOTRE_REFRESH_TOKEN_ICI",
            "remote_path": "/passwords.db",
            "_comment": "Utilisez un Refresh Token pour une connexion permanente"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_template, f, indent=2)
        
        print(f"📄 Template {self.config_file} créé.")
        print("💡 Ajoutez vos credentials Dropbox (App Key, Secret, Refresh Token)")
    
    def test_connection(self):
        """Teste la connexion Dropbox"""
        if not self.dbx:
            return False
        
        try:
            account = self.dbx.users_get_current_account()
            print(f"✅ Connecté à Dropbox : {account.name.display_name}")
            print(f"📧 Email : {account.email}")
            return True
        except Exception as e:
            print(f"❌ Test de connexion échoué : {e}")
            return False
    
    def download(self, local_file, remote_path=None):
        """Télécharge un fichier depuis Dropbox"""
        if not self.dbx:
            print("❌ Dropbox non configuré")
            return False
        
        if remote_path is None:
            remote_path = f"/{local_file}"
        
        try:
            print(f"⬇️  Downloading {remote_path}...")
            with open(local_file, 'wb') as f:
                metadata, response = self.dbx.files_download(remote_path)
                f.write(response.content)
            print(f"✅ Downloaded {local_file} ({metadata.size} bytes)")
            return True
            
        except ApiError as e:
            if e.error.is_path_lookup() and e.error.get_path_lookup().is_not_found():
                # Fichier n'existe pas sur Dropbox, c'est normal pour le premier lancement
                print(f"ℹ️  File {remote_path} not found on Dropbox (first time?)")
                return False
            else:
                print(f"❌ Download API error: {e}")
                return False
        except AuthError as e:
            print(f"❌ Erreur d'authentification Dropbox: {e}")
            return False
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def upload(self, local_file, remote_path=None):
        """Upload un fichier vers Dropbox"""
        if not self.dbx:
            print("❌ Dropbox non configuré")
            return False
        
        if not os.path.exists(local_file):
            print(f"❌ Fichier local {local_file} introuvable")
            return False
        
        if remote_path is None:
            remote_path = f"/{local_file}"
        
        try:
            file_size = os.path.getsize(local_file)
            print(f"⬆️  Uploading {local_file} ({file_size} bytes)...")
            
            with open(local_file, 'rb') as f:
                file_content = f.read()
                
                # Upload avec overwrite
                result = self.dbx.files_upload(
                    file_content,
                    remote_path,
                    mode=dropbox.files.WriteMode('overwrite')
                )
            
            print(f"✅ Uploaded to {remote_path} (rev: {result.rev[:8]}...)")
            return True
            
        except AuthError as e:
            print(f"❌ Erreur d'authentification Dropbox: {e}")
            return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def list_files(self, folder_path=""):
        """Liste les fichiers dans un dossier Dropbox"""
        if not self.dbx:
            print("❌ Dropbox non configuré")
            return []
        
        try:
            print(f"📂 Listing files in '{folder_path}'...")
            result = self.dbx.files_list_folder(folder_path)
            
            files = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append({
                        'name': entry.name,
                        'size': entry.size,
                        'modified': entry.server_modified.isoformat()
                    })
                    print(f"  📄 {entry.name} ({entry.size} bytes)")
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    print(f"  📁 {entry.name}/")
            
            return files
            
        except Exception as e:
            print(f"❌ List files error: {e}")
            return []

# Test rapide si exécuté directement
if __name__ == "__main__":
    print("🧪 Test Dropbox Sync avec Refresh Token")
    print("=" * 50)
    
    sync = DropboxSync()
    
    if sync.test_connection():
        print("\n📂 Fichiers dans le dossier racine :")
        files = sync.list_files()
        
        if not files:
            print("  (aucun fichier)")
    else:
        print("\n💡 Pour configurer Dropbox :")
        print("1. Modifiez config.json avec vos credentials")
        print("2. Utilisez un Refresh Token pour une connexion permanente")