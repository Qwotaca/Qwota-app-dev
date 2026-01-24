"""
Générateur de PDF moderne pour devis de peinture
Utilise le template HTML moderne avec design rouge/blanc/gris
"""

from datetime import datetime
import os
from io import BytesIO
import sys

# Importer weasyprint pour conversion HTML -> PDF
try:
    from weasyprint import HTML, CSS
except ImportError:
    print("[WARN] WeasyPrint n'est pas installé. Installation...")
    os.system(f"{sys.executable} -m pip install weasyprint")
    from weasyprint import HTML, CSS


def format_currency(value):
    """Formate un montant en format canadien-français"""
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace(' ', '').replace(',', '.')
        amount = float(value)
        formatted = f"{amount:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        return formatted
    except:
        return "0,00"


def generate_work_rows(endroits_data):
    """
    Génère les rangées HTML pour le tableau des endroits à peinturer

    endroits_data: liste de dict avec:
    - endroit: nom de l'endroit
    - lavage: bool
    - grattage: bool
    - platrage: bool
    - sablage: bool
    - appret: bool
    - details: texte des détails
    """
    rows = []
    for endroit in endroits_data:
        row = f"""
        <tr>
            <td>{endroit.get('endroit', '')}</td>
            <td class="checkbox-cell">
                {'<span style="color: #dc2626; font-weight: bold;">✓</span>' if endroit.get('lavage') else ''}
            </td>
            <td class="checkbox-cell">
                {'<span style="color: #dc2626; font-weight: bold;">✓</span>' if endroit.get('grattage') else ''}
            </td>
            <td class="checkbox-cell">
                {'<span style="color: #dc2626; font-weight: bold;">✓</span>' if endroit.get('platrage') else ''}
            </td>
            <td class="checkbox-cell">
                {'<span style="color: #dc2626; font-weight: bold;">✓</span>' if endroit.get('sablage') else ''}
            </td>
            <td class="checkbox-cell">
                {'<span style="color: #dc2626; font-weight: bold;">✓</span>' if endroit.get('appret') else ''}
            </td>
            <td>{endroit.get('details', '')}</td>
        </tr>
        """
        rows.append(row)

    return '\n'.join(rows) if rows else '<tr><td colspan="7" style="text-align: center; color: #9ca3af;">Aucun endroit spécifié</td></tr>'


def generate_modern_devis_pdf(data: dict) -> BytesIO:
    """
    Génère un PDF moderne à partir des données fournies

    Args:
        data: Dictionnaire contenant toutes les informations du devis

    Returns:
        BytesIO contenant le PDF généré
    """

    # Charger le template HTML
    template_path = os.path.join(os.path.dirname(__file__), 'devis_template_modern.html')

    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Calculer les montants
    montant_base = float(data.get('prix', 0))
    tps = montant_base * 0.05
    tvq = montant_base * 0.09975
    total = montant_base + tps + tvq

    # Préparer les données des endroits
    endroits_data = data.get('endroits', [])
    work_rows_html = generate_work_rows(endroits_data)

    # Formater les produits/couleurs (sans ajouter de bullets, ils viennent du frontend)
    produits_couleurs = data.get('produit', '')
    if produits_couleurs:
        produits_lines = [line.strip() for line in produits_couleurs.split('\n') if line.strip()]
        produits_formatted = '<br>'.join(produits_lines)
    else:
        produits_formatted = ''

    # Formater les particularités (sans ajouter de bullets, ils viennent du frontend)
    particularites = data.get('part', '')
    if particularites:
        part_lines = [line.strip() for line in particularites.split('\n') if line.strip()]
        particularites_formatted = '<br>'.join(part_lines)
    else:
        particularites_formatted = ''

    # Remplacer les placeholders dans le template
    replacements = {
        '{{NUMERO}}': str(data.get('num', '')),
        '{{DATE}}': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        '{{SITE_WEB}}': data.get('site_web', 'www.exemple.com'),
        '{{TELEPHONE_ENTREPRISE}}': data.get('telephone_entreprise', '1-855-XXX-XXXX'),

        # Client
        '{{NOM}}': data.get('nom', ''),
        '{{PRENOM}}': data.get('prenom', ''),
        '{{ADRESSE}}': data.get('adresse', '').split(',')[0] if data.get('adresse') else '',
        '{{VILLE}}': data.get('adresse', '').split(',')[1].strip() if ',' in data.get('adresse', '') else '',
        '{{CODE_POSTAL}}': data.get('adresse', '').split(',')[2].replace('QC', '').strip() if len(data.get('adresse', '').split(',')) > 2 else '',
        '{{TELEPHONE}}': data.get('telephone', ''),
        '{{COURRIEL}}': data.get('courriel', ''),

        # Entrepreneur
        '{{NEQ}}': data.get('neq', '1171602284'),
        '{{RBQ}}': data.get('rbq', '1229001821 T-0001'),
        '{{LICENCE}}': data.get('licence', '70534 PRO(T-0001)'),
        '{{TPS_NUM}}': data.get('tps_num', '122290'),
        '{{TVQ_NUM}}': data.get('tvq_num', '653 boulevard Curé-Labelle'),
        '{{ADRESSE_SIEGE}}': data.get('adresse_siege', 'Sainte Rose, (H7L 5R7)'),

        # Travaux
        '{{WORK_ROWS}}': work_rows_html,
        '{{PRODUITS_COULEURS}}': produits_formatted,
        '{{PARTICULARITES}}': particularites_formatted,

        # Dates
        '{{DATE_SOUMISSION}}': data.get('date', ''),
        '{{DATE_TRAVAUX}}': data.get('date2', ''),

        # Paiement
        '{{DEPOT_POURCENTAGE}}': str(data.get('depot_pct', 25)),
        '{{EMAIL_PAIEMENT}}': data.get('email_paiement', data.get('courriel', '')),
        '{{MONTANT}}': format_currency(montant_base),
        '{{TPS}}': format_currency(tps),
        '{{TVQ}}': format_currency(tvq),
        '{{TOTAL}}': format_currency(total),

        # Signatures
        '{{NOM_ENTREPRENEUR}}': data.get('nom_entrepreneur', ''),
        '{{NOM_ENTREPRISE}}': data.get('nom_entreprise', 'Qualité Étudiants'),
    }

    # Appliquer tous les remplacements
    html_content = html_template
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, str(value))

    # Générer le PDF
    pdf_output = BytesIO()
    HTML(string=html_content).write_pdf(pdf_output)
    pdf_output.seek(0)

    return pdf_output


def generate_modern_devis_file(data: dict, output_path: str) -> bool:
    """
    Génère un fichier PDF moderne

    Args:
        data: Dictionnaire contenant les données du devis
        output_path: Chemin du fichier de sortie

    Returns:
        True si succès, False sinon
    """
    try:
        pdf_buffer = generate_modern_devis_pdf(data)

        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.read())

        print(f"[OK] PDF généré avec succès: {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Erreur lors de la génération du PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test de génération
if __name__ == "__main__":
    # Données de test
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
            {
                'endroit': 'Chambre principale',
                'lavage': True,
                'grattage': True,
                'platrage': True,
                'sablage': False,
                'appret': True,
                'details': '2 couches - Beige chaud'
            }
        ],
        'site_web': 'www.qualiteetudiants.com',
        'telephone_entreprise': '1-855-798-0546',
        'nom_entrepreneur': 'Qualité Étudiants',
        'nom_entreprise': 'Qualité Étudiants'
    }

    # Générer le PDF de test
    output_file = os.path.join(os.path.dirname(__file__), 'test_devis_moderne.pdf')
    generate_modern_devis_file(test_data, output_file)
