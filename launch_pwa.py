#!/usr/bin/env python3
"""
Lanceur PWA simplifié - fonctionne avec tes fichiers existants
Pas besoin de templates séparés, tout est intégré
"""

import os
import sys
import socket
import webbrowser
import subprocess
from threading import Timer

def check_dependencies():
    """Vérifier Flask uniquement"""
    try:
        import flask
        print("✅ Flask")
        return True
    except ImportError:
        print("❌ Flask missing - installing...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])
            print("✅ Flask installed")
            return True
        except:
            print("❌ Failed to install Flask")
            return False

def check_files():
    """Vérifier les fichiers de base"""
    required = ['crypto.py', 'dropbox_sync.py', 'config.json']
    missing = [f for f in required if not os.path.exists(f)]
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    for f in required:
        print(f"✅ {f}")
    
    return True

def get_network_info():
    """Récupérer IP locale"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.1.100"

def generate_qr(url):
    """QR Code simple en ASCII"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        
        print(f"\n📱 QR Code pour mobile:")
        qr_matrix = qr.get_matrix()
        for row in qr_matrix:
            line = ""
            for cell in row:
                line += "██" if cell else "  "
            print(line)
        print()
    except ImportError:
        print(f"\n📱 URL mobile: {url}")
        print("💡 Scannez avec votre téléphone ou tapez l'URL")

def main():
    print("""
╭─────────────────────────────────────╮
│  📱 PASSWORD MANAGER PWA  📱       │
│                                     │
│  Ready to install on your phone!   │
╰─────────────────────────────────────╯
    """)
    
    print("🔍 Checking requirements...")
    
    # Vérifications
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    if not check_files():
        input("Press Enter to exit...")
        return
    
    # Vérifier que web_app_pwa.py existe
    if not os.path.exists('web_app_pwa.py'):
        print("❌ web_app_pwa.py missing!")
        print("💡 This file should have been created with the PWA code")
        input("Press Enter to exit...")
        return
    
    print("✅ web_app_pwa.py")
    
    # Configuration réseau
    host = "0.0.0.0"
    port = 5000
    local_ip = get_network_info()
    
    local_url = f"http://localhost:{port}"
    mobile_url = f"http://{local_ip}:{port}"
    
    print(f"\n🚀 Starting PWA server...")
    print(f"=" * 50)
    print(f"🌟 PASSWORD MANAGER PWA READY!")
    print(f"=" * 50)
    print(f"🖥️  Desktop: {local_url}")
    print(f"📱 Mobile:  {mobile_url}")
    print(f"\n📋 Mobile Setup:")
    print(f"   1. Connect phone to same WiFi as this PC")
    print(f"   2. Open Safari/Chrome on phone")
    print(f"   3. Go to: {mobile_url}")
    print(f"   4. iOS: Share → Add to Home Screen")
    print(f"   5. Android: Menu → Install App")
    print(f"   6. PWA installed like real app! 🎉")
    
    # QR Code
    generate_qr(mobile_url)
    
    print(f"💡 PWA Features:")
    print(f"   ✅ Works offline after first visit")
    print(f"   ✅ Installs like native app") 
    print(f"   ✅ Same security as desktop")
    print(f"   ✅ Touch-optimized interface")
    print(f"\n🛑 Stop server: Ctrl+C")
    print(f"=" * 50)
    
    # Ouvrir navigateur
    Timer(2.0, lambda: webbrowser.open(local_url)).start()
    
    try:
        # Lancer l'app PWA
        from web_app_pwa import app
        app.run(host=host, port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print(f"\n\n👋 PWA server stopped")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()