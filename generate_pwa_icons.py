#!/usr/bin/env python3
"""
Génération des icônes PWA dans toutes les tailles requises
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_pwa_icons():
    """Crée toutes les icônes PWA nécessaires"""
    
    # Créer le dossier static
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Tailles d'icônes requises pour PWA
    icon_sizes = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
    
    print("🎨 Generating PWA icons...")
    
    for size in icon_sizes:
        print(f"📐 Creating {size}x{size} icon...")
        
        # Créer une image avec fond transparent
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Couleurs
        bg_color = (44, 62, 80, 255)      # Bleu foncé
        lock_color = (255, 255, 255, 255)  # Blanc
        accent_color = (74, 158, 255, 255) # Bleu accent
        
        # Marges proportionnelles
        margin = size // 8
        
        # Dessiner le fond rond avec gradient effect
        draw.ellipse([margin, margin, size-margin, size-margin], fill=bg_color)
        
        # Ajouter un effet de bordure
        border_width = max(1, size // 64)
        draw.ellipse([margin, margin, size-margin, size-margin], 
                    outline=accent_color, width=border_width)
        
        # Dessiner le cadenas
        lock_size = size // 3
        lock_x = (size - lock_size) // 2
        lock_y = (size - lock_size) // 2
        
        # Corps du cadenas
        body_height = int(lock_size * 0.6)
        body_y = lock_y + int(lock_size * 0.4)
        radius = max(2, size // 32)
        
        # Dessiner le corps du cadenas
        draw.rounded_rectangle([lock_x, body_y, lock_x + lock_size, body_y + body_height], 
                             radius=radius, fill=lock_color)
        
        # Anse du cadenas
        shackle_width = int(lock_size * 0.6)
        shackle_height = int(lock_size * 0.4)
        shackle_x = lock_x + (lock_size - shackle_width) // 2
        shackle_y = lock_y
        
        # Dessiner l'anse (arc)
        line_width = max(2, size // 32)
        draw.arc([shackle_x, shackle_y, shackle_x + shackle_width, shackle_y + shackle_height],
                start=0, end=180, fill=lock_color, width=line_width)
        
        # Petit cercle pour le trou de serrure
        keyhole_size = max(2, size // 16)
        keyhole_x = lock_x + lock_size // 2 - keyhole_size // 2
        keyhole_y = body_y + body_height // 3
        draw.ellipse([keyhole_x, keyhole_y, keyhole_x + keyhole_size, keyhole_y + keyhole_size],
                    fill=bg_color)
        
        # Sauvegarder l'icône
        filename = f'static/icon-{size}.png'
        img.save(filename, format='PNG', optimize=True)
        print(f"✅ Saved {filename}")
    
    # Créer aussi favicon.ico
    favicon_img = Image.open('static/icon-32.png')
    favicon_img.save('static/favicon.ico', format='ICO', sizes=[(32, 32)])
    print("✅ Saved static/favicon.ico")
    
    print(f"\n🎉 Generated {len(icon_sizes)} PWA icons + favicon!")
    print("📁 All icons saved in 'static/' folder")

def create_splash_screens():
    """Crée des écrans de démarrage pour iOS"""
    print("\n🖼️  Generating splash screens...")
    
    # Tailles d'écrans iOS courantes
    splash_sizes = [
        (1125, 2436),  # iPhone X/XS
        (1242, 2688),  # iPhone XS Max
        (828, 1792),   # iPhone XR
        (1170, 2532),  # iPhone 12/13 Pro
        (1284, 2778),  # iPhone 12/13 Pro Max
        (1080, 2340),  # iPhone 12 mini
    ]
    
    for width, height in splash_sizes:
        # Créer l'écran de démarrage
        img = Image.new('RGB', (width, height), (26, 26, 26))  # Fond sombre
        draw = ImageDraw.Draw(img)
        
        # Logo centré
        logo_size = min(width, height) // 4
        logo_x = (width - logo_size) // 2
        logo_y = (height - logo_size) // 2
        
        # Fond du logo
        bg_color = (44, 62, 80)
        margin = logo_size // 8
        draw.ellipse([logo_x + margin, logo_y + margin, 
                     logo_x + logo_size - margin, logo_y + logo_size - margin], 
                    fill=bg_color)
        
        # Cadenas simple
        lock_size = logo_size // 3
        lock_x = logo_x + (logo_size - lock_size) // 2
        lock_y = logo_y + (logo_size - lock_size) // 2
        
        # Corps
        body_height = int(lock_size * 0.6)
        body_y = lock_y + int(lock_size * 0.4)
        draw.rounded_rectangle([lock_x, body_y, lock_x + lock_size, body_y + body_height], 
                             radius=8, fill=(255, 255, 255))
        
        # Anse
        shackle_width = int(lock_size * 0.6)
        shackle_height = int(lock_size * 0.4)
        shackle_x = lock_x + (lock_size - shackle_width) // 2
        shackle_y = lock_y
        draw.arc([shackle_x, shackle_y, shackle_x + shackle_width, shackle_y + shackle_height],
                start=0, end=180, fill=(255, 255, 255), width=6)
        
        # Sauvegarder
        filename = f'static/splash-{width}x{height}.png'
        img.save(filename, format='PNG', optimize=True)
        print(f"✅ Created splash screen {width}x{height}")

if __name__ == "__main__":
    try:
        create_pwa_icons()
        create_splash_screens()
        
        print(f"\n✨ PWA assets ready!")
        print(f"🚀 Your PWA now has:")
        print(f"   - ✅ All required icon sizes")
        print(f"   - ✅ Favicon for browsers")
        print(f"   - ✅ iOS splash screens")

    except Exception as e:
        print(f"⚠️  Error generating PWA assets: {e}")
        print("💡 Ensure you have Pillow installed: pip install Pillow")