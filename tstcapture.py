#!/usr/bin/env python3
"""
Test IMMÉDIAT du screenshot - Voir la photo directement
"""

from screenshotTacker import take_screenshot
import base64
import os
from datetime import datetime

def test_and_show_screenshot():
    """Capture et affiche la photo immédiatement"""
    print("📸 Capture d'écran en cours...")
    
    # Capture
    result = take_screenshot(quality=85)
    
    if result['success']:
        print("✅ Capture réussie!")
        print(f"📏 Résolution: {result['width']}x{result['height']}")
        print(f"💾 Taille: {result['size_kb']}KB")
        print(f"🎯 Qualité: {result['quality']}%")
        
        # Sauvegarde de la photo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_test_{timestamp}.jpg"
        
        # Convertir base64 -> image
        image_data = base64.b64decode(result['data'])
        
        # Sauvegarder
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Photo sauvegardée: {filename}")
        
        # OUVERTURE AUTOMATIQUE
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filename)
                print("🖼️  Photo ouverte avec le visionneuse Windows!")
            else:  # Linux
                os.system(f"xdg-open {filename}")
                print("🖼️  Photo ouverte avec le visionneuse Linux!")
        except Exception as e:
            print(f"⚠️  Ouverture auto échouée: {e}")
            print(f"📁 Ouvre manuellement: {os.path.abspath(filename)}")
        
        return filename
        
    else:
        print(f"❌ Échec: {result.get('error', 'Unknown error')}")
        return None

if __name__ == "__main__":
    test_and_show_screenshot()