#!/usr/bin/env python3
"""
Script pour corriger la configuration Dropbox
"""

import json
import os

def fix_dropbox_config():
    """Corriger le config.json pour Dropbox"""
    
    print("🔧 Dropbox Configuration Fix")
    print("=" * 40)
    
    # Vérifier si config.json existe
    if not os.path.exists('config.json'):
        print("❌ config.json not found!")
        print("Creating new config.json...")
        
        config = {
            "dropbox_token": "YOUR_DROPBOX_TOKEN_HERE",
            "remote_path": "/passwords.db"
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ config.json created")
    
    # Lire la config actuelle
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return
    
    # Vérifier le token
    token = config.get('dropbox_token', '')
    
    if not token or token in ['YOUR_DROPBOX_TOKEN_HERE', 'VOTRE_TOKEN_DROPBOX_ICI']:
        print("⚠️  Dropbox token not configured!")
        print("\n📋 How to get your Dropbox token:")
        print("1. Go to: https://www.dropbox.com/developers/apps")
        print("2. Click 'Create app'")
        print("3. Choose 'Scoped access' → 'Full Dropbox'")
        print("4. Name your app (e.g., 'PasswordManager')")
        print("5. In app settings → 'OAuth 2' → 'Generate access token'")
        print("6. Copy the token and paste it here")
        print()
        
        new_token = input("🔑 Paste your Dropbox token (or Enter to skip): ").strip()
        
        if new_token:
            config['dropbox_token'] = new_token
            
            try:
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                print("✅ Token saved to config.json")
                
                # Test the token
                print("🧪 Testing Dropbox connection...")
                try:
                    import dropbox
                    dbx = dropbox.Dropbox(new_token)
                    dbx.users_get_current_account()
                    print("✅ Dropbox connection successful!")
                except Exception as e:
                    print(f"❌ Dropbox test failed: {e}")
                    print("💡 Check your token and try again")
                    
            except Exception as e:
                print(f"❌ Error saving config: {e}")
        else:
            print("⚠️  Skipped - you can edit config.json manually later")
    else:
        print("✅ Dropbox token found")
        
        # Test existing token
        print("🧪 Testing existing token...")
        try:
            import dropbox
            dbx = dropbox.Dropbox(token)
            account = dbx.users_get_current_account()
            print(f"✅ Connected to Dropbox as: {account.name.display_name}")
        except Exception as e:
            print(f"❌ Token test failed: {e}")
            print("💡 You may need to generate a new token")
    
    print(f"\n📄 Current config.json:")
    try:
        with open('config.json', 'r') as f:
            content = f.read()
        print(content)
    except:
        pass
    
    print(f"\n💡 Tips:")
    print(f"   - Keep your token secure")
    print(f"   - Don't share config.json with others")
    print(f"   - Token enables automatic sync between devices")

if __name__ == "__main__":
    try:
        fix_dropbox_config()
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to exit...")