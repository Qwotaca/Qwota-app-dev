from PIL import Image

# Ouvrir l'image PNG
img = Image.open('logo.png')

# Convertir en RGBA si nécessaire
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Créer plusieurs tailles pour l'icône (Windows utilise différentes tailles)
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

# Sauvegarder en .ico
img.save('icon.ico', format='ICO', sizes=sizes)

print("Logo converti en icon.ico avec succes!")
