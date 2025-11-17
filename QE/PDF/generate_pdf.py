from datetime import datetime
import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.utils import simpleSplit, ImageReader

# Détection OS pour chemins de fichiers (même logique que main.py)
if sys.platform == 'win32':
    # Windows - chemin relatif depuis la racine du projet
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

def generate_pdf(data: dict) -> BytesIO:
    template_path = "QE/PDF/pdf/pdf-template-soumission.pdf"

    # Créer un calque avec le texte à insérer
    overlay = BytesIO()
    c = canvas.Canvas(overlay, pagesize=letter)

    c.setFont("Helvetica", 8.5)
    nom = data.get("nom", "")
    prix = data.get("prix", "")
    prenom = data.get("prenom", "")
    
    print(f"[DEBUG] DEBUG PDF - Prix reçu: '{prix}' (type: {type(prix)})")
    print(f"[DEBUG] DEBUG PDF - Toutes les clés dans data: {list(data.keys())}")
    print(f"[DEBUG] DEBUG PDF - Valeur brute data['prix']: {repr(data.get('prix', 'CLÉ_PRIX_ABSENTE'))}")
    
    # [FIX] NETTOYAGE BACKEND: Enlever espaces insécables et caractères indésirables
    if prix:
        prix_original = prix
        # Enlever espaces normaux ET insécables (\xa0), enlever $
        prix = prix.replace('\xa0', '').replace(' ', '').replace('$', '').strip()
        # Convertir virgule française en point anglais
        if ',' in prix and prix.count(',') == 1 and len(prix.split(',')[1]) <= 2:
            prix = prix.replace(',', '.')
        print(f"[FIX] DEBUG PDF - Prix après nettoyage backend: '{prix_original}' -> '{prix}'")
    c.drawCentredString(308, 736.5, nom)
    c.drawCentredString(447, 736.5, prenom)

    c.setFont("Helvetica", 8)
    courriel = data.get("courriel", "")
    date = data.get("date", "")
    c.drawCentredString(447, 685.5, courriel)
    c.drawCentredString(237.5, 124.5, date)

    c.setFont("Helvetica", 8.5)
    telephone = data.get("telephone", "")
    num = data.get("num", "")
    temps = data.get("temps", "")
    c.drawCentredString(447, 703, telephone)

    c.setFont("Helvetica-Oblique", 9.5)
    c.drawString(330, 761.5, num)

    c.setFont("Helvetica", 7)
    c.drawCentredString(468.5, 762.5, date)  # 469-0.5=468.5

    c.setFont("Helvetica", 8.5)
    date2 = data.get("date2", "")
    item = data.get("item", "")
    c.drawString(76, 305.5, date2)
    try:
        prix_val = float(prix)
        prix_formate = f"{prix_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        print(f"[OK] DEBUG PDF - Conversion reussie: prix_val={prix_val}, prix_formate='{prix_formate}'")
    except Exception as e:
        prix_val = 0
        prix_formate = ""
        print(f"[ERROR] DEBUG PDF - Erreur conversion: {e}")
    prix_avec_dollar = f"{prix_formate} $" if prix_formate else ""
    c.drawRightString(443, 149.5, prix_formate)
    c.drawString(476, 249.5, temps)
    c.drawString(310, 305.5, temps)
    c.drawString(381, 249.5, prix_avec_dollar)
    c.drawString(76, 249.5, item)

    c.setFont("Helvetica", 8.5)
    try:
        tvq_val = round(prix_val * 0.09975, 2)
        tvq = f"{tvq_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
    except:
        tvq_val = 0  # ← INITIALISER LA VARIABLE
        tvq = ""
    c.drawRightString(443, 124.5, tvq)

    try:
        tps_val = round(prix_val * 0.05, 2)
        tps = f"{tps_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
    except:
        tps_val = 0  # ← INITIALISER LA VARIABLE
        tps = ""
    c.drawRightString(443, 99.5, tps)

    try:
        total_val = prix_val + tps_val + tvq_val
        total = f"{total_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
    except:
        total_val = 0  # ← INITIALISER LA VARIABLE
        total = ""
    c.drawRightString(443, 74.5, total)

    try:
        depot_val = total_val * 0.25
        depot = f"{depot_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ") + " $"
    except:
        depot = ""
    c.drawCentredString(331, 188.5, depot)

    adresse = data.get("adresse", "")
    rue = adresse.split(",")[0].strip()

    # === AUTO-AJUSTEMENT ADRESSE ===
    # Définir la zone maximale fixe pour l'adresse
    adresse_center_x = 308
    adresse_y = 720
    adresse_max_width = 90  # Largeur maximale de la zone

    # Auto-ajuster la taille de la police si le texte est trop long
    font_size_rue = 8.5  # Taille de départ
    min_font_size_rue = 5.0  # Taille minimale

    # Réduire la taille jusqu'à ce que le texte rentre dans la box
    while font_size_rue >= min_font_size_rue:
        text_width = c.stringWidth(rue, "Helvetica", font_size_rue)
        if text_width <= adresse_max_width:
            break
        font_size_rue -= 0.2

    # Dessiner l'adresse avec la taille ajustée
    c.setFont("Helvetica", font_size_rue)
    c.drawCentredString(adresse_center_x, adresse_y, rue)

    ville = adresse.split(",")[1].strip() if "," in adresse else ""
    c.drawCentredString(448, 720, ville)
    postal = adresse.split(",")[2].replace("QC", "").strip() if "," in adresse else ""
    c.drawCentredString(308, 703, postal)

    c.setFont("Helvetica", 7)
    adresse_complete = ""
    try:
        parts = adresse.split(",")
        rue = parts[0].strip()
        ville = parts[1].strip()
        code_postal = parts[2].replace("QC", "").strip()
        adresse_complete = f"{rue}, {ville}, {code_postal}"
    except:
        adresse_complete = adresse.strip()
    c.drawCentredString(165, 149.5, adresse_complete)

    c.setFont("Helvetica", 7.5)
    endroit = data.get("endroit", "")
    x = 76
    y = 458.5
    max_width = 89.5
    max_height = 130
    font_size = 7.5
    min_font_size = 4.5
    line_height_ratio = 1.3

    # Fonction pour appliquer word wrap sur UNE ligne (respecte les \n)
    def wrap_single_line(text, size):
        words = text.split()
        wrapped = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if c.stringWidth(test_line, "Helvetica", size) <= max_width:
                line = test_line
            else:
                if line:
                    wrapped.append(line)
                line = word
        if line:
            wrapped.append(line)
        return wrapped if wrapped else [""]

    # Séparer d'abord par \n, puis appliquer word wrap sur chaque ligne
    def split_lines_with_newlines(text, size):
        all_lines = []
        raw_lines = text.split('\n')
        for raw_line in raw_lines:
            if raw_line.strip():
                all_lines.extend(wrap_single_line(raw_line.strip(), size))
            else:
                all_lines.append("")  # Ligne vide
        return all_lines

    while font_size >= min_font_size:
        lines = split_lines_with_newlines(endroit, font_size)
        line_height = font_size * line_height_ratio
        total_height = len(lines) * line_height
        if total_height <= max_height:
            break
        font_size -= 0.2

    text_obj = c.beginText()
    text_obj.setTextOrigin(x, y + max_height - line_height)
    text_obj.setFont("Helvetica", font_size)
    for line in lines:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # === PRODUIT / COULEURS ===
    produit = data.get("produit", "")
    print(f"[DEBUG] DEBUG PRODUIT - Reçu du frontend: {repr(produit)}")
    lines_produit_raw = [line.strip() for line in produit.split("\n") if line.strip()]
    print(f"[DEBUG] DEBUG PRODUIT - Lignes après split: {lines_produit_raw}")

    font_size_produit = 7.5
    line_height_produit = font_size_produit * 1.4
    x_produit = 403
    y_produit = 458.5
    max_width_produit = 135  # Largeur maximale pour le texte (réduite de 25px)
    max_height_produit = 130

    # Fonction pour couper les lignes trop longues (word wrap)
    def wrap_line_produit(text, max_w, font_s):
        words = text.split()
        wrapped = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if c.stringWidth(test, "Helvetica", font_s) <= max_w:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)
        return wrapped if wrapped else [text]

    # Appliquer le word wrap à chaque ligne
    lines_produit = []
    for line in lines_produit_raw:
        lines_produit.extend(wrap_line_produit(line, max_width_produit, font_size_produit))

    start_y_produit = y_produit + max_height_produit - font_size_produit

    text_obj = c.beginText()
    text_obj.setFont("Helvetica", font_size_produit)

    for i, line in enumerate(lines_produit):
        current_y = start_y_produit - (i * line_height_produit)
        if current_y < y_produit:
            break
        text_obj.setTextOrigin(x_produit, current_y)
        text_obj.textLine(line)

    c.drawText(text_obj)

    # === PARTICULARITÉ DES TRAVAUX ===
    part = data.get("part", "")
    lines_part = [line.strip() for line in part.split("\n") if line.strip()]
    font_size_part = 7.5
    line_height_part = font_size_part * 3.6
    x_part = 76
    y_part = 317.5
    max_width_part = 463
    max_height_part = 120

    start_y_part = y_part + max_height_part - font_size_part

    text_obj = c.beginText()
    text_obj.setFont("Helvetica", font_size_part)

    for i, line in enumerate(lines_part):
        current_y = start_y_part - (i * line_height_part)
        if current_y < y_part:
            break
        text_obj.setTextOrigin(x_part, current_y)
        text_obj.textLine(line)

    c.drawText(text_obj)

    # === DESSIN DES "X" POUR MOTS CLÉS ===
    produit_text = data.get("produit", "").lower()
    payer_par_text = data.get("payer_par", "").lower()

    xlavage = "lavage" in produit_text
    xsablage = "sablage" in produit_text
    xappret = "apprêt" in produit_text
    xreparations = "réparations" in produit_text
    xgrattage = "grattage" in produit_text
    xvirement = "virement" in payer_par_text
    xcheque = "chèque" in payer_par_text

    x_coords = {
        "xlavage": 188,
        "xsablage": 328.5,
        "xappret": 375.2,
        "xreparations": 281.7,
        "xgrattage": 235,
        "xvirement": 450.7,
        "xcheque": 450.7
    }

    y_coord_anciens = 578.5
    y_coord_virement = 189.5
    y_coord_cheque = 179.2

    c.setFont("Helvetica", 8)
    if xlavage:
        c.drawString(x_coords["xlavage"], y_coord_anciens, "X")
    if xsablage:
        c.drawString(x_coords["xsablage"], y_coord_anciens, "X")
    if xappret:
        c.drawString(x_coords["xappret"], y_coord_anciens, "X")
    if xreparations:
        c.drawString(x_coords["xreparations"], y_coord_anciens, "X")
    if xgrattage:
        c.drawString(x_coords["xgrattage"], y_coord_anciens, "X")
    if xvirement:
        c.drawString(x_coords["xvirement"], y_coord_virement, "X")
    if xcheque:
        c.drawString(x_coords["xcheque"], y_coord_cheque, "X")

    # === INFORMATIONS ENTREPRENEUR (user_info.json) ===
    username = data.get("username", "")
    print(f"[DEBUG] DEBUG: Username reçu pour signature: '{username}'")

    if username:
        # Charger les informations de l'entrepreneur depuis user_info.json
        user_info_path = os.path.join(base_cloud, "signatures", username, "user_info.json")
        user_info = {}

        if os.path.exists(user_info_path):
            try:
                import json
                with open(user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
                print(f"[OK] Informations entrepreneur chargees: {user_info}")
            except Exception as e:
                print(f"[WARN] Erreur chargement user_info.json: {e}")

        # Afficher prénom et nom sur la même ligne (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("prenom") and user_info.get("nom"):
            c.setFont("Helvetica", 8)
            nom_complet = f"{user_info['prenom']} {user_info['nom']}"
            c.drawCentredString(166.5, 648.5, nom_complet)  # 167-0.5=166.5, 648+0.5=648.5
            print(f"[OK] Nom complet ajoute: {nom_complet} a (166.5, 648.5)")

        # Afficher courriel (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("courriel"):
            c.setFont("Helvetica", 8)
            c.drawCentredString(166.5, 632.5, user_info['courriel'])  # 167-0.5=166.5, 632+0.5=632.5
            print(f"[OK] Courriel ajoute: {user_info['courriel']} a (166.5, 632.5)")

        # Afficher téléphone (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("telephone"):
            c.setFont("Helvetica", 8)
            c.drawCentredString(166.5, 616.5, user_info['telephone'])  # 167-0.5=166.5, 616+0.5=616.5
            print(f"[OK] Telephone ajoute: {user_info['telephone']} a (166.5, 616.5)")

        # === SIGNATURE ENTREPRENEUR ===
        signature_path = os.path.join(base_cloud, "signatures", username, f"signature_{username}_black.png")
        print(f"[DEBUG] DEBUG: Chemin signature noire: {signature_path}")
        print(f"[DEBUG] DEBUG: Signature noire existe? {os.path.exists(signature_path)}")

        if os.path.exists(signature_path):
            try:
                print("[DEBUG] DEBUG: Tentative de chargement de la signature...")

                # Charger la signature de l'entrepreneur
                signature_img = ImageReader(signature_path)

                # Position signature entrepreneur (au-dessus de la future signature client)
                # Client sera à x=80, y=87.5, donc entrepreneur à x=80, y=112.5 (remonté de 5px)
                x_entrepreneur = 80
                y_entrepreneur = 112.5
                width_entrepreneur = 100
                height_entrepreneur = 30

                print(f"[DEBUG] DEBUG: Ajout signature à position ({x_entrepreneur}, {y_entrepreneur})")

                c.drawImage(signature_img, x_entrepreneur, y_entrepreneur,
                          width=width_entrepreneur, height=height_entrepreneur, mask='auto')

                print("[OK] DEBUG: Signature entrepreneur ajoutee avec succes!")

                # Afficher courriel en plus petit (0.5px plus bas, 4px plus à gauche)
                if user_info.get("courriel"):
                    c.setFont("Helvetica", 6)  # Plus petit
                    courriel_x = x_entrepreneur + width_entrepreneur + 20 - 25 - 8 - 5 - 4  # 20-25-8-5-4 = -22
                    courriel_y = y_entrepreneur + height_entrepreneur + 50 - 10 - 5 + 1 - 0.5  # 50-10-5+1-0.5 = 35.5px
                    c.drawCentredString(courriel_x, courriel_y, user_info['courriel'])
                    print(f"[OK] Courriel signature ajoute: {user_info['courriel']} a ({courriel_x}, {courriel_y})")

            except Exception as e:
                print(f"[ERROR] DEBUG: Erreur lors de l'ajout de la signature entrepreneur: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[ERROR] DEBUG: Fichier signature non trouve: {signature_path}")
    else:
        print("[ERROR] DEBUG: Aucun username fourni")

    c.save()
    overlay.seek(0)

    background = PdfReader(template_path)
    overlay_pdf = PdfReader(overlay)

    writer = PdfWriter()
    page = background.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output
