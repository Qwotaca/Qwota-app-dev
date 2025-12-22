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

def generate_facture_pdf(nom: str, prenom: str, adresse: str, prix: str, depot: str = "0", telephone: str = "", courriel: str = "", endroit: str = "", item: str = "", part: str = "", produit: str = "", payer_par: str = "", username: str = "", temps: str = "") -> BytesIO:
    print(f"[DEBUG FACTURE] Téléphone reçu: '{telephone}'")
    print(f"[DEBUG FACTURE] Courriel reçu: '{courriel}'")
    print(f"[DEBUG FACTURE] Endroit reçu: '{endroit}'")
    print(f"[DEBUG FACTURE] Item reçu: '{item}'")
    print(f"[DEBUG FACTURE] Part reçu: '{part}'")
    print(f"[DEBUG FACTURE] Produit reçu: '{produit}'")
    print(f"[DEBUG FACTURE] Payer par reçu: '{payer_par}'")

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
    tps = round(montant * 0.05, 2)
    tvq = round(montant * 0.09975, 2)

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

    # === ENDROIT (identique à generate_pdf.py) ===
    c.setFont("Helvetica", 7.5)
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


    c.setFont("Helvetica", 8.5)
    c.drawRightString(211, 148.5, prix_formate)  # Prix 8px plus à droite (203+8=211)
    c.drawRightString(211, 123.5, tps_f)  # TPS 8px plus à droite (203+8=211)
    c.drawRightString(211, 98.5, tvq_f)  # TVQ 8px plus à droite (203+8=211)

    # Dépôt à la position exacte de generate_pdf.py
    c.drawCentredString(331, 188.5, depot_f)

    c.drawRightString(211, 73.5, total_f)  # Total 8px plus à droite (203+8=211)

    # === ITEM ET PRIX (identique à generate_pdf.py) ===
    c.setFont("Helvetica", 8.5)
    c.drawString(76, 249.5, item)
    c.drawString(476, 249.5, temps)
    c.drawString(310, 305.5, temps)

    # Prix avec dollar sur la même ligne (position 381, 249.5)
    try:
        prix_val = float(prix.replace("$", "").replace(",", ".").replace(" ", ""))
        prix_formate = f"{prix_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    except:
        prix_val = 0
        prix_formate = ""
    prix_avec_dollar = f"{prix_formate} $" if prix_formate else ""
    c.drawString(381, 249.5, prix_avec_dollar)

    # === PRODUIT / COULEURS (identique à generate_pdf.py) ===
    lines_produit_raw = [line.strip() for line in produit.split("\n") if line.strip()]

    font_size_produit = 7.5
    line_height_produit = font_size_produit * 1.4
    x_produit = 403
    y_produit = 458.5
    max_width_produit = 135
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
    # Code identique à generate_pdf.py
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
    # Code identique à generate_pdf.py
    produit_text = produit.lower()
    payer_par_text = payer_par.lower()

    print(f"[DEBUG FACTURE] Détection mots-clés:")
    print(f"[DEBUG FACTURE] produit_text: '{produit_text}'")
    print(f"[DEBUG FACTURE] payer_par_text: '{payer_par_text}'")

    xlavage = "lavage" in produit_text
    xsablage = "sablage" in produit_text
    xappret = "apprêt" in produit_text
    xreparations = "réparations" in produit_text
    xgrattage = "grattage" in produit_text
    xvirement = "virement" in payer_par_text or "interac" in payer_par_text
    xcheque = "chèque" in payer_par_text or "cheque" in payer_par_text

    print(f"[DEBUG FACTURE] Détections:")
    print(f"[DEBUG FACTURE] xvirement: {xvirement} (cherche 'virement' ou 'interac' dans '{payer_par_text}')")
    print(f"[DEBUG FACTURE] xcheque: {xcheque} (cherche 'chèque' ou 'cheque' dans '{payer_par_text}')")

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
