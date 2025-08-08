#!/usr/bin/env python3
"""
Application Flask PWA CORRIGÉE - Version finale compatible Flask 2.3.3
"""

from flask import Flask, render_template_string, request, jsonify, session, Response
import json
import os
import sys
from crypto import PasswordCrypto
from dropbox_sync import DropboxSync
import secrets
import string
import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

class PWAPasswordManager:
    def __init__(self):
        self.dropbox = DropboxSync()
        self.db_file = "passwords.db"
     # ✅ AJOUTEZ CETTE NOUVELLE MÉTHODE
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
    
    
        
    def authenticate(self, master_password):
        """Authentification robuste"""
        try:
            crypto = PasswordCrypto(master_password)
            
            # Sync Dropbox avec gestion d'erreurs
            try:
                download_success = self.dropbox.download(self.db_file)
                if download_success:
                    print("✅ Database downloaded from Dropbox")
            except Exception as e:
                print(f"⚠️  Dropbox sync warning: {e}")
            
            auth_token = None
            
            if os.path.exists(self.db_file):
                try:
                    with open(self.db_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        auth_token = data.get('auth_token')
                        
                        if auth_token:
                            crypto.decrypt(auth_token)
                            session['authenticated'] = True
                            session['master_password'] = master_password
                            return {"success": True, "passwords": data.get('passwords', {})}
                            
                except Exception as e:
                    if "decrypt" in str(e).lower():
                        return {"success": False, "error": "Incorrect master password"}
                    print(f"Database error: {e}")
            
            # Premier lancement
            print("Creating new database...")
            token = crypto.encrypt("AUTH_VALID")
            self.save_database(token, {})
            session['authenticated'] = True
            session['master_password'] = master_password
            return {"success": True, "passwords": {}, "first_time": True}
            
        except Exception as e:
            print(f"Auth error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_crypto(self):
        if not session.get('authenticated'):
            return None
        return PasswordCrypto(session['master_password'])
    
    def load_passwords(self):
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('passwords', {})
        except Exception as e:
            print(f"Error loading passwords: {e}")
        return {}
    
    # ✅ MODIFIEZ CETTE MÉTHODE EXISTANTE
    def save_database(self, auth_token, passwords):
        try:
            data = {
                'auth_token': auth_token,
                'passwords': passwords
            }
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Database saved locally")
            
            try:
                # Upload principal
                success = self.dropbox.upload(self.db_file)
                if success:
                    print("✅ Uploaded to Dropbox")
                    
                    # ✅ NOUVEAU : Backup automatique
                    self.create_dropbox_backup()
                    
            except Exception as e:
                print(f"⚠️  Dropbox upload warning: {e}")
        
        except Exception as e:
            print(f"Save error: {e}")
            raise e
    
    def generate_password(self, length=16):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))

# Instance globale
manager = PWAPasswordManager()

def init_static_files():
    """Initialise les fichiers statiques nécessaires"""
    try:
        if not os.path.exists('static'):
            os.makedirs('static')
            print("📁 Created static folder")
        
        # Créer manifest.json
        manifest = {
            "name": "Password Manager",
            "short_name": "Passwords",
            "description": "Secure password manager with AES encryption",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1a1a1a",
            "theme_color": "#4a9eff",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgdmlld0JveD0iMCAwIDE5MiAxOTIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIiByeD0iNDAiIGZpbGw9IiM0YTllZmYiLz4KPHN2ZyB4PSI0OCIgeT0iNDgiIHdpZHRoPSI5NiIgaGVpZ2h0PSI5NiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CjxwYXRoIGQ9Ik0xOCAxMGgtMVY2YzAtMi43Ni0yLjI0LTUtNS01UzIgMy4yNCAyIDZ2NGgtMWMtMS4xIDAtMiAuOS0yIDJ2MTBjMCAxLjEuOSAyIDIgMmgxNmMxLjEgMCAyLS45IDItMlYxMmMwLTEuMS0uOS0yLTItMnpNOC45IDZjMC0xLjcxIDEuMzktMy4xIDMuMS0zLjFzMy4xIDEuMzkgMy4xIDMuMXY0SDguOVY2eiIvPgo8L3N2Zz4KPC9zdmc+",
                    "sizes": "192x192",
                    "type": "image/svg+xml"
                }
            ]
        }
        
        manifest_path = os.path.join('static', 'manifest.json')
        if not os.path.exists(manifest_path):
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            print("📄 Created manifest.json")
            
    except Exception as e:
        print(f"Init static files error: {e}")

# Templates intégrés
LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#4a9eff">
    <title>🔐 Password Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white; min-height: 100vh;
            display: flex; align-items: center; justify-content: center; padding: 20px;
        }
        .container { width: 100%; max-width: 400px; text-align: center; }
        .logo { font-size: 4rem; margin-bottom: 1rem; }
        .title { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
        .subtitle { color: #b0b0b0; margin-bottom: 3rem; }
        .login-form {
            background: rgba(45, 45, 45, 0.9); padding: 2rem; border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .input-group { margin-bottom: 1.5rem; }
        input[type="password"] {
            width: 100%; padding: 1.2rem; border: none; border-radius: 15px;
            background: rgba(255, 255, 255, 0.1); color: white; font-size: 1.1rem;
            outline: none; transition: all 0.3s ease;
        }
        input::placeholder { color: #b0b0b0; }
        input:focus { background: rgba(255, 255, 255, 0.15); box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.5); }
        .btn {
            width: 100%; padding: 1.2rem; border: none; border-radius: 15px;
            background: linear-gradient(135deg, #4a9eff 0%, #3d8bdb 100%);
            color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn:hover:not(:disabled) { transform: translateY(-2px); }
        .btn:disabled { background: #666; cursor: not-allowed; }
        .status {
            margin-top: 1.5rem; padding: 1rem; border-radius: 12px; font-size: 0.95rem;
            opacity: 0; transition: all 0.3s ease;
        }
        .status.show { opacity: 1; }
        .status.error { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }
        .status.loading { background: rgba(74, 158, 255, 0.15); color: #4a9eff; }
        .status.success { background: rgba(0, 212, 170, 0.15); color: #00d4aa; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔐</div>
        <h1 class="title">Password Manager</h1>
        <p class="subtitle">Secure • Simple • Synchronized</p>
        
        <form class="login-form" id="loginForm">
            <div class="input-group">
                <input type="password" id="masterPassword" placeholder="Master Password" required />
            </div>
            <button type="submit" class="btn" id="loginBtn">🔓 Unlock</button>
            <div id="status" class="status"></div>
        </form>
    </div>

    <script>
        function showStatus(message, type = 'loading') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type + ' show';
        }
        
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const password = document.getElementById('masterPassword').value.trim();
            const btn = document.getElementById('loginBtn');
            
            if (!password) {
                showStatus('Please enter your master password', 'error');
                return;
            }
            
            btn.disabled = true;
            btn.textContent = '🔄 Unlocking...';
            showStatus('Authenticating...', 'loading');
            
            try {
                const response = await fetch('/api/auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ master_password: password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Welcome! 🎉', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showStatus(result.error || 'Authentication failed', 'error');
                }
            } catch (error) {
                showStatus('Connection error', 'error');
                console.error('Auth error:', error);
            } finally {
                btn.disabled = false;
                btn.textContent = '🔓 Unlock';
            }
        });
        
        document.getElementById('masterPassword').focus();
    </script>
</body>
</html>'''

MAIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#4a9eff">
    <link rel="manifest" href="/static/manifest.json">
    <title>🔐 My Passwords</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a1a; color: white; line-height: 1.6; min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
            padding: 1rem; display: flex; justify-content: space-between; align-items: center;
            position: sticky; top: 0; z-index: 100; border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .header h1 { font-size: 1.5rem; font-weight: 700; }
        .header-actions { display: flex; gap: 0.75rem; }
        .btn-sm {
            padding: 0.5rem 1rem; border: none; border-radius: 10px;
            background: linear-gradient(135deg, #4a9eff 0%, #3d8bdb 100%);
            color: white; font-size: 0.9rem; font-weight: 600; cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-sm:hover { transform: translateY(-2px); }
        .btn-outline { background: transparent; border: 2px solid rgba(255, 255, 255, 0.2); color: #b0b0b0; }
        .btn-outline:hover { background: rgba(255, 255, 255, 0.1); color: white; }
        .container { padding: 1rem; max-width: 800px; margin: 0 auto; }
        .search-bar { position: relative; margin-bottom: 1.5rem; }
        .search-input {
            width: 100%; padding: 1rem 1rem 1rem 3rem; border: none; border-radius: 15px;
            background: rgba(45, 45, 45, 0.8); color: white; font-size: 1rem; outline: none;
        }
        .search-icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: #b0b0b0; }
        .password-list { display: flex; flex-direction: column; gap: 1rem; }
        .password-card {
            background: rgba(45, 45, 45, 0.9); border-radius: 15px; padding: 1.25rem;
            cursor: pointer; transition: all 0.3s ease; border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .password-card:hover { border-color: #4a9eff; transform: translateY(-2px); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .card-title { font-size: 1.2rem; font-weight: 600; }
        .card-actions { display: flex; gap: 0.5rem; opacity: 0; transition: opacity 0.3s ease; }
        .password-card:hover .card-actions { opacity: 1; }
        .btn-icon {
            width: 36px; height: 36px; border: none; border-radius: 8px;
            background: rgba(255, 255, 255, 0.1); color: white; cursor: pointer;
            display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;
        }
        .btn-icon:hover { background: rgba(74, 158, 255, 0.3); }
        .card-username { color: #b0b0b0; font-size: 0.95rem; }
        .empty-state { text-align: center; padding: 4rem 1rem; color: #b0b0b0; }
        .empty-state .icon { font-size: 4rem; margin-bottom: 1rem; }
        .fab {
            position: fixed; bottom: 2rem; right: 2rem; width: 60px; height: 60px;
            border-radius: 50%; background: linear-gradient(135deg, #4a9eff 0%, #3d8bdb 100%);
            border: none; color: white; font-size: 1.5rem; cursor: pointer;
        }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.8); z-index: 2000; }
        .modal.show { display: flex; align-items: center; justify-content: center; }
        .modal-content { background: #2d2d2d; border-radius: 20px; padding: 2rem; width: 90%; max-width: 500px; }
        .modal-header { display: flex; justify-content: space-between; margin-bottom: 2rem; }
        .btn-close { background: none; border: none; color: #b0b0b0; font-size: 1.5rem; cursor: pointer; }
        .form-group { margin-bottom: 1.5rem; }
        .form-label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        .form-input {
            width: 100%; padding: 1rem; border: none; border-radius: 12px;
            background: rgba(255, 255, 255, 0.1); color: white; font-size: 1rem; outline: none;
        }
        .input-group { display: flex; gap: 0.75rem; }
        .btn { padding: 1rem 2rem; border: none; border-radius: 12px; background: #4a9eff; color: white; font-weight: 600; cursor: pointer; }
        .toast { position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); background: #00d4aa; color: white; padding: 1rem 2rem; border-radius: 12px; z-index: 3000; }
        .toast.error { background: #ff6b6b; }
    </style>
</head>
<body>
    <header class="header">
        <h1>🔐 Passwords</h1>
        <div class="header-actions">
            <button class="btn-sm" onclick="openAddModal()">+ New</button>
            <button class="btn-sm btn-outline" onclick="logout()">Logout</button>
        </div>
    </header>
    
    <div class="container">
        <div class="search-bar">
            <span class="search-icon">🔍</span>
            <input type="text" class="search-input" id="searchInput" placeholder="Search passwords..." oninput="filterPasswords()" />
        </div>
        <div class="password-list" id="passwordList">Loading...</div>
    </div>
    
    <button class="fab" onclick="openAddModal()">+</button>
    
    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Password</h2>
                <button class="btn-close" onclick="closeModal()">&times;</button>
            </div>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let passwords = {};
        
        async function loadPasswords() {
            try {
                const response = await fetch('/api/passwords');
                const result = await response.json();
                
                if (result.success) {
                    passwords = result.passwords;
                    renderPasswords();
                } else {
                    document.getElementById('passwordList').innerHTML = '<div class="empty-state"><div class="icon">🔐</div><p>No passwords yet. Click + to add one!</p></div>';
                }
            } catch (error) {
                console.error('Load error:', error);
                showToast('Connection error', 'error');
            }
        }
        
        function renderPasswords(filter = '') {
            const list = document.getElementById('passwordList');
            const filtered = Object.entries(passwords).filter(([account]) => 
                account.toLowerCase().includes(filter.toLowerCase())
            );
            
            if (filtered.length === 0) {
                list.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>No passwords found</p></div>';
                return;
            }
            
            list.innerHTML = filtered.map(([account, data]) => `
                <div class="password-card" onclick="viewPassword('${escapeHtml(account)}')">
                    <div class="card-header">
                        <div class="card-title">${escapeHtml(account)}</div>
                        <div class="card-actions" onclick="event.stopPropagation()">
                            <button class="btn-icon" onclick="copyPassword('${escapeHtml(account)}')" title="Copy Password">📋</button>
                            <button class="btn-icon" onclick="editPassword('${escapeHtml(account)}')" title="Edit">✏️</button>
                        </div>
                    </div>
                    <div class="card-username">${escapeHtml(data.username)}</div>
                </div>
            `).join('');
        }
        
        function filterPasswords() {
            renderPasswords(document.getElementById('searchInput').value);
        }
        
        async function copyPassword(account) {
            const password = passwords[account].password;
            
            try {
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(password);
                    showToast('Password copied! 📋');
                } else {
                    const textarea = document.createElement('textarea');
                    textarea.value = password;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    showToast('Password copied! 📋');
                }
            } catch (error) {
                console.error('Copy failed:', error);
                showToast('Copy failed', 'error');
            }
        }
        
        function viewPassword(account) {
            const data = passwords[account];
            document.getElementById('modalTitle').textContent = account;
            document.getElementById('modalContent').innerHTML = `
                <div class="form-group">
                    <label class="form-label">Username</label>
                    <div class="input-group">
                        <input type="text" class="form-input" value="${escapeHtml(data.username)}" readonly>
                        <button class="btn-sm" onclick="copyText('${escapeHtml(data.username)}', 'Username copied!')">📋</button>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <div class="input-group">
                        <input type="text" class="form-input" value="${escapeHtml(data.password)}" readonly style="font-family: monospace;">
                        <button class="btn-sm" onclick="copyText('${escapeHtml(data.password)}', 'Password copied!')">📋</button>
                    </div>
                </div>
                ${data.notes ? `
                    <div class="form-group">
                        <label class="form-label">Notes</label>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; font-size: 0.9rem;">
                            ${escapeHtml(data.notes)}
                        </div>
                    </div>
                ` : ''}
                <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                    <button class="btn" onclick="editPassword('${escapeHtml(account)}')">✏️ Edit</button>
                    <button class="btn-sm btn-outline" onclick="closeModal()">Close</button>
                </div>
            `;
            document.getElementById('modal').classList.add('show');
        }
        
        async function copyText(text, successMessage = 'Copied!') {
            try {
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(text);
                } else {
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                }
                showToast(successMessage);
            } catch (error) {
                console.error('Copy error:', error);
                showToast('Copy failed', 'error');
            }
        }
        
        function openAddModal() {
            document.getElementById('modalTitle').textContent = 'New Password';
            document.getElementById('modalContent').innerHTML = `
                <form onsubmit="return savePassword(event)">
                    <div class="form-group">
                        <label class="form-label">Account</label>
                        <input type="text" class="form-input" id="account" required placeholder="e.g. Gmail, Facebook">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-input" id="username" required placeholder="Your username or email">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <div class="input-group">
                            <input type="text" class="form-input" id="password" required style="font-family: monospace;" placeholder="Enter or generate password">
                            <button type="button" class="btn-sm" onclick="generatePassword()" title="Generate">🎲</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Notes (optional)</label>
                        <input type="text" class="form-input" id="notes" placeholder="Additional notes">
                    </div>
                    <button type="submit" class="btn">Save Password</button>
                </form>
            `;
            document.getElementById('modal').classList.add('show');
            setTimeout(() => document.getElementById('account').focus(), 100);
        }
        
        function editPassword(account) {
            const data = passwords[account];
            document.getElementById('modalTitle').textContent = 'Edit ' + account;
            document.getElementById('modalContent').innerHTML = `
                <form onsubmit="return savePassword(event, '${escapeHtml(account)}')">
                    <div class="form-group">
                        <label class="form-label">Account</label>
                        <input type="text" class="form-input" id="account" value="${escapeHtml(account)}" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-input" id="username" value="${escapeHtml(data.username)}" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <div class="input-group">
                            <input type="text" class="form-input" id="password" value="${escapeHtml(data.password)}" required style="font-family: monospace;">
                            <button type="button" class="btn-sm" onclick="generatePassword()">🎲</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Notes</label>
                        <input type="text" class="form-input" id="notes" value="${escapeHtml(data.notes || '')}">
                    </div>
                    <button type="submit" class="btn">Update Password</button>
                </form>
            `;
            document.getElementById('modal').classList.add('show');
        }
        
        async function savePassword(event, originalAccount) {
            event.preventDefault();
            
            const account = document.getElementById('account').value.trim();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const notes = document.getElementById('notes').value.trim();
            
            if (!account || !username || !password) {
                showToast('Please fill all required fields', 'error');
                return false;
            }
            
            try {
                const response = await fetch('/api/passwords', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account, username, password, notes })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('Password saved! 🎉');
                    closeModal();
                    loadPasswords();
                } else {
                    showToast(result.error || 'Save failed', 'error');
                }
            } catch (error) {
                console.error('Save error:', error);
                showToast('Save failed', 'error');
            }
            
            return false;
        }
        
        async function generatePassword() {
            try {
                const response = await fetch('/api/generate-password');
                const result = await response.json();
                if (result.success) {
                    document.getElementById('password').value = result.password;
                    showToast('Password generated! 🎲');
                }
            } catch (error) {
                // Fallback local generation
                const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
                let password = '';
                for (let i = 0; i < 16; i++) {
                    password += chars.charAt(Math.floor(Math.random() * chars.length));
                }
                document.getElementById('password').value = password;
                showToast('Password generated! 🎲');
            }
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('show');
        }
        
        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                showToast('Logged out');
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                location.reload();
            }
        }
        
        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 3000);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }
        
        // Initialiser au chargement
        loadPasswords();
        
        // Gestion du clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>'''

# Routes principales
@app.route('/')
def index():
    """Route principale CORRIGÉE"""
    try:
        # Initialiser les fichiers statiques dès la première requête
        init_static_files()
        
        if session.get('authenticated'):
            return render_template_string(MAIN_HTML)
        else:
            return render_template_string(LOGIN_HTML)
    except Exception as e:
        print(f"Route error: {e}")
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """API authentification"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data"})
        
        master_password = data.get('master_password', '').strip()
        if not master_password:
            return jsonify({"success": False, "error": "Password required"})
        
        result = manager.authenticate(master_password)
        return jsonify(result)
        
    except Exception as e:
        print(f"Auth error: {e}")
        return jsonify({"success": False, "error": "Auth failed"})

@app.route('/api/passwords', methods=['GET'])
def get_passwords():
    """GET passwords"""
    if not session.get('authenticated'):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        crypto = manager.get_crypto()
        if not crypto:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
            
        passwords = manager.load_passwords()
        decrypted = {}
        
        for account, encrypted in passwords.items():
            try:
                data = json.loads(crypto.decrypt(encrypted))
                decrypted[account] = data
            except Exception as e:
                print(f"Decrypt error for {account}: {e}")
                continue
        
        return jsonify({"success": True, "passwords": decrypted})
        
    except Exception as e:
        print(f"Get passwords error: {e}")
        return jsonify({"success": False, "error": "Load failed"})

@app.route('/api/passwords', methods=['POST'])
def save_password():
    """POST password"""
    if not session.get('authenticated'):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data"})
            
        account = data.get('account', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        notes = data.get('notes', '').strip()
        
        if not all([account, username, password]):
            return jsonify({"success": False, "error": "Missing required fields"})
        
        crypto = manager.get_crypto()
        if not crypto:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
            
        passwords = manager.load_passwords()
        
        password_data = {
            'username': username,
            'password': password,
            'notes': notes
        }
        
        encrypted = crypto.encrypt(json.dumps(password_data))
        passwords[account] = encrypted
        
        auth_token = crypto.encrypt("AUTH_VALID")
        manager.save_database(auth_token, passwords)
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Save error: {e}")
        return jsonify({"success": False, "error": "Save failed"})

@app.route('/api/generate-password')
def generate_password():
    """Generate password"""
    try:
        password = manager.generate_password()
        return jsonify({"success": True, "password": password})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout"""
    session.clear()
    return jsonify({"success": True})

@app.route('/static/manifest.json')
def manifest():
    """Serve manifest.json"""
    manifest = {
        "name": "Password Manager",
        "short_name": "Passwords",
        "description": "Secure password manager with AES encryption",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a1a1a",
        "theme_color": "#4a9eff",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgdmlld0JveD0iMCAwIDE5MiAxOTIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIiByeD0iNDAiIGZpbGw9IiM0YTllZmYiLz4KPHN2ZyB4PSI0OCIgeT0iNDgiIHdpZHRoPSI5NiIgaGVpZ2h0PSI5NiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CjxwYXRoIGQ9Ik0xOCAxMGgtMVY2YzAtMi43Ni0yLjI0LTUtNS01UzIgMy4yNCAyIDZ2NGgtMWMtMS4xIDAtMiAuOS0yIDJ2MTBjMCAxLjEuOSAyIDIgMmgxNmMxLjEgMCAyLS45IDItMlYxMmMwLTEuMS0uOS0yLTItMnpNOC45IDZjMC0xLjcxIDEuMzktMy4xIDMuMS0zLjFzMy4xIDEuMzkgMy4xIDMuMXY0SDguOVY2eiIvPgo8L3N2Zz4KPC9zdmc+",
                "sizes": "192x192",
                "type": "image/svg+xml"
            }
        ]
    }
    return jsonify(manifest)

@app.route('/favicon.ico')
def favicon():
    """Favicon simple"""
    return '', 204

# Route de test
@app.route('/test')
def test():
    """Route de test"""
    return "<h1>✅ Flask fonctionne !</h1><p>L'app PWA est active.</p>"

if __name__ == '__main__':
    print("🚀 Starting PWA Password Manager")
    print("📱 Templates intégrés - initialisation automatique")
    
    # Initialisation immédiate
    try:
        init_static_files()
        print("✅ Static files initialized")
    except Exception as e:
        print(f"❌ Static files init error: {e}")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False,  # Mode production pour déploiement
        threaded=True
    )