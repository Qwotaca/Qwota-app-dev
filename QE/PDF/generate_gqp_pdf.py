from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from io import BytesIO
from reportlab.lib.utils import ImageReader
from copy import deepcopy
import os

def generate_gqp_pdf(photo_files: list, infos: dict) -> BytesIO:
    # Utiliser chemin absolu pour le template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "pdf", "Ajouter un titre.pdf")
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Divise les images en groupes de 4
    image_groups = [photo_files[i:i+4] for i in range(0, len(photo_files), 4)]

    def draw_photos(images, positions):
        overlay = BytesIO()
        c = canvas.Canvas(overlay, pagesize=letter)
        for file, (x, y) in zip(images, positions):
            file.seek(0)
            print("[DEBUG] Image reçue :", file)
            img = Image.open(file)
            image_reader = ImageReader(img)
            c.drawImage(image_reader, x, y, width=234, height=308, preserveAspectRatio=True, mask='auto')
        c.save()
        overlay.seek(0)
        return PdfReader(overlay).pages[0]


    def shrink_to_fit(c, text, max_width, max_font_size, min_font_size, x, y):
        size = max_font_size
        while size >= min_font_size:
            c.setFont("Helvetica", size)
            if c.stringWidth(text) <= max_width:
                break
            size -= 0.5
        c.drawString(x, y, text)

    def wrap_text_to_width(c, text, max_width, font_size):
        c.setFont("Helvetica", font_size)
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if c.stringWidth(test_line) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines


    # === Coordonnées images
    positions = [
        (67, 383), 
        (312, 383), 
        (67, 65),  
        (312, 65)  
    ]

    output = BytesIO()

    # === PAGE 1 avec texte ===
    page1 = reader.pages[0]
    overlay_text = BytesIO()
    c = canvas.Canvas(overlay_text, pagesize=letter)

    # Texte infos
    # Coordonnées alignées à gauche
    c.setFont("Helvetica", 12)

    # Nom complet (fixe)
    c.drawString(99, 694, f"{infos.get('prenom', '')} {infos.get('nom', '')}".strip())

    # Téléphone (fixe)
    c.drawString(129, 667.5, infos.get("telephone", ""))

    # Adresse (max 190px)
    adresse = infos.get("adresse", "")
    adresse_simplifiee = adresse.split(",")[:2]
    adresse_finale = ", ".join(adresse_simplifiee).strip()
    shrink_to_fit(c, adresse_finale, 190, 12, 6, 361, 694.5)

    # Courriel (max 190px)
    shrink_to_fit(c, infos.get("courriel", ""), 190, 12, 6, 361, 668)

    # Heure et Montant (fixes)
    c.drawString(172, 122, infos.get("heure", ""))
    c.drawString(358, 122, infos.get("montant", ""))  # Déplacé de 353 à 358 (+5px)

    # ------------------ Bloc ÉTAPES (à gauche) ------------------
    base_font_size = 12
    min_font_size = 7
    box_width = 238
    box_height = 380
    line_spacing = 2

    
    box_y = 554 - box_height + 16
    etapes_text = infos.get("etapes", "").strip()
    font_size_etapes = base_font_size
    final_lines_etapes = []

    while font_size_etapes >= min_font_size:
        wrapped = []
        for line in etapes_text.split("\n"):
            sub_lines = wrap_text_to_width(c, line, box_width, font_size_etapes)
            wrapped += sub_lines
            wrapped.append("")  # ← ajoute saut de ligne entre les étapes
        total_height = len(wrapped) * (font_size_etapes + line_spacing)
        if total_height <= box_height:
            final_lines_etapes = wrapped
            break
        font_size_etapes -= 1

    # Texte étapes
    c.setFont("Helvetica", font_size_etapes)  # ← police normale
    y = box_y + box_height - font_size_etapes
    for line in final_lines_etapes:
        c.drawString(67, y, line)
        y -= font_size_etapes + line_spacing


    # ------------------ Bloc ENDROIT (à droite) ------------------
    endroit_text = infos.get("endroit", "").strip()
    font_size_endroit = base_font_size
    final_lines_endroit = []

    while font_size_endroit >= min_font_size:
        wrapped = []
        for line in endroit_text.split("\n"):
            wrapped += wrap_text_to_width(c, line, box_width, font_size_endroit)
        total_height = len(wrapped) * (font_size_endroit + line_spacing)
        if total_height <= box_height:
            final_lines_endroit = wrapped
            break
        font_size_endroit -= 1

    # Texte Endroit
    c.setFont("Helvetica", font_size_endroit)
    y_endroit = box_y + box_height - font_size_endroit
    for line in final_lines_endroit:
        c.drawString(310, y_endroit, line)
        y_endroit -= font_size_endroit + line_spacing





    # Finalisation
    c.save()
    overlay_text.seek(0)
    page1.merge_page(PdfReader(overlay_text).pages[0])
    writer.add_page(page1)

    for i, group in enumerate(image_groups):
        page_index = i + 1
        if page_index >= len(reader.pages):
            break
        original_page = reader.pages[page_index]
        page = deepcopy(original_page)  # COPIE PROFONDE pour ne pas modifier l'original
        overlay = draw_photos(group, positions[:len(group)])
        page.merge_page(overlay)
        writer.add_page(page)

    writer.write(output)
    output.seek(0)
    return output
