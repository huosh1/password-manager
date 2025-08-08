#!/usr/bin/env python3
"""
Interface graphique minimaliste et aesthetic pour le gestionnaire de mots de passe
"""

import customtkinter as ctk
from tkinter import messagebox
import json
import os
import threading
import time
from crypto import PasswordCrypto
from dropbox_sync import DropboxSync
import secrets
import string
import pyperclip
import datetime
# Configuration du thème
ctk.set_appearance_mode("dark")  # "dark" ou "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ModernPasswordManager:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Password Manager")
        self.app.geometry("1000x700")
        self.app.minsize(900, 600)
        
        # Variables
        self.crypto = None
        self.dropbox = DropboxSync()
        self.passwords = {}
        self.db_file = "passwords.db"
        self.current_passwords = {}  # Pour le filtrage
        
        # Colors palette minimaliste
        self.colors = {
            'primary': '#1a1a1a',
            'secondary': '#2d2d2d', 
            'accent': '#4a9eff',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0',
            'success': '#00d4aa',
            'warning': '#ff6b6b',
            'background': '#0d1117'
        }
        
        # Interface
        self.create_login_interface()
        self.center_window()
    
    def center_window(self):
        """Centre la fenêtre"""
        self.app.update_idletasks()
        x = (self.app.winfo_screenwidth() // 2) - (self.app.winfo_width() // 2)
        y = (self.app.winfo_screenheight() // 2) - (self.app.winfo_height() // 2)
        self.app.geometry(f"+{x}+{y}")
    
    def clear_interface(self):
        """Efface l'interface"""
        for widget in self.app.winfo_children():
            widget.destroy()
    
    def create_login_interface(self):
        """Interface de connexion minimaliste"""
        self.clear_interface()
        
        # Container principal
        main_container = ctk.CTkFrame(self.app, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Logo et titre centré
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(expand=True, fill="both")
        
        # Logo simple
        logo_label = ctk.CTkLabel(
            header_frame,
            text="🔐",
            font=ctk.CTkFont(size=80)
        )
        logo_label.pack(pady=(100, 20))
        
        # Titre
        title_label = ctk.CTkLabel(
            header_frame,
            text="Password Manager",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Sous-titre
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Secure • Simple • Synchronized",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        subtitle_label.pack(pady=(0, 60))
        
        # Container de connexion
        login_container = ctk.CTkFrame(
            header_frame,
            width=400,
            height=200,
            corner_radius=20
        )
        login_container.pack(pady=20)
        login_container.pack_propagate(False)
        
        # Champ password
        self.master_password_entry = ctk.CTkEntry(
            login_container,
            placeholder_text="Master Password",
            show="●",
            width=300,
            height=50,
            font=ctk.CTkFont(size=16),
            corner_radius=15
        )
        self.master_password_entry.pack(pady=(40, 20))
        self.master_password_entry.focus()
        
        # Bouton de connexion
        self.login_button = ctk.CTkButton(
            login_container,
            text="Unlock",
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=15,
            command=self.authenticate
        )
        self.login_button.pack(pady=(0, 20))
        
        # Status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Enter your master password to continue",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(pady=(30, 0))
        
        # Bind Enter
        self.master_password_entry.bind('<Return>', lambda e: self.authenticate())
    
    def authenticate(self):
        """Authentification"""
        master_password = self.master_password_entry.get()
        
        if not master_password:
            self.show_status("Please enter your master password", "warning")
            return
        
        self.login_button.configure(state="disabled", text="Unlocking...")
        self.show_status("Authenticating...", "info")
        
        # Threading pour ne pas bloquer l'UI
        threading.Thread(target=self._auth_worker, args=(master_password,), daemon=True).start()
    
    def _auth_worker(self, master_password):
        """Worker d'authentification avec gestion premier lancement"""
        try:
            self.crypto = PasswordCrypto(master_password)
            
            # Sync Dropbox
            self.app.after(0, lambda: self.show_status("Syncing with Dropbox...", "info"))
            
            # Essayer de télécharger la base existante
            auth_token = None
            try:
                auth_token = self.load_database()
            except Exception as e:
                # Erreur de sync Dropbox - pas grave pour premier lancement
                print(f"Dropbox sync error (normal for first use): {e}")
            
            if auth_token:
                # Base existante trouvée - vérifier le master password
                try:
                    self.crypto.decrypt(auth_token)
                    # Master password correct
                    self.app.after(0, self.create_main_interface)
                except Exception:
                    # Master password incorrect
                    self.app.after(0, lambda: [
                        self.show_status("Incorrect master password", "error"),
                        self.login_button.configure(state="normal", text="Unlock")
                    ])
            else:
                # Pas de base existante - premier lancement
                self.app.after(0, lambda: self.show_status("Creating new database...", "info"))
                
                try:
                    # Créer le token d'authentification
                    token = self.crypto.encrypt("AUTH_VALID")
                    
                    # Initialiser une base vide
                    self.passwords = {}
                    
                    # Sauvegarder la nouvelle base
                    self.save_database(token)
                    
                    # Aller à l'interface principale
                    self.app.after(0, lambda: [
                        self.show_status("Database created successfully!", "success"),
                        self.create_main_interface
                    ])
                    
                    # Petit délai puis interface
                    self.app.after(1500, self.create_main_interface)
                    
                except Exception as create_error:
                    self.app.after(0, lambda: [
                        self.show_status(f"Error creating database: {str(create_error)}", "error"),
                        self.login_button.configure(state="normal", text="Unlock")
                    ])
                    
        except Exception as e:
            self.app.after(0, lambda: [
                self.show_status(f"Authentication error: {str(e)}", "error"),
                self.login_button.configure(state="normal", text="Unlock")
            ])
    
    def show_status(self, message, status_type="info"):
        """Affiche un status avec couleur"""
        colors = {
            "info": self.colors['text_secondary'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['warning']
        }
        
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message, text_color=colors.get(status_type, colors["info"]))
    
    def load_database(self):
        """Charge la base de données avec gestion robuste des erreurs"""
        try:
            # Essayer de télécharger depuis Dropbox
            download_success = self.dropbox.download(self.db_file)
            
            if download_success:
                print("✅ Database downloaded from Dropbox")
            else:
                print("ℹ️  No existing database on Dropbox (normal for first use)")
                
        except Exception as dropbox_error:
            print(f"⚠️  Dropbox error (not critical): {dropbox_error}")
            # Continuer même si Dropbox échoue
        
        # Essayer de charger le fichier local
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Vérifier la structure du fichier
                    if isinstance(data, dict):
                        self.passwords = data.get('passwords', {})
                        auth_token = data.get('auth_token')
                        
                        if auth_token:
                            print("✅ Existing database loaded")
                            return auth_token
                        else:
                            print("⚠️  Database exists but no auth token found")
                    else:
                        print("⚠️  Invalid database format")
                        
            except json.JSONDecodeError:
                print("⚠️  Corrupted database file, will create new one")
            except Exception as file_error:
                print(f"⚠️  Error reading database: {file_error}")
        else:
            print("ℹ️  No local database found")
        
        # Aucune base valide trouvée
        return None
     # ✅ AJOUTEZ CETTE NOUVELLE MÉTHODE (après load_database)
    def create_dropbox_backup(self):
        """Crée un backup horodaté sur Dropbox"""
        if not os.path.exists(self.db_file):
            return False
        
        try:
            # Nom du backup avec date et heure
            now = datetime.datetime.now()
            backup_name = f"passwords-{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            
            # Upload du backup sur Dropbox
            success = self.dropbox.upload(self.db_file, f"/{backup_name}")
            if success:
                print(f"📦 Backup créé sur Dropbox: {backup_name}")
                return True
            else:
                print("⚠️  Backup Dropbox échoué")
                return False
                
        except Exception as e:
            print(f"⚠️  Backup warning: {e}")
            return False
    
    # ✅ MODIFIEZ CETTE MÉTHODE EXISTANTE (vers ligne 200)
    def save_database(self, auth_token):
        """Sauvegarde la base avec gestion d'erreurs robuste"""
        try:
            data = {
                'auth_token': auth_token,
                'passwords': self.passwords
            }
            
            # Sauvegarder localement d'abord
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Database saved locally")
            
            # Upload vers Dropbox en arrière-plan
            threading.Thread(target=self._upload_worker, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            raise e
  
    def _upload_worker(self):
        """Upload vers Dropbox en arrière-plan avec retry"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                success = self.dropbox.upload(self.db_file)
                if success:
                    print("✅ Database uploaded to Dropbox")
                    
                    # ✅ NOUVEAU : Backup automatique
                    self.create_dropbox_backup()
                    return
                else:
                    print(f"⚠️  Upload attempt {attempt + 1} failed")
                    
            except Exception as e:
                print(f"⚠️  Upload attempt {attempt + 1} error: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        print("❌ All upload attempts failed (database saved locally only)")
        
    def create_main_interface(self):
        """Interface principale minimaliste"""
        self.clear_interface()
        
        # Layout en grid
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_rowconfigure(1, weight=1)
        
        # Header bar
        self.create_header()
        
        # Main content
        self.create_main_content()
        
        # Populate passwords
        self.refresh_passwords()
    
    def create_header(self):
        """Header minimaliste"""
        header = ctk.CTkFrame(self.app, height=80, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        # Container pour centrer le contenu
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Titre à gauche
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🔐 Passwords",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Actions à droite
        actions_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        actions_frame.pack(side="right", fill="y")
        
        # Bouton nouveau
        new_button = ctk.CTkButton(
            actions_frame,
            text="+ New",
            width=80,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            command=self.add_password
        )
        new_button.pack(side="right", padx=(10, 0))
        
        # Bouton logout
        logout_button = ctk.CTkButton(
            actions_frame,
            text="Logout",
            width=70,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            text_color=self.colors['text_secondary'],
            command=self.logout
        )
        logout_button.pack(side="right", padx=(10, 0))
    
    def create_main_content(self):
        """Contenu principal"""
        # Container principal
        main_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Search bar
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=60)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        search_frame.grid_propagate(False)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search passwords...",
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=20
        )
        self.search_entry.pack(fill="x", pady=10)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Passwords container
        self.passwords_frame = ctk.CTkScrollableFrame(
            main_frame,
            corner_radius=15,
            fg_color=("#f0f0f0", "#1a1a1a")
        )
        self.passwords_frame.grid(row=1, column=0, sticky="nsew")
        self.passwords_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_passwords(self, filter_text=""):
        """Actualise la liste des mots de passe"""
        # Clear existing
        for widget in self.passwords_frame.winfo_children():
            widget.destroy()
        
        # Filter passwords
        filtered = {}
        for account, data in self.passwords.items():
            if filter_text.lower() in account.lower():
                filtered[account] = data
        
        if not filtered:
            # Empty state
            empty_label = ctk.CTkLabel(
                self.passwords_frame,
                text="No passwords found\n\nClick '+ New' to add your first password",
                font=ctk.CTkFont(size=16),
                text_color=self.colors['text_secondary']
            )
            empty_label.pack(pady=100)
            return
        
        # Create password cards
        for i, (account, encrypted_data) in enumerate(filtered.items()):
            try:
                decrypted = json.loads(self.crypto.decrypt(encrypted_data))
                self.create_password_card(account, decrypted, i)
            except:
                continue
    
    def create_password_card(self, account, data, index):
        """Crée une carte de mot de passe minimaliste"""
        # Card container
        card = ctk.CTkFrame(
            self.passwords_frame,
            height=80,
            corner_radius=12,
            fg_color=("#ffffff", "#2d2d2d")
        )
        card.pack(fill="x", padx=10, pady=5)
        card.pack_propagate(False)
        
        # Click binding
        card.bind("<Button-1>", lambda e: self.show_password_details(account, data))
        
        # Content frame
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Left side - Info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Account name
        account_label = ctk.CTkLabel(
            info_frame,
            text=account,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        account_label.pack(anchor="w")
        
        # Username
        username_label = ctk.CTkLabel(
            info_frame,
            text=data.get('username', ''),
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary'],
            anchor="w"
        )
        username_label.pack(anchor="w")
        
        # Right side - Actions
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.pack(side="right", fill="y")
        
        # Copy password button
        copy_btn = ctk.CTkButton(
            actions_frame,
            text="📋",
            width=40,
            height=30,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#e0e0e0", "#404040"),
            command=lambda: self.copy_password(data['password'])
        )
        copy_btn.pack(side="right", padx=(5, 0))
        
        # Edit button
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=40,
            height=30,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#e0e0e0", "#404040"),
            command=lambda: self.edit_password(account, data)
        )
        edit_btn.pack(side="right", padx=(5, 0))
    
    def copy_password(self, password):
        """Copie le mot de passe"""
        try:
            pyperclip.copy(password)
            self.show_toast("Password copied!")
        except:
            # Fallback pour les systèmes sans pyperclip
            self.app.clipboard_clear()
            self.app.clipboard_append(password)
            self.show_toast("Password copied!")
    
    def show_toast(self, message, toast_type="success"):
        """Affiche un toast minimaliste amélioré"""
        # Couleurs selon le type
        colors = {
            "success": self.colors['success'],
            "error": self.colors['warning'],
            "info": self.colors['accent']
        }
        
        toast = ctk.CTkFrame(
            self.app,
            fg_color=colors.get(toast_type, colors["success"]),
            corner_radius=10,
            width=300,
            height=50
        )
        toast.place(relx=0.5, rely=0.85, anchor="center")
        toast.pack_propagate(False)
        
        # Message
        toast_label = ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        )
        toast_label.pack(expand=True)
        
        # Auto-hide après 3s
        def hide_toast():
            try:
                toast.destroy()
            except:
                pass
        
        self.app.after(3000, hide_toast)
    
    def on_search(self, event):
        """Event de recherche"""
        filter_text = self.search_entry.get()
        self.refresh_passwords(filter_text)
    
    def show_password_details(self, account, data):
        """Affiche les détails du mot de passe"""
        self.create_details_window(account, data)
    
    def create_details_window(self, account, data):
        """Fenêtre de détails minimaliste"""
        window = ctk.CTkToplevel(self.app)
        window.title(account)
        window.geometry("450x350")
        window.resizable(False, False)
        window.transient(self.app)
        window.grab_set()
        
        # Center window
        window.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (window.winfo_width() // 2)
        y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")
        
        # Main container
        main_frame = ctk.CTkFrame(window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=account,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))
        
        # Fields
        fields = [
            ("Username", data.get('username', '')),
            ("Password", data.get('password', '')),
            ("Notes", data.get('notes', ''))
        ]
        
        for label_text, value in fields:
            if not value and label_text == "Notes":
                continue
                
            # Label
            label = ctk.CTkLabel(
                main_frame,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            label.pack(fill="x", pady=(10, 5))
            
            # Value frame
            value_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            value_frame.pack(fill="x", pady=(0, 10))
            
            # Entry/textbox
            if label_text == "Notes":
                value_widget = ctk.CTkTextbox(
                    value_frame,
                    height=60,
                    font=ctk.CTkFont(size=12)
                )
                value_widget.pack(fill="x")
                value_widget.insert("1.0", value)
                value_widget.configure(state="disabled")
            else:
                value_entry = ctk.CTkEntry(
                    value_frame,
                    font=ctk.CTkFont(size=12),
                    height=35
                )
                value_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
                value_entry.insert(0, value)
                value_entry.configure(state="readonly")
                
                if label_text == "Password":
                    value_entry.configure(show="●")
                
                # Copy button
                copy_btn = ctk.CTkButton(
                    value_frame,
                    text="Copy",
                    width=60,
                    height=35,
                    font=ctk.CTkFont(size=11),
                    command=lambda v=value: self.copy_password(v)
                )
                copy_btn.pack(side="right")
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            height=40,
            corner_radius=10,
            command=window.destroy
        )
        close_btn.pack(pady=(20, 0))
    
    def add_password(self):
        """Ajoute un nouveau mot de passe"""
        self.create_password_form()
    
    def edit_password(self, account, data):
        """Modifie un mot de passe"""
        self.create_password_form(account, data)
    
    def create_password_form(self, account=None, data=None):
        """Formulaire minimaliste"""
        window = ctk.CTkToplevel(self.app)
        window.title("New Password" if not account else f"Edit {account}")
        window.geometry("500x500")
        window.resizable(False, False)
        window.transient(self.app)
        window.grab_set()
        
        # Center
        window.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (window.winfo_width() // 2)
        y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")
        
        # Container
        main_frame = ctk.CTkFrame(window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title = "New Password" if not account else f"Edit {account}"
        title_label = ctk.CTkLabel(
            main_frame,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))
        
        # Form fields
        fields_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        fields_frame.pack(fill="x", pady=(0, 30))
        
        # Account name
        account_label = ctk.CTkLabel(fields_frame, text="Account Name", anchor="w")
        account_label.pack(fill="x", pady=(0, 5))
        
        account_entry = ctk.CTkEntry(
            fields_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        account_entry.pack(fill="x", pady=(0, 20))
        if account:
            account_entry.insert(0, account)
        
        # Username
        username_label = ctk.CTkLabel(fields_frame, text="Username", anchor="w")
        username_label.pack(fill="x", pady=(0, 5))
        
        username_entry = ctk.CTkEntry(
            fields_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        username_entry.pack(fill="x", pady=(0, 20))
        if data:
            username_entry.insert(0, data.get('username', ''))
        
        # Password
        password_label = ctk.CTkLabel(fields_frame, text="Password", anchor="w")
        password_label.pack(fill="x", pady=(0, 5))
        
        password_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 20))
        
        password_entry = ctk.CTkEntry(
            password_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        password_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if data:
            password_entry.insert(0, data.get('password', ''))
        
        generate_btn = ctk.CTkButton(
            password_frame,
            text="Generate",
            width=80,
            height=40,
            corner_radius=10,
            command=lambda: self.generate_and_set_password(password_entry)
        )
        generate_btn.pack(side="right")
        
        # Notes
        notes_label = ctk.CTkLabel(fields_frame, text="Notes", anchor="w")
        notes_label.pack(fill="x", pady=(0, 5))
        
        notes_textbox = ctk.CTkTextbox(
            fields_frame,
            height=80,
            font=ctk.CTkFont(size=12),
            corner_radius=10
        )
        notes_textbox.pack(fill="x", pady=(0, 20))
        if data:
            notes_textbox.insert("1.0", data.get('notes', ''))
        
        # Buttons - Layout amélioré
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        # Bouton Save plus visible à gauche
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Password",
            height=45,
            width=200,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.save_password_form(
                window, account, account_entry, username_entry, password_entry, notes_textbox
            )
        )
        save_btn.pack(side="left")
        
        # Bouton Cancel à droite
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancel",
            height=45,
            width=120,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=window.destroy
        )
        cancel_btn.pack(side="right")
        
        # Focus sur le premier champ vide
        if not account:
            account_entry.focus()
        elif not data:
            username_entry.focus()
        
        # Bind Enter key pour valider
        def on_enter(event):
            self.save_password_form(
                window, account, account_entry, username_entry, password_entry, notes_textbox
            )
        
        # Bind Enter sur tous les champs sauf notes
        account_entry.bind('<Return>', on_enter)
        username_entry.bind('<Return>', on_enter)
        password_entry.bind('<Return>', on_enter)
        
        # Bind Escape pour annuler
        window.bind('<Escape>', lambda e: window.destroy())
    
    def generate_and_set_password(self, entry):
        """Génère et définit un mot de passe"""
        password = self.generate_password()
        entry.delete(0, "end")
        entry.insert(0, password)
    
    def generate_password(self, length=16):
        """Génère un mot de passe"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def save_password_form(self, window, original_account, account_entry, username_entry, password_entry, notes_textbox):
        """Sauvegarde le formulaire avec validation améliorée"""
        account = account_entry.get().strip()
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        notes = notes_textbox.get("1.0", "end").strip()
        
        # Validation avec feedback visuel
        if not account:
            account_entry.configure(border_color="red")
            self.show_toast("Account name is required!")
            account_entry.focus()
            return
        
        if not username:
            username_entry.configure(border_color="red")
            self.show_toast("Username is required!")
            username_entry.focus()
            return
        
        if not password:
            password_entry.configure(border_color="red")
            self.show_toast("Password is required!")
            password_entry.focus()
            return
        
        # Reset border colors
        account_entry.configure(border_color=("gray60", "gray40"))
        username_entry.configure(border_color=("gray60", "gray40"))
        password_entry.configure(border_color=("gray60", "gray40"))
        
        # Check if account exists
        if not original_account and account in self.passwords:
            account_entry.configure(border_color="red")
            self.show_toast("Account already exists!")
            account_entry.focus()
            return
        
        # Remove old account if renamed
        if original_account and original_account != account:
            if account in self.passwords:
                account_entry.configure(border_color="red")
                self.show_toast("An account with this name already exists!")
                account_entry.focus()
                return
            del self.passwords[original_account]
        
        # Show saving feedback
        save_btn = None
        for widget in window.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkButton) and "Save" in grandchild.cget("text"):
                                save_btn = grandchild
                                break
        
        if save_btn:
            save_btn.configure(text="💾 Saving...", state="disabled")
            window.update()
        
        try:
            # Save
            data = {
                'username': username,
                'password': password,
                'notes': notes
            }
            
            encrypted_data = self.crypto.encrypt(json.dumps(data))
            self.passwords[account] = encrypted_data
            
            auth_token = self.crypto.encrypt("AUTH_VALID")
            self.save_database(auth_token)
            
            # Refresh the passwords list
            self.refresh_passwords()
            
            # Close window
            window.destroy()
            
            # Show success
            action = "added" if not original_account else "updated"
            self.show_toast(f"Password {action} successfully!")
            
        except Exception as e:
            if save_btn:
                save_btn.configure(text="💾 Save Password", state="normal")
            self.show_toast(f"Error: {str(e)}")
            print(f"Error saving password: {e}")
    
    def logout(self):
        """Déconnexion"""
        self.crypto = None
        self.passwords = {}
        self.create_login_interface()
    
    def run(self):
        """Lance l'application"""
        self.app.mainloop()

if __name__ == "__main__":
    app = ModernPasswordManager()
    app.run()