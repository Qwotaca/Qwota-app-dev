from datetime import datetime
import os
import sys
import re
import json
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

def generate_pdf(data: dict, language: str = 'fr') -> BytesIO:
    """
    Génère un PDF de soumission

    Args:
        data: Données de la soumission
        language: Langue du template ('fr' ou 'en'), par défaut 'fr'
    """
    # Choisir le template selon la langue - utiliser chemin absolu
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if language == 'en':
        template_path = os.path.join(script_dir, "pdf", "pdf-template-soumission-en.pdf")
    else:
        template_path = os.path.join(script_dir, "pdf", "pdf-template-soumission.pdf")

    # Les templates FR et EN ont la même structure, pas d'ajustement nécessaire
    y_offset = 0

    print(f"[PDF] Langue sélectionnée: {language}, Template: {template_path}")

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
    # Pas d'ajustement - templates FR et EN identiques
    client_y_adjust = 0

    c.drawCentredString(308, 736.5 + y_offset + client_y_adjust, nom)
    c.drawCentredString(447, 736.5 + y_offset + client_y_adjust, prenom)

    c.setFont("Helvetica", 8)
    courriel = data.get("courriel", "")
    date = data.get("date", "")
    c.drawCentredString(447, 685.5 + y_offset + client_y_adjust, courriel)
    c.drawCentredString(237.5, 124.5 + y_offset, date)

    c.setFont("Helvetica", 8.5)
    telephone = data.get("telephone", "")
    num = data.get("num", "")
    temps = data.get("temps", "")
    c.drawCentredString(447, 703 + y_offset + client_y_adjust, telephone)

    c.setFont("Helvetica-Oblique", 9.5)
    c.drawString(330, 761.5 + y_offset, num)

    c.setFont("Helvetica", 7)
    c.drawCentredString(468.5, 762.5 + y_offset, date)  # 469-0.5=468.5

    c.setFont("Helvetica", 8.5)
    date2 = data.get("date2", "")
    item = data.get("item", "")
    c.drawString(76, 307.5 + y_offset, date2)
    try:
        prix_val = float(prix)
        prix_formate = f"{prix_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        print(f"[OK] DEBUG PDF - Conversion reussie: prix_val={prix_val}, prix_formate='{prix_formate}'")
    except Exception as e:
        prix_val = 0
        prix_formate = ""
        print(f"[ERROR] DEBUG PDF - Erreur conversion: {e}")
    prix_avec_dollar = f"{prix_formate} $" if prix_formate else ""
    c.drawRightString(443, 149.5 + y_offset, prix_formate)
    c.drawString(235, 307.5 + y_offset, temps)

    # === ITEM en colonnes (nom | prix | durée) ===
    # Positions des colonnes
    x_item_nom = 76      # Colonne Item (nom)
    x_item_prix = 381    # Colonne Prix
    x_item_duree = 476   # Colonne Durée approx
    y_start = 249.5 + y_offset  # Position Y de départ
    line_height = 12     # Hauteur entre les lignes

    print(f"[PDF DEBUG] Item reçu: '{item}'")
    print(f"[PDF DEBUG] Type item: {type(item)}")

    # Parser les items (nouveau format JSON ou ancien format texte)
    try:
        items_list = json.loads(item)
        print(f"[PDF DEBUG] Items parsés: {items_list}")
        if isinstance(items_list, list) and len(items_list) > 0:
            # Nouveau format JSON: [{"nom": "...", "prix": "...", "duree": "..."}]
            for i, it in enumerate(items_list):
                y_pos = y_start - (i * line_height)
                print(f"[PDF DEBUG] Item {i}: nom={it.get('nom')}, prix={it.get('prix')}, duree={it.get('duree')}, y={y_pos}")
                if it.get('nom'):
                    c.drawString(x_item_nom, y_pos, it['nom'])
                if it.get('prix'):
                    c.drawString(x_item_prix, y_pos, it['prix'])
                if it.get('duree'):
                    c.drawString(x_item_duree, y_pos, it['duree'])
        else:
            print(f"[PDF DEBUG] Liste vide ou invalide, fallback ancien format")
            # Liste vide ou format invalide - ancien comportement
            c.drawString(x_item_nom, y_start, item if item else "")
            c.drawString(x_item_prix, y_start, prix_avec_dollar)
            c.drawString(x_item_duree, y_start, temps)
    except Exception as e:
        print(f"[PDF DEBUG] Erreur parsing JSON: {e}")
        # Ancien format texte - afficher tel quel
        c.drawString(x_item_nom, y_start, item if item else "")
        c.drawString(x_item_prix, y_start, prix_avec_dollar)
        c.drawString(x_item_duree, y_start, temps)

    c.setFont("Helvetica", 8.5)

    # Calculer les taxes selon la langue
    if language == 'fr':
        # Français: TPS 5% + TVQ 9.975%
        try:
            tps_val = round(prix_val * 0.05, 2)
            tps = f"{tps_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        except:
            tps_val = 0
            tps = ""

        try:
            tvq_val = round(prix_val * 0.09975, 2)
            tvq = f"{tvq_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        except:
            tvq_val = 0
            tvq = ""

        total_val = prix_val + tps_val + tvq_val
    else:
        # Anglais: TVH/HST 13%
        try:
            tvh_val = round(prix_val * 0.13, 2)
            tvh = f"{tvh_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        except:
            tvh_val = 0
            tvh = ""

        total_val = prix_val + tvh_val

    # Calculer le total formaté
    try:
        total = f"{total_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
    except:
        total = ""

    # Affichage selon la langue
    if language == 'fr':
        # Français: TVQ, TPS, Total à leurs positions normales
        c.drawRightString(443, 124.5 + y_offset, tvq)
        c.drawRightString(443, 99.5 + y_offset, tps)
        c.drawRightString(443, 74.5 + y_offset, total)
    else:
        # Anglais: TVH en haut, Total en bas
        c.drawRightString(443, 124.5 + y_offset, tvh)
        c.drawRightString(443, 99.5 + y_offset, total)

    # Utiliser le dépôt envoyé depuis le formulaire, sinon calculer 25% du total
    depot_from_form = data.get("depot", "")
    if depot_from_form and depot_from_form.strip():
        # Nettoyer et formater le dépôt envoyé depuis le formulaire
        try:
            depot_clean = depot_from_form.replace('\xa0', '').replace(' ', '').replace('$', '').strip()
            if ',' in depot_clean and depot_clean.count(',') == 1 and len(depot_clean.split(',')[1]) <= 2:
                depot_clean = depot_clean.replace(',', '.')
            depot_val = float(depot_clean)
            depot = f"{depot_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ") + " $"
        except:
            # Si erreur de parsing, calculer automatiquement
            try:
                depot_val = total_val * 0.25
                depot = f"{depot_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ") + " $"
            except:
                depot = ""
    else:
        # Si pas de dépôt dans le formulaire, calculer automatiquement
        try:
            depot_val = total_val * 0.25
            depot = f"{depot_val:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ") + " $"
        except:
            depot = ""
    c.drawCentredString(331, 188.5 + y_offset, depot)

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
    c.drawCentredString(adresse_center_x, adresse_y + y_offset + client_y_adjust, rue)

    # Remettre la taille normale pour ville et code postal
    c.setFont("Helvetica", 8.5)
    ville = adresse.split(",")[1].strip() if "," in adresse else ""
    c.drawCentredString(448, 720 + y_offset + client_y_adjust, ville)
    postal = adresse.split(",")[2].replace("QC", "").strip() if "," in adresse else ""
    c.drawCentredString(308, 703 + y_offset + client_y_adjust, postal)

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
    # Anglais: +1px vers le haut
    adresse_y = 149.5 + y_offset + (1 if language == 'en' else 0)
    c.drawCentredString(165, adresse_y, adresse_complete)

    c.setFont("Helvetica", 7.5)
    endroit = data.get("endroit", "")
    # Pas d'ajustement - templates FR et EN identiques
    x = 82
    y = 460.5 + y_offset
    max_width = 84.5
    max_height = 130
    base_font_size = 7.5
    min_font_size = 4.0
    line_height_ratio = 1.75

    # Séparer par \n - chaque endroit = 1 ligne (pas de wrap)
    raw_lines = [line.strip() for line in endroit.split('\n') if line.strip()]

    # Fonction pour calculer la taille de police nécessaire pour qu'une ligne tienne sur 1 seule ligne
    def get_font_size_for_line(text, max_size, min_size, max_w):
        size = max_size
        while size >= min_size:
            if c.stringWidth(text, "Helvetica", size) <= max_w:
                return size
            size -= 0.2
        return min_size  # Retourner la taille minimum si ça ne rentre toujours pas

    # Calculer la taille de police pour chaque ligne
    line_font_sizes = []
    for line in raw_lines:
        font_size = get_font_size_for_line(line, base_font_size, min_font_size, max_width)
        line_font_sizes.append(font_size)

    # Dessiner chaque ligne avec sa propre taille de police
    line_height = base_font_size * line_height_ratio
    current_y = y + max_height - line_height

    for i, line in enumerate(raw_lines):
        font_size = line_font_sizes[i]
        c.setFont("Helvetica", font_size)
        c.drawString(x, current_y, line)
        current_y -= line_height

    # === PRODUIT / COULEURS ===
    produit = data.get("produit", "")
    print(f"[DEBUG] DEBUG PRODUIT - Reçu du frontend: {repr(produit)}")
    lines_produit_raw = [line.strip() for line in produit.split("\n") if line.strip()]
    print(f"[DEBUG] DEBUG PRODUIT - Lignes après split: {lines_produit_raw}")

    font_size_produit = 7.5
    line_height_produit = font_size_produit * 1.4
    # Pas d'ajustement - templates FR et EN identiques
    x_produit = 403
    y_produit = 294.5 + y_offset
    max_width_produit = 139  # Largeur maximale pour le texte
    max_height_produit = 292

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
                # Si le mot seul est trop long, le couper en caractères
                if c.stringWidth(word, "Helvetica", font_s) > max_w:
                    # Couper le mot caractère par caractère
                    temp = ""
                    for char in word:
                        if c.stringWidth(temp + char, "Helvetica", font_s) <= max_w:
                            temp += char
                        else:
                            if temp:
                                wrapped.append(temp)
                            temp = char
                    current = temp
                else:
                    current = word
        if current:
            wrapped.append(current)
        return wrapped if wrapped else [text]

    # Ajustement automatique de la taille de police pour que tout rentre
    current_font_size = font_size_produit
    current_line_height = line_height_produit

    print(f"\n[PDF PRODUIT] ==================== DEBUT AJUSTEMENT ====================")
    print(f"[PDF PRODUIT] Texte brut recu: {len(lines_produit_raw)} lignes")
    print(f"[PDF PRODUIT] Hauteur disponible: {max_height_produit}px")
    print(f"[PDF PRODUIT] Largeur disponible: {max_width_produit}px")

    # Boucle pour réduire la taille jusqu'à ce que tout rentre
    iteration = 0
    while current_font_size > 2.5:  # Minimum 2.5pt
        iteration += 1
        lines_produit = []
        current_line_height = current_font_size * 1.4

        # Wrapper toutes les lignes
        for line in lines_produit_raw:
            lines_produit.extend(wrap_line_produit(line, max_width_produit, current_font_size))

        # Calculer la hauteur totale nécessaire
        total_height_needed = len(lines_produit) * current_line_height

        print(f"[PDF PRODUIT] Iteration {iteration}: Taille police={current_font_size}pt | Lignes apres wrap={len(lines_produit)} | Hauteur necessaire={total_height_needed:.2f}px")

        # Si ça rentre, on arrête
        if total_height_needed <= max_height_produit:
            print(f"[PDF PRODUIT] OK Tout rentre! Taille finale: {current_font_size}pt")
            break

        # Sinon, réduire la taille
        current_font_size -= 0.25
        print(f"[PDF PRODUIT] WARN Trop grand, reduction a {current_font_size}pt")

    # Si on n'a pas de lignes, refaire une dernière fois
    if 'lines_produit' not in locals() or not lines_produit:
        lines_produit = []
        for line in lines_produit_raw:
            lines_produit.extend(wrap_line_produit(line, max_width_produit, current_font_size))

    print(f"[PDF PRODUIT] ==================== FIN AJUSTEMENT ====================")
    print(f"[PDF PRODUIT] RÉSULTAT FINAL: Taille={current_font_size}pt | Lignes={len(lines_produit)} | Hauteur ligne={current_line_height:.2f}px\n")

    start_y_produit = y_produit + max_height_produit - current_font_size

    # Dessiner chaque ligne individuellement pour pouvoir changer la police (gras pour les titres)
    header_pattern = re.compile(r'^===\s*(.+?)\s*===$')

    for i, line in enumerate(lines_produit):
        current_y = start_y_produit - (i * current_line_height)
        if current_y < y_produit:
            break

        # Vérifier si c'est un header (=== Endroit ===)
        header_match = header_pattern.match(line)
        if header_match:
            # Extraire le nom de l'endroit et ajouter ":"
            endroit_name = header_match.group(1) + ":"
            c.setFont("Helvetica-Bold", current_font_size)
            c.drawString(x_produit, current_y, endroit_name)
        else:
            # Ligne normale
            c.setFont("Helvetica", current_font_size)
            c.drawString(x_produit, current_y, line)

    # === PARTICULARITÉ DES TRAVAUX ===
    part = data.get("part", "")
    lines_part = [line.strip() for line in part.split("\n") if line.strip()]
    font_size_part = 7.5
    line_height_part = font_size_part * 1.8  # Espacement léger
    x_part = 76
    y_part = 317.5 + y_offset
    max_width_part = 326
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

    # === DESSIN DES "X" POUR MOTS CLÉS (par endroit) ===
    produit_text = data.get("produit", "")
    payer_par_text = data.get("payer_par", "").lower()

    # Parser les sections par endroit (=== NomEndroit ===)
    endroit_pattern = re.compile(r'===\s*(.+?)\s*===')
    endroit_sections = re.split(r'===\s*.+?\s*===', produit_text)

    # Ajustement pour anglais seulement (X de préparation)
    x_adjust_prep = 0.5 if language == 'en' else 0
    y_adjust_prep = 0.5 if language == 'en' else 0

    # Coordonnées X pour chaque type de préparation
    x_coords = {
        "lavage": 188 + x_adjust_prep,
        "sablage": 328.5 + x_adjust_prep,
        "appret": 375.2 + x_adjust_prep,
        "reparations": 281.7 + x_adjust_prep,
        "grattage": 235 + x_adjust_prep,
    }

    y_coord_base = 578.5 + y_offset + y_adjust_prep
    y_spacing = 13.125  # Même que endroit: 7.5 × 1.75

    c.setFont("Helvetica", 8)

    # Pour chaque endroit (max 10), dessiner les X sur sa propre ligne
    for i, section in enumerate(endroit_sections[1:11]):  # Skip first empty, max 10 endroits
        section_lower = section.lower()
        y_coord = y_coord_base - (i * y_spacing)

        # Lavage (FR) / Pressure wash (EN)
        if "lavage" in section_lower or "pressure wash" in section_lower:
            c.drawString(x_coords["lavage"], y_coord, "X")
        # Sablage (FR) / Sanding (EN)
        if "sablage" in section_lower or "sanding" in section_lower:
            c.drawString(x_coords["sablage"], y_coord, "X")
        # Apprêt (FR) / Primer (EN)
        if "apprêt" in section_lower or "appret" in section_lower or "primer" in section_lower:
            c.drawString(x_coords["appret"], y_coord, "X")
        # Réparations (FR) / Repairs (EN)
        if "réparations" in section_lower or "reparations" in section_lower or "repairs" in section_lower:
            c.drawString(x_coords["reparations"], y_coord, "X")
        # Grattage (FR) / Scraping (EN)
        if "grattage" in section_lower or "scraping" in section_lower:
            c.drawString(x_coords["grattage"], y_coord, "X")

    # Paiement (une seule ligne, inchangé)
    xvirement = "virement" in payer_par_text
    xcheque = "chèque" in payer_par_text

    # Anglais: virement/chèque +0.5px à droite et +0.5px vers le haut
    x_adjust_paiement = 0.5 if language == 'en' else 0
    y_adjust_paiement = 0.5 if language == 'en' else 0

    y_coord_virement = 189.5 + y_offset + y_adjust_paiement
    y_coord_cheque = 179.2 + y_offset + y_adjust_paiement

    if xvirement:
        c.drawString(450.7 + x_adjust_paiement, y_coord_virement, "X")
    if xcheque:
        c.drawString(450.7 + x_adjust_paiement, y_coord_cheque, "X")

    # === INFORMATIONS ENTREPRENEUR (user_info.json) ===
    username = data.get("username", "")
    print(f"[DEBUG] DEBUG: Username reçu pour signature: '{username}'")

    if username:
        # Charger les informations de l'entrepreneur depuis user_info.json
        user_info_path = os.path.join(base_cloud, "signatures", username, "user_info.json")
        user_info = {}

        if os.path.exists(user_info_path):
            try:
                with open(user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
                print(f"[OK] Informations entrepreneur chargees: {user_info}")
            except Exception as e:
                print(f"[WARN] Erreur chargement user_info.json: {e}")

        # Anglais: +1px vers le haut pour les infos entrepreneur
        entrepreneur_y_adjust = 1 if language == 'en' else 0

        # Afficher prénom et nom sur la même ligne (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("prenom") and user_info.get("nom"):
            c.setFont("Helvetica", 8)
            nom_complet = f"{user_info['prenom']} {user_info['nom']}"
            c.drawCentredString(166.5, 648.5 + y_offset + entrepreneur_y_adjust, nom_complet)  # 167-0.5=166.5, 648+0.5=648.5
            print(f"[OK] Nom complet ajoute: {nom_complet} a (166.5, {648.5 + y_offset + entrepreneur_y_adjust})")

        # Afficher courriel (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("courriel"):
            c.setFont("Helvetica", 8)
            c.drawCentredString(166.5, 632.5 + y_offset + entrepreneur_y_adjust, user_info['courriel'])  # 167-0.5=166.5, 632+0.5=632.5
            print(f"[OK] Courriel ajoute: {user_info['courriel']} a (166.5, {632.5 + y_offset + entrepreneur_y_adjust})")

        # Afficher téléphone (0.5px plus à gauche, 0.5px plus haut)
        if user_info.get("telephone"):
            c.setFont("Helvetica", 8)
            c.drawCentredString(166.5, 616.5 + y_offset + entrepreneur_y_adjust, user_info['telephone'])  # 167-0.5=166.5, 616+0.5=616.5
            print(f"[OK] Telephone ajoute: {user_info['telephone']} a (166.5, {616.5 + y_offset + entrepreneur_y_adjust})")

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
                y_entrepreneur = 112.5 + y_offset
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

    # Ajouter la page 2 si elle existe dans le template (pour template anglais)
    if len(background.pages) > 1:
        page2 = background.pages[1]
        writer.add_page(page2)
        print(f"[PDF] Page 2 du template ajoutée")

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output
