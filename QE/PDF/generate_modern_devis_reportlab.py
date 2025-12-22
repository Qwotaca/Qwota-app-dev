"""
Générateur de PDF moderne pour devis de peinture
Utilise ReportLab avec design rouge/blanc/gris et splash de peinture
"""

from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


def draw_paint_splashes(c, width, height):
    """Dessine des formes de splash de peinture en arrière-plan"""
    # Splash rouge en haut à droite
    c.setFillColor(HexColor('#dc2626'))
    c.setFillAlpha(0.08)
    c.circle(width - 50, height - 50, 150, fill=1, stroke=0)

    # Splash rouge en bas à gauche
    c.setFillColor(HexColor('#dc2626'))
    c.setFillAlpha(0.08)
    c.circle(50, 50, 175, fill=1, stroke=0)

    # Splash gris à droite
    c.setFillColor(HexColor('#6b7280'))
    c.setFillAlpha(0.06)
    c.circle(width + 50, height/2, 125, fill=1, stroke=0)

    # Reset alpha
    c.setFillAlpha(1)


def draw_header(c, x, y, data):
    """Dessine l'en-tête avec logo et informations"""
    # Logo placeholder
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1.5)
    c.setDash([4, 3])
    c.rect(x, y - 80, 180, 80, fill=0)
    c.setDash([])
    c.setFillColor(HexColor('#9ca3af'))
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(x + 90, y - 45, "VOTRE LOGO ICI")

    # Title DEVIS
    c.setFillColor(HexColor('#dc2626'))
    c.setFont("Helvetica-Bold", 28)
    c.drawRightString(x + 550, y - 20, "DEVIS")

    # Numéro et date
    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica", 11)
    c.drawRightString(x + 550, y - 40, f"N° {data.get('num', '')}")
    c.drawRightString(x + 550, y - 55, f"Date: {data.get('date', '')}")

    # Ligne rouge en bas
    c.setStrokeColor(HexColor('#dc2626'))
    c.setLineWidth(3)
    c.line(x, y - 95, x + 550, y - 95)


def draw_company_info_bar(c, x, y, data):
    """Dessine la barre d'informations de l'entreprise"""
    # Rectangle fond gris foncé
    c.setFillColor(HexColor('#1f2937'))
    c.roundRect(x, y - 40, 550, 40, 8, fill=1, stroke=0)

    # Texte blanc
    c.setFillColor(white)
    c.setFont("Helvetica", 9)

    # Ligne 1
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor('#dc2626'))
    c.drawString(x + 10, y - 18, "Assurance:")
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawString(x + 70, y - 18, "Responsabilité civile 2M$ • CNESST")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor('#dc2626'))
    c.drawString(x + 300, y - 18, "Garantie:")
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawString(x + 350, y - 18, "2 ans sur tous nos travaux")

    # Ligne 2
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor('#dc2626'))
    c.drawString(x + 10, y - 32, "Site web:")
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawString(x + 60, y - 32, data.get('site_web', 'www.exemple.com'))

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor('#dc2626'))
    c.drawString(x + 300, y - 32, "Téléphone:")
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawString(x + 360, y - 32, data.get('telephone_entreprise', ''))


def draw_section_title(c, x, y, title):
    """Dessine un titre de section avec bordure rouge"""
    c.setFillColor(HexColor('#dc2626'))
    c.rect(x, y - 12, 4, 14, fill=1, stroke=0)

    c.setFillColor(HexColor('#1f2937'))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x + 10, y - 10, title)


def draw_client_section(c, x, y, data):
    """Dessine la section informations client"""
    draw_section_title(c, x, y, "INFORMATIONS CLIENT")

    # Rectangle fond
    c.setFillColor(HexColor('#f9fafb'))
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1)
    c.roundRect(x, y - 95, 550, 75, 8, fill=1, stroke=1)

    # Labels et valeurs
    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica-Bold", 9)

    fields = [
        ("NOM", data.get('nom', ''), x + 10, y - 30),
        ("PRÉNOM", data.get('prenom', ''), x + 285, y - 30),
        ("ADRESSE", data.get('adresse', '').split(',')[0] if data.get('adresse') else '', x + 10, y - 50),
        ("VILLE", data.get('adresse', '').split(',')[1].strip() if ',' in data.get('adresse', '') else '', x + 285, y - 50),
        ("CODE POSTAL", data.get('adresse', '').split(',')[2].replace('QC', '').strip() if len(data.get('adresse', '').split(',')) > 2 else '', x + 10, y - 70),
        ("TÉLÉPHONE", data.get('telephone', ''), x + 285, y - 70),
        ("COURRIEL", data.get('courriel', ''), x + 10, y - 90),
    ]

    for label, value, fx, fy in fields:
        # Label
        c.setFillColor(HexColor('#6b7280'))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(fx, fy, label)

        # Valeur
        c.setFillColor(HexColor('#1f2937'))
        c.setFont("Helvetica", 11)
        c.drawString(fx, fy - 12, str(value))

        # Ligne de séparation
        c.setStrokeColor(HexColor('#d1d5db'))
        c.setLineWidth(0.5)
        width = 265 if fx == x + 10 else 255
        c.line(fx, fy - 15, fx + width, fy - 15)


def draw_entrepreneur_section(c, x, y, data):
    """Dessine la section informations entrepreneur"""
    draw_section_title(c, x, y, "INFORMATIONS ENTREPRENEUR")

    # Rectangle fond rouge clair
    c.setFillColor(HexColor('#fef2f2'))
    c.setStrokeColor(HexColor('#fecaca'))
    c.setLineWidth(1)
    c.roundRect(x, y - 70, 550, 60, 8, fill=1, stroke=1)

    # Labels et valeurs en 3 colonnes
    c.setFont("Helvetica-Bold", 9)

    fields = [
        ("NEQ", data.get('neq', '1171602284'), x + 10, y - 25),
        ("RBQ", data.get('rbq', '1229001821 T-0001'), x + 195, y - 25),
        ("LICENCE", data.get('licence', '70534 PRO(T-0001)'), x + 380, y - 25),
        ("TPS", data.get('tps_num', '122290'), x + 10, y - 50),
        ("TVQ", data.get('tvq_num', '653'), x + 195, y - 50),
        ("ADRESSE", data.get('adresse_siege', 'Sainte Rose, (H7L 5R7)'), x + 380, y - 50),
    ]

    for label, value, fx, fy in fields:
        c.setFillColor(HexColor('#991b1b'))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(fx, fy, label)

        c.setFillColor(HexColor('#1f2937'))
        c.setFont("Helvetica", 10)
        c.drawString(fx, fy - 12, str(value))


def draw_work_table(c, x, y, endroits_data):
    """Dessine le tableau des endroits à peinturer"""
    draw_section_title(c, x, y, "ENDROITS À PEINTURER")

    # Créer les données du tableau
    table_data = [
        ['Endroit', 'Lavage', 'Grattage', 'Plâtrage', 'Sablage', 'Apprêt', 'Produits/Détails']
    ]

    for endroit in endroits_data:
        row = [
            endroit.get('endroit', ''),
            '✓' if endroit.get('lavage') else '',
            '✓' if endroit.get('grattage') else '',
            '✓' if endroit.get('platrage') else '',
            '✓' if endroit.get('sablage') else '',
            '✓' if endroit.get('appret') else '',
            endroit.get('details', '')
        ]
        table_data.append(row)

    # Si pas de données, ajouter une ligne vide
    if len(table_data) == 1:
        table_data.append(['', '', '', '', '', '', ''])

    # Créer le tableau
    col_widths = [120, 45, 50, 50, 45, 45, 195]
    table = Table(table_data, colWidths=col_widths)

    # Style du tableau
    style = TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (5, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (5, -1), 'CENTER'),
        ('TEXTCOLOR', (1, 1), (5, -1), HexColor('#dc2626')),

        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor('#1f2937')),

        # Alternance de couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9fafb')]),
    ])

    table.setStyle(style)
    table.wrapOn(c, 550, 400)
    table.drawOn(c, x, y - 15 - (len(table_data) * 25))

    return y - 20 - (len(table_data) * 25)


def draw_work_details(c, x, y, data):
    """Dessine les détails des travaux"""
    # Produits/Couleurs
    c.setFillColor(HexColor('#f9fafb'))
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1)
    c.roundRect(x, y - 100, 265, 100, 8, fill=1, stroke=1)

    c.setFillColor(HexColor('#dc2626'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y - 18, "[PACKAGE] PRODUITS / COULEURS")

    produits = data.get('produit', '')
    if produits:
        lines = [line.strip() for line in produits.split('\n') if line.strip()]
        c.setFillColor(HexColor('#374151'))
        c.setFont("Helvetica", 9)
        text_y = y - 35
        for line in lines[:7]:  # Max 7 lignes
            c.drawString(x + 10, text_y, f"• {line}")
            text_y -= 12

    # Particularités
    c.setFillColor(HexColor('#f9fafb'))
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.roundRect(x + 285, y - 100, 265, 100, 8, fill=1, stroke=1)

    c.setFillColor(HexColor('#dc2626'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 295, y - 18, "[FIX] PARTICULARITÉS")

    part = data.get('part', '')
    if part:
        lines = [line.strip() for line in part.split('\n') if line.strip()]
        c.setFillColor(HexColor('#374151'))
        c.setFont("Helvetica", 9)
        text_y = y - 35
        for line in lines[:7]:  # Max 7 lignes
            c.drawString(x + 295, text_y, f"• {line}")
            text_y -= 12


def draw_dates_section(c, x, y, data):
    """Dessine la section des dates"""
    # Date soumission
    c.setFillColor(white)
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1)
    c.roundRect(x, y - 40, 265, 40, 8, fill=1, stroke=1)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 10, y - 18, "[DATE] DATE APPROXIMATIVE DE LA SOUMISSION")

    c.setFillColor(HexColor('#1f2937'))
    c.setFont("Helvetica", 11)
    c.drawString(x + 10, y - 32, data.get('date', ''))

    # Date travaux
    c.setFillColor(white)
    c.roundRect(x + 285, y - 40, 265, 40, 8, fill=1, stroke=1)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 295, y - 18, "🛠️ DATE APPROXIMATIVE DES TRAVAUX")

    c.setFillColor(HexColor('#1f2937'))
    c.setFont("Helvetica", 11)
    c.drawString(x + 295, y - 32, data.get('date2', ''))


def draw_payment_section(c, x, y, data):
    """Dessine la section paiement"""
    # Calculer les montants
    montant_base = float(data.get('prix', 0))
    tps = montant_base * 0.05
    tvq = montant_base * 0.09975
    total = montant_base + tps + tvq

    def format_currency(amount):
        formatted = f"{amount:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        return formatted

    # Rectangle principal rouge
    c.setFillColor(HexColor('#fef2f2'))
    c.setStrokeColor(HexColor('#dc2626'))
    c.setLineWidth(2)
    c.roundRect(x, y - 110, 550, 110, 8, fill=1, stroke=1)

    # Titre
    c.setFillColor(HexColor('#dc2626'))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x + 275, y - 20, "[MONEY] MODALITÉS DE PAIEMENT")

    # Options de paiement à gauche
    c.setFillColor(HexColor('#1f2937'))
    c.setFont("Helvetica", 9)
    c.drawString(x + 15, y - 45, f"Dépôt requis: Minimum {data.get('depot_pct', 25)}% pour réserver")

    c.setFont("Helvetica", 10)
    c.rect(x + 15, y - 65, 10, 10, fill=0)
    c.drawString(x + 30, y - 63, f"Virement Interac à: {data.get('email_paiement', '')}")

    c.rect(x + 15, y - 82, 10, 10, fill=0)
    c.drawString(x + 30, y - 80, "Chèque")

    c.setFillColor(HexColor('#991b1b'))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 15, y - 100, "Validité: Cette soumission est valide pendant 15 jours")

    # Montants à droite
    box_x = x + 380
    c.setFillColor(white)
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1)
    c.roundRect(box_x, y - 95, 155, 80, 6, fill=1, stroke=1)

    amounts = [
        ("Montant des travaux", format_currency(montant_base), y - 45),
        ("TPS (5%)", format_currency(tps), y - 60),
        ("TVQ (9.975%)", format_currency(tvq), y - 75),
    ]

    for label, amount, ay in amounts:
        c.setFillColor(HexColor('#1f2937'))
        c.setFont("Helvetica", 10)
        c.drawString(box_x + 10, ay, label)
        c.drawRightString(box_x + 145, ay, f"{amount} $")

        c.setStrokeColor(HexColor('#e5e7eb'))
        c.setLineWidth(0.5)
        c.line(box_x + 10, ay - 3, box_x + 145, ay - 3)

    # Total
    c.setStrokeColor(HexColor('#dc2626'))
    c.setLineWidth(2)
    c.line(box_x + 10, y - 82, box_x + 145, y - 82)

    c.setFillColor(HexColor('#dc2626'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(box_x + 10, y - 95, "TOTAL")
    c.drawRightString(box_x + 145, y - 95, f"{format_currency(total)} $")


def draw_signatures(c, x, y, data):
    """Dessine la section signatures"""
    # Signature entrepreneur
    c.setStrokeColor(HexColor('#e5e7eb'))
    c.setLineWidth(1)
    c.roundRect(x, y - 80, 265, 80, 8, fill=0, stroke=1)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 10, y - 18, "ENTREPRENEUR")

    c.setStrokeColor(HexColor('#1f2937'))
    c.setLineWidth(2)
    c.line(x + 10, y - 55, x + 255, y - 55)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + 132, y - 65, f"Nom: {data.get('nom_entrepreneur', '')}")
    c.drawCentredString(x + 132, y - 75, "Date: _______________")

    # Signature client
    c.roundRect(x + 285, y - 80, 265, 80, 8, fill=0, stroke=1)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 295, y - 18, "CLIENT")

    c.setStrokeColor(HexColor('#1f2937'))
    c.setLineWidth(2)
    c.line(x + 295, y - 55, x + 540, y - 55)

    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + 417, y - 65, "Signature")
    c.drawCentredString(x + 417, y - 75, "Date: _______________")


def generate_modern_devis_pdf(data: dict) -> BytesIO:
    """
    Génère un PDF moderne de devis avec ReportLab

    Args:
        data: Dictionnaire avec toutes les données du devis

    Returns:
        BytesIO contenant le PDF
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Dessiner les splashes en arrière-plan
    draw_paint_splashes(c, width, height)

    # Marges
    margin_x = 0.4 * inch
    current_y = height - 0.4 * inch

    # Header
    draw_header(c, margin_x, current_y, data)
    current_y -= 115

    # Company info bar
    draw_company_info_bar(c, margin_x, current_y, data)
    current_y -= 60

    # Client section
    draw_client_section(c, margin_x, current_y, data)
    current_y -= 115

    # Entrepreneur section
    draw_entrepreneur_section(c, margin_x, current_y, data)
    current_y -= 90

    # Ligne d'accentuation
    c.setStrokeColor(HexColor('#dc2626'))
    c.setLineWidth(2)
    c.line(margin_x, current_y, margin_x + 550, current_y)
    current_y -= 15

    # Work table
    endroits = data.get('endroits', [])
    current_y = draw_work_table(c, margin_x, current_y, endroits)
    current_y -= 15

    # Work details
    draw_work_details(c, margin_x, current_y, data)
    current_y -= 115

    # Dates
    draw_dates_section(c, margin_x, current_y, data)
    current_y -= 55

    # Payment
    draw_payment_section(c, margin_x, current_y, data)
    current_y -= 125

    # Signatures
    draw_signatures(c, margin_x, current_y, data)

    # Footer
    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica", 7)
    footer_text = f"Je suis satisfait des travaux effectués par {data.get('nom_entreprise', 'Qualité Étudiants')}"
    c.drawCentredString(width / 2, 0.3 * inch, footer_text)

    # Finaliser
    c.save()
    buffer.seek(0)
    return buffer


# Test
if __name__ == "__main__":
    test_data = {
        'num': 'DEV-2024-001',
        'date': '2024-10-05',
        'nom': 'Tremblay',
        'prenom': 'Jean',
        'adresse': '123 Rue Principale, Montréal, QC, H1A 1A1',
        'telephone': '514-555-1234',
        'courriel': 'jean.tremblay@example.com',
        'prix': '2500.00',
        'date2': '2024-10-15',
        'produit': 'Peinture Benjamin Moore - Blanc Dove\nFini mat pour plafonds\nFini satin pour murs',
        'part': 'Protection complète des planchers\nDéplacement des meubles légers\nNettoyage complet après travaux',
        'endroits': [
            {
                'endroit': 'Salon',
                'lavage': True,
                'grattage': True,
                'platrage': False,
                'sablage': False,
                'appret': True,
                'details': '2 couches - Blanc Dove'
            },
            {
                'endroit': 'Cuisine',
                'lavage': True,
                'grattage': False,
                'platrage': False,
                'sablage': False,
                'appret': True,
                'details': '2 couches - Gris perle'
            },
        ],
        'site_web': 'www.qualiteetudiants.com',
        'telephone_entreprise': '1-855-798-0546',
        'nom_entrepreneur': 'Qualité Étudiants',
        'nom_entreprise': 'Qualité Étudiants',
        'email_paiement': 'paiement@exemple.com',
        'depot_pct': 25
    }

    output_file = os.path.join(os.path.dirname(__file__), 'test_devis_moderne.pdf')
    buffer = generate_modern_devis_pdf(test_data)

    with open(output_file, 'wb') as f:
        f.write(buffer.read())

    print(f"PDF genere avec succes: {output_file}")
