from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit, ImageReader
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import os
import sys
import json
import random
import re

# Détection OS pour chemins de fichiers (même logique que main.py)
if sys.platform == 'win32':
    # Windows - chemin relatif depuis la racine du projet
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

BASE_DIR = os.getcwd()
FACTURE_NUM_FILE = os.path.join(BASE_DIR, "factures", "used_nums.json")
os.makedirs(os.path.dirname(FACTURE_NUM_FILE), exist_ok=True)

def generate_unique_facture_num():
    used = set()
    if os.path.exists(FACTURE_NUM_FILE):
        with open(FACTURE_NUM_FILE, "r") as f:
            used = set(json.load(f))
    while True:
        part1 = f"{random.randint(0, 999999):06}"
        part2 = f"{random.randint(0, 99):02}"
        num = f"{part1}-{part2}"
        if num not in used:
            used.add(num)
            with open(FACTURE_NUM_FILE, "w") as f:
                json.dump(list(used), f)
            return num

def formater_prix(prix_str):
    try:
        montant = float(prix_str.replace("$", "").replace(",", ".").replace(" ", ""))
    except:
        montant = 0.0
    return f"{montant:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ") + " $"

def generate_facture_pdf(nom: str, prenom: str, adresse: str, prix: str, depot: str = "0", telephone: str = "", courriel: str = "", endroit: str = "", item: str = "", part: str = "", produit: str = "", payer_par: str = "", username: str = "", temps: str = "", language: str = "fr") -> BytesIO:
    print(f"[DEBUG FACTURE] Téléphone reçu: '{telephone}'")
    print(f"[DEBUG FACTURE] Courriel reçu: '{courriel}'")
    print(f"[DEBUG FACTURE] Endroit reçu: '{endroit}'")
    print(f"[DEBUG FACTURE] Endroit repr: {repr(endroit)}")
    print(f"[DEBUG FACTURE] Item reçu: '{item}'")
    print(f"[DEBUG FACTURE] Part reçu: '{part}'")
    print(f"[DEBUG FACTURE] Produit reçu: '{produit}'")
    print(f"[DEBUG FACTURE] Payer par reçu: '{payer_par}'")

    # Choisir le template selon la langue
    if language == 'en':
        template_path = os.path.join(BASE_DIR, "QE", "PDF", "pdf", "facture-en.pdf")
    else:
        template_path = os.path.join(BASE_DIR, "QE", "PDF", "pdf", "facture.pdf")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template non trouvé : {template_path}")

    reader = PdfReader(template_path)
    writer = PdfWriter()

    try:
        montant = float(prix.replace("$", "").replace(",", ".").replace(" ", ""))
    except:
        montant = 0.0

    try:
        depot_val = float(depot.replace("$", "").replace(",", ".").replace(" ", ""))
    except:
        depot_val = 0.0

    # Les taxes sont calculées sur le montant de base complet
    if language == 'fr':
        # Français: TPS 5% + TVQ 9.975%
        tps = round(montant * 0.05, 2)
        tvq = round(montant * 0.09975, 2)
        tvh = 0
    else:
        # Anglais: TVH/HST 13%
        tps = 0
        tvq = 0
        tvh = round(montant * 0.13, 2)

    facture_num = generate_unique_facture_num()

    rue = ville = code_postal = ""
    try:
        parts = [p.strip() for p in adresse.split(",")]
        if len(parts) >= 3:
            rue = parts[0]
            ville = parts[1]
            code_postal = parts[2].replace("QC", "").strip()
    except:
        pass

    # Formatage sans le symbole $
    try:
        prix_formate = f"{montant:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        prix_formate = ""

    if language == 'fr':
        try:
            tps_f = f"{tps:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        except:
            tps_f = ""

        try:
            tvq_f = f"{tvq:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        except:
            tvq_f = ""

        try:
            # Total = montant + TPS + TVQ (sans soustraire le dépôt)
            total_avec_taxes = montant + tps + tvq
            total_f = f"{total_avec_taxes:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        except:
            total_f = ""
    else:
        # Anglais: TVH 13%
        try:
            tvh_f = f"{tvh:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        except:
            tvh_f = ""

        try:
            total_avec_taxes = montant + tvh
            total_f = f"{total_avec_taxes:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        except:
            total_f = ""

        tps_f = ""
        tvq_f = ""

    try:
        montant_f = f"{montant:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        montant_f = ""

    depot_f = formater_prix(str(depot_val))  # Garde le $ pour le dépôt

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)


    c.setFillColorRGB(0, 0, 0)
    date = datetime.today().strftime('%d/%m/%Y')

    c.setFont("Helvetica", 7)
    c.drawCentredString(468.5, 762.5, date)

    # Numéro de facture avec police Helvetica-Oblique 9.5 (même que generate_pdf.py)
    c.setFont("Helvetica-Oblique", 9.5)
    c.drawString(295, 761.5, facture_num)

    c.setFont("Helvetica", 8.5)
    c.drawCentredString(308, 736.5, nom)
    c.drawCentredString(447, 736.5, prenom)

    # === AUTO-AJUSTEMENT ADRESSE (identique à generate_pdf.py) ===
    adresse_center_x = 308
    adresse_y = 720
    adresse_max_width = 90

    font_size_rue = 8.5
    min_font_size_rue = 5.0

    while font_size_rue >= min_font_size_rue:
        text_width = c.stringWidth(rue, "Helvetica", font_size_rue)
        if text_width <= adresse_max_width:
            break
        font_size_rue -= 0.2

    c.setFont("Helvetica", font_size_rue)
    c.drawCentredString(adresse_center_x, adresse_y, rue)

    c.setFont("Helvetica", 8.5)
    c.drawCentredString(448, 720, ville)
    c.drawCentredString(308, 703, code_postal)

    # Téléphone avec police Helvetica 8.5 (même que generate_pdf.py ligne 47)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(447, 703, telephone)

    # Courriel avec police Helvetica 8 (même que generate_pdf.py ligne 40)
    c.setFont("Helvetica", 8)
    print(f"[DEBUG FACTURE] Dessin courriel '{courriel}' à position (447, 685.5)")
    c.drawCentredString(447, 685.5, courriel)

    # === ENDROIT (ligne par ligne comme generate_pdf.py) ===
    c.setFont("Helvetica", 7.5)
    x = 81
    y = 460
    max_width = 80
    max_height = 130
    base_font_size = 7.5
    min_font_size = 4.0
    line_height_ratio = 1.75

    # Séparer par \n - chaque endroit = 1 ligne (pas de wrap)
    # Fallback: si pas de \n, essayer de splitter par virgule
    if '\n' in endroit:
        raw_lines = [line.strip() for line in endroit.split('\n') if line.strip()]
    else:
        raw_lines = [line.strip() for line in endroit.split(',') if line.strip()]

    # Fonction pour calculer la taille de police nécessaire pour qu'une ligne tienne sur 1 seule ligne
    def get_font_size_for_line(text, max_size, min_size, max_w):
        size = max_size
        while size >= min_size:
            if c.stringWidth(text, "Helvetica", size) <= max_w:
                return size
            size -= 0.2
        return min_size

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

    c.setFont("Helvetica", 8.5)
    c.drawRightString(211, 149, prix_formate)  # Total avant taxe (+0.5px haut)

    if language == 'fr':
        # Français: TPS, TVQ, Total
        c.drawRightString(211, 123.5, tps_f)  # TPS
        c.drawRightString(211, 98.5, tvq_f)  # TVQ
        c.drawRightString(211, 72.5, total_f)  # Total (-1px bas)
    else:
        # Anglais: TVH en haut, Total en bas
        c.drawRightString(211, 123.5, tvh_f)  # TVH
        c.drawRightString(211, 97.5, total_f)  # Total (-1px bas)

    # Dépôt à la position exacte de generate_pdf.py
    c.drawCentredString(331, 188.5, depot_f)

    # === ITEM ET PRIX ===
    c.setFont("Helvetica", 8.5)

    # Positions des colonnes
    x_item_nom = 76      # Colonne Item (nom)
    x_item_prix = 381    # Colonne Prix
    x_item_duree = 476   # Colonne Durée approx
    y_start = 249.5      # Position Y de départ
    line_height = 12     # Hauteur entre les lignes

    # Parser les items (nouveau format JSON ou ancien format texte)
    try:
        items_list = json.loads(item)
        if isinstance(items_list, list) and len(items_list) > 0:
            # Nouveau format JSON: [{"nom": "...", "prix": "...", "duree": "..."}]
            for i, it in enumerate(items_list):
                y_pos = y_start - (i * line_height)
                if it.get('nom'):
                    c.drawString(x_item_nom, y_pos, it['nom'])
                if it.get('prix'):
                    c.drawString(x_item_prix, y_pos, it['prix'])
                if it.get('duree'):
                    c.drawString(x_item_duree, y_pos, it['duree'])
        else:
            # Liste vide ou format invalide
            c.drawString(x_item_nom, y_start, item if item else "")
    except:
        # Ancien format texte - afficher tel quel
        c.drawString(x_item_nom, y_start, item if item else "")

    c.drawString(310, 305.5, temps)

    # === PRODUIT / COULEURS (identique à generate_pdf.py) ===
    lines_produit_raw = [line.strip() for line in produit.split("\n") if line.strip()]

    font_size_produit = 7.5
    line_height_produit = font_size_produit * 1.4
    x_produit = 403
    y_produit = 294.5
    max_width_produit = 139
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
                current = word
        if current:
            wrapped.append(current)
        return wrapped if wrapped else [text]

    # Ajustement automatique de la taille de police pour que tout rentre
    current_font_size = font_size_produit
    current_line_height = line_height_produit

    print(f"\n[FACTURE PRODUIT] ==================== DEBUT AJUSTEMENT ====================")
    print(f"[FACTURE PRODUIT] Texte brut recu: {len(lines_produit_raw)} lignes")
    print(f"[FACTURE PRODUIT] Hauteur disponible: {max_height_produit}px")
    print(f"[FACTURE PRODUIT] Largeur disponible: {max_width_produit}px")

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

        print(f"[FACTURE PRODUIT] Iteration {iteration}: Taille police={current_font_size}pt | Lignes apres wrap={len(lines_produit)} | Hauteur necessaire={total_height_needed:.2f}px")

        # Si ça rentre, on arrête
        if total_height_needed <= max_height_produit:
            print(f"[FACTURE PRODUIT] OK Tout rentre! Taille finale: {current_font_size}pt")
            break

        # Sinon, réduire la taille
        current_font_size -= 0.25
        print(f"[FACTURE PRODUIT] WARN Trop grand, reduction a {current_font_size}pt")

    # Si on n'a pas de lignes, refaire une dernière fois
    if 'lines_produit' not in locals() or not lines_produit:
        lines_produit = []
        for line in lines_produit_raw:
            lines_produit.extend(wrap_line_produit(line, max_width_produit, current_font_size))

    print(f"[FACTURE PRODUIT] ==================== FIN AJUSTEMENT ====================")
    print(f"[FACTURE PRODUIT] RÉSULTAT FINAL: Taille={current_font_size}pt | Lignes={len(lines_produit)} | Hauteur ligne={current_line_height:.2f}px\n")

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
    # Code identique à generate_pdf.py
    lines_part = [line.strip() for line in part.split("\n") if line.strip()]
    font_size_part = 7.5
    line_height_part = font_size_part * 1.8  # Espacement léger
    x_part = 76
    y_part = 317.5
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
    produit_text = produit
    payer_par_text = payer_par.lower()

    # Parser les sections par endroit (=== NomEndroit ===)
    endroit_pattern = re.compile(r'===\s*(.+?)\s*===')
    endroit_sections = re.split(r'===\s*.+?\s*===', produit_text)

    # Ajustement pour anglais seulement (-0.5px à gauche)
    x_adjust_en = -0.5 if language == 'en' else 0

    # Coordonnées X pour chaque type de préparation (+0.5px droite vs soumission)
    x_coords = {
        "lavage": 188.5 + x_adjust_en,
        "sablage": 329 + x_adjust_en,
        "appret": 375.7 + x_adjust_en,
        "reparations": 282.2 + x_adjust_en,
        "grattage": 235.5 + x_adjust_en,
    }

    y_coord_base = 579     # 578.5 + 0.5 (plus haut)
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

    # Paiement (+0.5px gauche, +1.5px haut)
    xvirement = "virement" in payer_par_text or "interac" in payer_par_text
    xcheque = "chèque" in payer_par_text or "cheque" in payer_par_text

    y_coord_virement = 191    # 189.5 + 1.5
    y_coord_cheque = 180.7    # 179.2 + 1.5

    if xvirement:
        c.drawString(451.2, y_coord_virement, "X")  # 450.7 + 0.5
    if xcheque:
        c.drawString(451.2, y_coord_cheque, "X")    # 450.7 + 0.5

    # === COURRIEL ENTREPRENEUR EN BAS ===
    if username:
        # Charger les informations de l'entrepreneur depuis user_info.json
        user_info_path = os.path.join(base_cloud, "signatures", username, "user_info.json")
        user_info = {}

        if os.path.exists(user_info_path):
            try:
                with open(user_info_path, "r", encoding="utf-8") as f:
                    user_info = json.load(f)
            except Exception as e:
                print(f"[WARN] Erreur chargement user_info.json: {e}")

        # Afficher courriel entrepreneur en petit (même position que dans soumission)
        if user_info.get("courriel"):
            c.setFont("Helvetica", 6)
            # Position identique à generate_pdf.py (au-dessus de la zone signature)
            courriel_x = 80 + 100 + 20 - 25 - 8 - 5 - 4  # = 58
            courriel_y = 112.5 + 30 + 50 - 10 - 5 + 1 - 0.5  # = 178
            c.drawCentredString(courriel_x, courriel_y, user_info['courriel'])

    c.save()
    packet.seek(0)

    overlay = PdfReader(packet)
    page = reader.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output

def save_facture_and_return_url(nom, prenom, adresse, prix, username, depot="0", telephone="", courriel="", endroit="", item="", part="", produit="", payer_par="", temps=""):
    buffer = generate_facture_pdf(nom, prenom, adresse, prix, depot, telephone, courriel, endroit, item, part, produit, payer_par, username, temps)

    folder = os.path.join(base_cloud, "factures_completes", username)
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"facture_{nom}_{prenom}_{timestamp}.pdf".replace(" ", "_")
    filepath = os.path.join(folder, filename)

    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())

    url = f"https://www.qwota.ca/cloud/factures/{username}/{filename}"

    data = {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "prix": prix,
        "telephone": telephone,
        "pdf_url": url
    }

    enregistrer_facture_json(data, username)
    return data

def enregistrer_facture_json(facture_data, username):
    dossier = os.path.join(base_cloud, "factures_completes", username)
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "factures.json")

    data = []
    if os.path.exists(fichier):
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)

    data.append(facture_data)

    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
