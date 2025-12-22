from datetime import datetime
import os
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.utils import simpleSplit

def generate_calcul_pdf(data: dict, language: str = 'fr') -> BytesIO:
    """
    Génère un PDF de calculateur basé sur les données du calculateur Qwota
    Utilise le template templatecalcul.pdf (français) ou pdf-template-soumission-en.pdf (anglais)

    Args:
        data: Données de la soumission
        language: Langue du template ('fr' ou 'en'), par défaut 'fr'
    """
    print(f"DEBUG INT: ========= DÉBUT GÉNÉRATION PDF CALCULATEUR =========")
    print(f"DEBUG INT: Fonction generate_calcul_pdf() appelée")
    print(f"DEBUG INT: Type de data reçue: {type(data)}")
    print(f"DEBUG INT: Clés principales: {list(data.keys()) if data else 'Aucune data'}")
    print(f"DEBUG INT: Langue sélectionnée: {language}")

    # Choisir le template selon la langue - utiliser chemin absolu
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if language == 'en':
        template_path = os.path.join(script_dir, "pdf", "pdf-template-soumission-en.pdf")
    else:
        template_path = os.path.join(script_dir, "pdf", "templatecalcul.pdf")

    # Les templates FR et EN ont la même structure, pas d'ajustement nécessaire
    y_offset = 0

    # DEBUG: Vérifier si le template existe
    print(f"DEBUG INT: Cherche template à: {template_path}")
    print(f"DEBUG INT: Template existe? {os.path.exists(template_path)}")
    if os.path.exists(template_path):
        print(f"DEBUG INT: Template trouvé!")
    else:
        print(f"DEBUG INT: ERREUR - Template introuvable!")
        # Lister les fichiers du dossier pdf
        if os.path.exists("pdf"):
            pdf_files = os.listdir("pdf")
            print(f"DEBUG INT: Fichiers dans pdf/: {pdf_files}")
        else:
            print(f"DEBUG INT: Dossier pdf/ n'existe pas!")
    
    # Créer un calque avec le texte à insérer
    overlay = BytesIO()
    c = canvas.Canvas(overlay, pagesize=letter)
    width, height = letter
    
    # === EN-TÊTE ET TITRE ===
    c.setFont("Helvetica-Bold", 16)
    # Ancien titre supprimé - sera remplacé plus bas
 
    
    # === INFORMATIONS CLIENT ET COÛTS (CÔTE À CÔTE) ===
    client = data.get("client", {})
    nom_client = client.get("name", "")
    adresse_client = client.get("address", "")
    telephone_client = client.get("phone", "")
    date_estimation = client.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    # Préparer les données de coûts pour l'affichage en haut à droite
    costs = data.get("costs", {})
    hours = data.get("hours", {})



    y_pos = height - 80 + y_offset
    

    
    # === LAYOUT DEUX COLONNES : INFORMATIONS CLIENT + DÉTAIL DES COÛTS ===
    # Colonne gauche: Informations client
    left_col_x = 50
    right_col_x = width - 200  # Position à droite
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.Color(31/255, 41/255, 55/255))
    c.drawString(left_col_x, y_pos, "INFORMATIONS CLIENT")
    c.drawString(right_col_x, y_pos, "DÉTAIL DES COÛTS")
    
    y_left = y_pos - 25
    y_right = y_pos - 25
    
    # Informations client (colonne gauche)
    c.setFont("Helvetica", 12)
    c.drawString(left_col_x, y_left, f"Client: {nom_client}")
    y_left -= 18
    c.drawString(left_col_x, y_left, f"Adresse: {adresse_client}")
    y_left -= 18
    c.drawString(left_col_x, y_left, f"Téléphone: {telephone_client}")
    y_left -= 18
    c.drawString(left_col_x, y_left, f"Date: {date_estimation}")
    y_left -= 18
    
    # Détail des coûts (colonne droite)
    def format_price_top(price):
        try:
            if isinstance(price, (int, float)):
                return f"{price:,.2f} $".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
            else:
                val = float(str(price).replace("$", "").replace(",", ".").replace(" ", ""))
                return f"{val:,.2f} $".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        except:
            return "0,00 $"
    
    c.setFont("Helvetica", 11)
    
    # Main d'œuvre - Lavage
    try:
        lavage_cost = float(costs.get("lavage", 0)) if costs.get("lavage", 0) else 0
        if lavage_cost > 0:
            c.drawString(right_col_x, y_right, f"Lavage: {format_price_top(lavage_cost)}")
            y_right -= 14
    except (ValueError, TypeError):
        pass
    
    # Main d'œuvre - Préparation
    try:
        preparation_cost = float(costs.get("preparation", 0)) if costs.get("preparation", 0) else 0
        if preparation_cost > 0:
            c.drawString(right_col_x, y_right, f"Préparation: {format_price_top(preparation_cost)}")
            y_right -= 14
    except (ValueError, TypeError):
        pass
    
    # Main d'œuvre - Peinture
    try:
        peinture_hours = float(hours.get("peinture", 0)) if hours.get("peinture", 0) else 0
        peinture_cost = peinture_hours * 43
        if peinture_cost > 0:
            c.drawString(right_col_x, y_right, f"Peinture: {format_price_top(peinture_cost)}")
            y_right -= 14
    except (ValueError, TypeError):
        pass
    
    # Produits
    try:
        materiaux_base = float(costs.get("materiaux", 0)) if costs.get("materiaux", 0) else 0
        if materiaux_base > 0:
            c.drawString(right_col_x, y_right, f"Produits: {format_price_top(materiaux_base)}")
            y_right -= 14
    except (ValueError, TypeError):
        pass
    
    # Sous-total et marge
    try:
        sous_total = float(costs.get("sousTotal", 0)) if costs.get("sousTotal", 0) else 0
        if sous_total > 0:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(right_col_x, y_right, f"Sous-total: {format_price_top(sous_total)}")
            y_right -= 16
            
            marge_profit = float(costs.get("margeProfit", 0)) if costs.get("margeProfit", 0) else 0
            if marge_profit > 0:
                c.setFont("Helvetica", 11)
                c.drawString(right_col_x, y_right, f"Marge: {format_price_top(marge_profit)}")
                y_right -= 14
                
                total_estime = sous_total + marge_profit
                c.setFont("Helvetica-Bold", 12)
                c.drawString(right_col_x, y_right, f"Total: {format_price_top(total_estime)}")
                y_right -= 16
    except (ValueError, TypeError):
        pass
    
    # === ESPACE ENTRE DÉTAIL DES COÛTS ET PARAMÈTRES ===
    y_right -= 25  # Plus d'espace pour séparer visuellement les sections
    
    # === PARAMÈTRES ===
    parameters = data.get("parameters", {})
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_col_x, y_right, "PARAMÈTRES")
    y_right -= 18
    
    c.setFont("Helvetica", 10)
    # Taux horaire en premier dans les paramètres (dynamique)
    taux_horaire = parameters.get("taux_horaire", 43)  # 43 par défaut si pas trouvé
    c.drawString(right_col_x, y_right, f"Taux horaire: {taux_horaire}$/h")
    y_right -= 12
    
    if parameters.get("profitMargin"):
        c.drawString(right_col_x, y_right, f"Marge: {parameters['profitMargin']}%")
        y_right -= 12
    
    # Espace après les paramètres
    y_right -= 20
    
    # === PRODUITS ET MATÉRIAUX (dans la colonne droite) ===
    product_general = data.get("product", {})
    
    # Chercher les produits appliqués - d'abord dans product_general.products[]
    produits_utilises_droite = []
    
    # 1. Vérifier dans product_general.products[] (produits individuels)
    if product_general and product_general.get("products") and len(product_general["products"]) > 0:
        for i, prod in enumerate(product_general["products"]):
            gallons_appliques = prod.get("gallons", 0)
            if gallons_appliques and gallons_appliques > 0:
                # Déterminer les sections d'application pour ce produit spécifique
                sections_application = []
                
                # Chercher les sections où ce produit est appliqué dans les endroits
                endroits = data.get("endroits", {})
                if endroits:
                    for endroit_id, endroit_info in endroits.items():
                        if isinstance(endroit_info, dict) and endroit_info.get("sections"):
                            for section_id, section_data in endroit_info["sections"].items():
                                product_data = section_data.get("product", {})
                                # Si ce produit spécifique est utilisé dans cette section
                                if (product_data.get("produit") == prod.get("name") or 
                                    (product_data.get("gallons", 0) > 0 and len(product_general["products"]) > 1)):
                                    categorie = endroit_info.get("category", endroit_info.get("title", "Section"))
                                    if categorie not in sections_application:
                                        sections_application.append(categorie)
                
                produits_utilises_droite.append({
                    'produit': prod.get("name", "Produit"),
                    'gallons': gallons_appliques,
                    'section_name': prod.get("sectionName", ""),
                    'sections': sections_application if sections_application else ["Surfaces extérieures"],
                    'prix_unitaire': prod.get("pricePerGallon", prod.get("price", 100)),
                    'cout_total': prod.get("totalCost", gallons_appliques * (prod.get("pricePerGallon", prod.get("price", 100))))
                })
    
    # 2. Si pas de produits individuels, chercher dans les endroits
    if not produits_utilises_droite:
        endroits = data.get("endroits", {})
        if endroits:
            for endroit_id, endroit_info in endroits.items():
                if isinstance(endroit_info, dict) and endroit_info.get("sections"):
                    titre_endroit = endroit_info.get("title", "Endroit")
                    
                    for section_id, section_data in endroit_info["sections"].items():
                        product_data = section_data.get("product", {})
                        if product_data:
                            # Récupérer le nom du produit
                            product_name = product_data.get("produit", "")
                            if not product_name or product_name in ["Produit sélectionné", "Produit", ""]:
                                # Fallback vers product_general.name
                                if product_general and product_general.get("name"):
                                    product_name = product_general["name"]
                                else:
                                    product_name = "Produit appliqué"
                            
                            # Récupérer les gallons appliqués
                            gallons_appliques = product_data.get("gallons", 0)
                            if gallons_appliques and gallons_appliques > 0:
                                produits_utilises_droite.append({
                                    'produit': product_name,
                                    'gallons': gallons_appliques,
                                    'sections': [titre_endroit],
                                    'prix_unitaire': product_data.get("pricePerGallon", product_general.get("price", 100) if product_general else 100),
                                    'cout_total': product_data.get("totalCost", gallons_appliques * (product_data.get("pricePerGallon", product_general.get("price", 100) if product_general else 100)))
                                })
    
    # Afficher les produits dans la colonne droite
    cout_produits_total = (data.get("costs", {}).get("produits_appliques", 0) or 
                          data.get("costs", {}).get("materiaux", 0))
    
    if produits_utilises_droite or cout_produits_total > 0:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(right_col_x, y_right, "PRODUITS")
        y_right -= 18
        
        if produits_utilises_droite:
            # Afficher chaque produit séparément
            for produit in produits_utilises_droite:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(right_col_x, y_right, f"• {produit['produit']}")
                y_right -= 12
                
                c.setFont("Helvetica", 9)
                c.drawString(right_col_x, y_right, f"Quantité: {produit['gallons']} gal")
                y_right -= 10
                
                # Afficher la section spécifique de ce produit (nettoyée)
                if produit.get('section_name'):
                    # Nettoyer le nom de section - garder seulement la catégorie principale
                    section_brute = produit['section_name']
                    
                    # Mapping des catégories principales
                    if "revêtement" in section_brute.lower() or "latte" in section_brute.lower():
                        section_propre = "Revêtement"
                    elif "corniche" in section_brute.lower() or "moulure" in section_brute.lower() or "fascia" in section_brute.lower():
                        section_propre = "Corniches et moulures"  
                    elif "fenêtre" in section_brute.lower() or "fenetre" in section_brute.lower() or "volet" in section_brute.lower():
                        section_propre = "Fenêtres et volets"
                    elif "porte" in section_brute.lower():
                        section_propre = "Portes et cadres de porte"
                    elif "balcon" in section_brute.lower() or "rampe" in section_brute.lower() or "marche" in section_brute.lower():
                        section_propre = "Balcon"
                    elif "clôture" in section_brute.lower() or "cloture" in section_brute.lower() or "panneau" in section_brute.lower() or "treillis" in section_brute.lower():
                        section_propre = "Clôture"
                    elif "fer" in section_brute.lower() and "forgé" in section_brute.lower():
                        section_propre = "Fer forgé"
                    else:
                        section_propre = "Autre"
                    
                    c.drawString(right_col_x, y_right, f"Section: {section_propre}")
                    y_right -= 10
                elif produit.get('sections'):
                    sections_text = ', '.join(produit['sections'])
                    c.drawString(right_col_x, y_right, f"Sections: {sections_text}")
                    y_right -= 10
                
                if produit.get('cout_total', 0) > 0:
                    cout_format = f"{produit['cout_total']:,.0f} $".replace(",", " ")
                    c.drawString(right_col_x, y_right, f"Coût: {cout_format}")
                    y_right -= 10
                
                y_right -= 8
        else:
            # Fallback: afficher le coût total des produits avec détails
            # Essayer de récupérer les infos du produit sélectionné et des sections
            selected_product = data.get("selectedProduct", {})
            product_general = data.get("product", {})
            
            # Déterminer le nom du produit - utiliser product.name directement
            product_name = "Produit appliqué"
            
            # 1. Utiliser product_general.name (c'est là qu'est "Dulux Gripper")
            if product_general and product_general.get("name"):
                name = product_general["name"]
                # Éviter les noms qui indiquent un regroupement et les transformer
                if name and name not in ["Produit sélectionné", "Produit", ""]:
                    if name in ["2 produits", "3 produits", "4 produits", "5 produits"]:
                        # Extraire le nombre de produits
                        nb_produits = name.split()[0]
                        product_name = f"Produits appliqués ({nb_produits})"
                    else:
                        product_name = name
                else:
                    product_name = "Produits appliqués"
            
            # 2. Si pas trouvé, chercher dans product_general.products[]
            elif product_general and product_general.get("products") and len(product_general["products"]) > 0:
                for prod in product_general["products"]:
                    name = prod.get("name", "")
                    if name and name not in ["Produit sélectionné", "Produit", ""]:
                        product_name = name
                        break
            
            # 3. Chercher dans selectedProduct
            elif selected_product and selected_product.get("name"):
                name = selected_product["name"]
                if name and name not in ["Produit sélectionné", "Produit", ""]:
                    product_name = name
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(right_col_x, y_right, f"• {product_name}")
            y_right -= 12
            
            # Calculer les gallons - utiliser product_general.price
            gallons_calcules = 0
            price_per_unit = 100  # Prix par défaut
            
            # 1. Utiliser product_general.price
            if product_general and product_general.get("price", 0) > 0:
                price_per_unit = product_general["price"]
            # 2. Fallback vers selected_product
            elif selected_product and selected_product.get("price", 0) > 0:
                price_per_unit = selected_product["price"]
            
            if price_per_unit > 0:
                gallons_calcules = cout_produits_total / price_per_unit
            
            c.setFont("Helvetica", 9)
            if gallons_calcules > 0:
                c.drawString(right_col_x, y_right, f"Quantité: {gallons_calcules:.0f} gal")
                y_right -= 10
            
            # Déterminer les sections d'application
            sections_application = []
            endroits = data.get("endroits", {})
            if endroits:
                for endroit_id, endroit_info in endroits.items():
                    if isinstance(endroit_info, dict):
                        titre = endroit_info.get("title", "")
                        # Appliquer le mapping de titre
                        titre_mapping = {
                            "latte horizontale": "Revêtement",
                            "revêtement horizontal": "Revêtement", 
                            "marches": "Balcon",
                            "rampe": "Fer forgé",
                            "balcon": "Balcon",
                            "corniches": "Corniches et moulures",
                            "corniche": "Corniches et moulures",
                            "moulure": "Corniches et moulures", 
                            "fascia": "Corniches et moulures",
                            "fenetre": "Fenêtres et volets",
                            "porte": "Portes",
                            "cloture": "Clôture"
                        }
                        
                        section_title = titre
                        for key, value in titre_mapping.items():
                            if key.lower() in titre.lower():
                                section_title = value
                                break
                        
                        if section_title not in sections_application:
                            sections_application.append(section_title)
            
            if sections_application:
                c.drawString(right_col_x, y_right, f"Sections: {', '.join(sections_application)}")
                y_right -= 10
            else:
                c.drawString(right_col_x, y_right, f"Sections: Surfaces extérieures")
                y_right -= 10
            
            cout_format = f"{cout_produits_total:,.0f} $".replace(",", " ")
            c.drawString(right_col_x, y_right, f"Coût total: {cout_format}")
            y_right -= 10
            
            y_right -= 8
    
    # Utiliser la même hauteur que la colonne droite pour aligner les sections
    y_pos = y_left - 15  # Commencer à la même hauteur que les informations client
    
    # === PRÉPARATION ET LAVAGE - SURFACES EXTÉRIEURES ===
    surfaces = data.get("surfaces", {})
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.Color(31/255, 41/255, 55/255))
    c.drawString(50, y_pos, "PRÉPARATION")
    y_pos -= 30
    
    # Organiser par type de travail (lavage, préparation)
    travaux_par_type = {}
    total_ext = 0
    
    for section_name, section_data in surfaces.items():
        print(f"DEBUG: Traitement section {section_name}: {section_data}")
        if section_name in ["avant", "droit", "arriere", "gauche"]:
            if isinstance(section_data, dict):
                for surface_type, value in section_data.items():
                    print(f"DEBUG: Type de surface: {surface_type} = {value}")
                    if isinstance(value, (int, float)) and value > 0:
                        # Classifier les types de travaux selon la bonne logique
                        surface_lower = surface_type.lower()
                        
                        # LAVAGE: tous les types de lavage
                        if any(keyword in surface_lower for keyword in [
                            "lavage_pression", "lavage_main", "lavage", "lavage_lineaire", 
                            "lavage_plancher", "lavage_balcon", "lavage_porte", "lavage_fenetre"
                        ]):
                            categorie = "Lavage"
                        
                        # PRÉPARATION: grattage, sablage, ponçage, primer, etc.
                        elif any(keyword in surface_lower for keyword in [
                            "grattage", "sablage", "poncer", "reboucher", "decapage", 
                            "primer", "retouche", "preparation", "prep", "calfeutrage"
                        ]):
                            categorie = "Préparation"
                        
                        # PEINTURE
                        elif "peinture" in surface_lower:
                            categorie = "Peinture"
                        
                        # AUTRE
                        else:
                            categorie = "Autre"
                        
                        
                        if categorie not in travaux_par_type:
                            travaux_par_type[categorie] = []
                        
                        travaux_par_type[categorie].append({
                            'section': section_name.capitalize(),
                            'type': surface_type,
                            'surface': value
                        })
                        total_ext += value
    
    # Afficher par catégorie de façon professionnelle
    for categorie, travaux in travaux_par_type.items():
        c.setFont("Helvetica-Bold", 12)
        c.drawString(60, y_pos, f"• {categorie}:")
        y_pos -= 18
        
        c.setFont("Helvetica", 11)
        for travail in travaux:
            # Nettoyer l'affichage du type de travail (remplacer _ par espaces)
            type_affiche = travail['type'].replace('_', ' ')
            c.drawString(80, y_pos, f"{travail['section']} - {type_affiche}: {travail['surface']:.1f} pi²")
            y_pos -= 14
        y_pos -= 10  # Espacement entre catégories
    
    
    # Supprimer l'affichage du total des surfaces
    y_pos -= 25  # Plus d'espace avant la section suivante
    
    # === ENDROITS PERSONNALISÉS ===
    endroits = data.get("endroits", {})
    if endroits:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "ENDROITS À PEINTURER")
        y_pos -= 25
        
        for endroit_id, endroit_info in endroits.items():
            if isinstance(endroit_info, dict) and endroit_info.get("sections"):
                # Utiliser la catégorie principale si disponible, sinon le titre
                titre_endroit = endroit_info.get("category", endroit_info.get("title", f"Endroit {endroit_id}"))
                
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, titre_endroit)
                y_pos -= 18
                
                # Parcourir chaque section (sous-type)
                for section_id, section_data in endroit_info["sections"].items():
                    type_travail = section_data.get("type", "Type inconnu")
                    surfaces = section_data.get("surfaces", {})
                    total_surface = section_data.get("totalSurface", 0)
                    options = section_data.get("options", {})
                    
                    # Afficher le sous-titre technique avec une puce
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(60, y_pos, f"• {type_travail}")
                    y_pos -= 14
                    
                    c.setFont("Helvetica", 10)
                    
                    # Afficher les surfaces par côté
                    if surfaces:
                        for cote, surface in surfaces.items():
                            c.drawString(80, y_pos, f"{cote.capitalize()}: {surface} pi²")
                            y_pos -= 12
                    
                    # Afficher le total et gallons
                    if total_surface > 0:
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(80, y_pos, f"Total: {total_surface} pi²")
                        y_pos -= 12
                        
                        # Ne pas afficher les gallons calculés automatiquement
                        # Seulement afficher si des gallons ont été vraiment appliqués
                    
                    # Afficher les informations de produit
                    product_data = section_data.get("product", {})
                    if product_data:
                        c.setFont("Helvetica", 8)
                        if product_data.get("produit"):
                            c.drawString(50, y_pos, f"  Produit: {product_data['produit']}")
                            y_pos -= 10
                        if product_data.get("gallons"):
                            # Utiliser la valeur réelle des gallons sans arrondir à nouveau si elle est déjà correcte
                            gallons_display = product_data["gallons"]
                            if isinstance(gallons_display, (int, float)):
                                gallons_display = int(gallons_display) if gallons_display == int(gallons_display) else gallons_display
                            c.drawString(50, y_pos, f"  Quantité: {gallons_display} gallons")
                            y_pos -= 10
                        if product_data.get("primer") and product_data.get("primer").lower() == "oui":
                            c.drawString(50, y_pos, f"  Primer: Oui")
                            y_pos -= 10
                        if product_data.get("troisieme_couche") and product_data.get("troisieme_couche").lower() == "oui":
                            c.drawString(50, y_pos, f"  3ème couche: Oui")
                            y_pos -= 10
                    
                    # Afficher les autres options
                    c.setFont("Helvetica", 8)
                    for option_name, option_value in options.items():
                        if option_name != "type_revetement":  # Éviter doublon avec produit
                            c.drawString(50, y_pos, f"  {option_name.replace('_', ' ').title()}: {option_value}")
                            y_pos -= 10
                    
                    y_pos -= 5
                
                y_pos -= 5
        y_pos -= 25  # Plus d'espace avant la section suivante
    
    # === SURFACES INTÉRIEURES ===
    if surfaces.get("interieur"):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "SURFACES INTÉRIEURES")
        y_pos -= 25
        
        c.setFont("Helvetica", 11)
        total_int = 0
        int_surfaces = surfaces["interieur"]
        for room in int_surfaces:
            if isinstance(room, dict):
                room_name = room.get("nom", "Pièce")
                c.setFont("Helvetica-Bold", 11)
                c.drawString(50, y_pos, f"{room_name}:")
                y_pos -= 18
                
                c.setFont("Helvetica", 11)
                for surface_type, area_value in room.items():
                    if surface_type != "nom" and area_value and float(area_value) > 0:
                        c.drawString(50, y_pos, f"{surface_type}: {area_value} pi²")
                        total_int += float(area_value)
                        y_pos -= 14
                y_pos -= 8
        
        if total_int > 0:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, f"Total intérieur: {total_int:.1f} pi²")
            y_pos -= 30
    
    # === PIED DE PAGE ===
    c.setFont("Helvetica", 8)
    c.drawString(50, 50, f"Estimation générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(width-50, 50, "Calculateur Qwota")
    
    # Finaliser l'overlay première page
    c.save()
    overlay.seek(0)
    
    # === CRÉER LA DEUXIÈME PAGE POUR L'INTÉRIEUR ===
    overlay2 = BytesIO()
    c2 = canvas.Canvas(overlay2, pagesize=letter)
    
    # Récupérer les données intérieures
    costs_int = data.get("costs", {})
    hours_int = data.get("hours", {})
    surfaces_int = data.get("surfaces", {})
    products_int = data.get("products", [])
    
    # DEBUG INITIAL - Afficher TOUTES les données reçues
    print(f"DEBUG INT: === DÉBUT CRÉATION PAGE 2 ===")
    print(f"DEBUG INT: Données complètes reçues: {list(data.keys())}")
    print(f"DEBUG INT: Type de data: {type(data)}")
    
    # Debug surfaces en détail
    print(f"DEBUG INT: Clés surfaces: {list(surfaces_int.keys()) if surfaces_int else 'Aucune surface'}")
    surfaces_int_filtrees = {k: v for k, v in surfaces_int.items() if k.startswith('int_')}
    print(f"DEBUG INT: Surfaces intérieures trouvées: {surfaces_int_filtrees}")
    
    # Debug coûts
    couts_int_filtrees = {k: v for k, v in costs_int.items() if 'int' in k.lower()}
    print(f"DEBUG INT: Coûts intérieur trouvés: {couts_int_filtrees}")
    
    # Debug heures  
    heures_int_filtrees = {k: v for k, v in hours_int.items() if 'int' in k.lower()}
    print(f"DEBUG INT: Heures intérieur trouvées: {heures_int_filtrees}")
    
    # Debug produits
    print(f"DEBUG INT: Produits reçus - Type: {type(products_int)}, Longueur: {len(products_int) if products_int else 0}")
    if products_int:
        print(f"DEBUG INT: Premier produit exemple: {products_int[0] if len(products_int) > 0 else 'Aucun'}")
    
    # Vérifier si on a des données intérieur
    has_interior_data = bool(surfaces_int_filtrees or couts_int_filtrees or heures_int_filtrees)
    print(f"DEBUG INT: A des données intérieur? {has_interior_data}")
    
    print(f"DEBUG INT: Début création page 2 - Intérieur")
    print(f"DEBUG INT: Coûts reçus: {costs_int}")
    print(f"DEBUG INT: Heures reçues: {hours_int}")
    print(f"DEBUG INT: Surfaces reçues: {list(surfaces_int.keys()) if surfaces_int else 'Aucune'}")
    
    # === LAYOUT IDENTIQUE À LA PAGE 1 MAIS POUR INTÉRIEUR ===
    y_pos = height - 80 + y_offset
    left_col_x = 50
    right_col_x = width - 200
    
    # Titres des sections
    c2.setFont("Helvetica-Bold", 14)
    c2.setFillColor(colors.Color(31/255, 41/255, 55/255))
    c2.drawString(left_col_x, y_pos, "INFORMATIONS CLIENT")
    c2.drawString(right_col_x, y_pos, "DÉTAIL DES COÛTS")
    
    y_left = y_pos - 25
    y_right = y_pos - 25
    
    # Informations client (identiques à page 1)
    c2.setFont("Helvetica", 12)
    c2.drawString(left_col_x, y_left, f"Client: {nom_client}")
    y_left -= 18
    c2.drawString(left_col_x, y_left, f"Adresse: {adresse_client}")
    y_left -= 18
    c2.drawString(left_col_x, y_left, f"Téléphone: {telephone_client}")
    y_left -= 18
    c2.drawString(left_col_x, y_left, f"Date: {date_estimation}")
    y_left -= 18
    
    # Détail des coûts INTÉRIEUR (structure identique à page 1)
    def format_price_top_int(price):
        try:
            if isinstance(price, (int, float)):
                return f"{price:,.2f} $".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
            else:
                val = float(str(price).replace("$", "").replace(",", ".").replace(" ", ""))
                return f"{val:,.2f} $".replace(",", "TEMP").replace(".", ",").replace("TEMP", " ")
        except:
            return "0,00 $"
    
    c2.setFont("Helvetica", 11)
    
    # Main d'œuvre - Lavage INTÉRIEUR
    try:
        lavage_cost_int = float(costs_int.get("lavage_int", 0)) if costs_int.get("lavage_int", 0) else 0
        if lavage_cost_int > 0:
            c2.drawString(right_col_x, y_right, f"Lavage: {format_price_top_int(lavage_cost_int)}")
            y_right -= 14
            print(f"DEBUG INT: Affiché lavage: {lavage_cost_int}")
    except (ValueError, TypeError):
        pass
    
    # Main d'œuvre - Préparation INTÉRIEUR
    try:
        preparation_cost_int = float(costs_int.get("preparation_int", 0)) if costs_int.get("preparation_int", 0) else 0
        if preparation_cost_int > 0:
            c2.drawString(right_col_x, y_right, f"Préparation: {format_price_top_int(preparation_cost_int)}")
            y_right -= 14
            print(f"DEBUG INT: Affiché préparation: {preparation_cost_int}")
    except (ValueError, TypeError):
        pass
    
    # Main d'œuvre - Peinture INTÉRIEUR (utiliser main_oeuvre_int + peinture calculée)
    try:
        main_oeuvre_int_val = float(costs_int.get("main_oeuvre_int", 0)) if costs_int.get("main_oeuvre_int", 0) else 0
        peinture_hours_int = float(hours_int.get("peinture_int", 0)) if hours_int.get("peinture_int", 0) else 0
        peinture_cost_calculated = peinture_hours_int * 43
        
        # Utiliser main_oeuvre_int s'il existe, sinon calculer depuis les heures
        final_peinture_cost = main_oeuvre_int_val if main_oeuvre_int_val > 0 else peinture_cost_calculated
        
        if final_peinture_cost > 0:
            c2.drawString(right_col_x, y_right, f"Main d'œuvre: {format_price_top_int(final_peinture_cost)}")
            y_right -= 14
            print(f"DEBUG INT: Affiché main d'œuvre: {final_peinture_cost} ({peinture_hours_int}h)")
    except (ValueError, TypeError):
        pass
    
    # Produits INTÉRIEUR
    try:
        materiaux_base_int = float(costs_int.get("materiaux_int", 0)) if costs_int.get("materiaux_int", 0) else 0
        if materiaux_base_int > 0:
            c2.drawString(right_col_x, y_right, f"Produits: {format_price_top_int(materiaux_base_int)}")
            y_right -= 14
            print(f"DEBUG INT: Affiché produits: {materiaux_base_int}")
    except (ValueError, TypeError):
        pass
    
    # Sous-total et marge INTÉRIEUR
    try:
        sous_total_int = float(costs_int.get("sousTotal_int", 0)) if costs_int.get("sousTotal_int", 0) else 0
        if sous_total_int > 0:
            c2.setFont("Helvetica-Bold", 11)
            c2.drawString(right_col_x, y_right, f"Sous-total: {format_price_top_int(sous_total_int)}")
            y_right -= 16
            
            marge_profit_int = float(costs_int.get("margeProfit_int", 0)) if costs_int.get("margeProfit_int", 0) else 0
            if marge_profit_int > 0:
                c2.setFont("Helvetica", 11)
                c2.drawString(right_col_x, y_right, f"Marge: {format_price_top_int(marge_profit_int)}")
                y_right -= 14
                
                total_estime_int = sous_total_int + marge_profit_int
                c2.setFont("Helvetica-Bold", 12)
                c2.drawString(right_col_x, y_right, f"Total: {format_price_top_int(total_estime_int)}")
                y_right -= 16
                print(f"DEBUG INT: Affiché total: {total_estime_int}")
    except (ValueError, TypeError):
        pass
    
    # === ESPACE ENTRE DÉTAIL DES COÛTS ET PARAMÈTRES ===
    y_right -= 25
    
    # === PARAMÈTRES INTÉRIEUR ===
    parameters_int = data.get("parameters", {})
    c2.setFont("Helvetica-Bold", 12)
    c2.drawString(right_col_x, y_right, "PARAMÈTRES")
    y_right -= 18
    
    c2.setFont("Helvetica", 10)
    taux_horaire_int = parameters_int.get("taux_horaire", 43)
    c2.drawString(right_col_x, y_right, f"Taux horaire: {taux_horaire_int}$/h")
    y_right -= 12
    
    if parameters_int.get("profitMargin"):
        c2.drawString(right_col_x, y_right, f"Marge: {parameters_int['profitMargin']}%")
        y_right -= 12
    
    y_right -= 20
    
    # === SURFACES INTÉRIEURES (colonne gauche) ===
    surfaces = data.get("surfaces", {})
    print(f"DEBUG INT: Analyse des surfaces pour intérieur")
    
    # Regrouper les surfaces INTÉRIEUR par section
    surfaces_par_section_int = {}
    types_travaux_int = set()
    
    # Parcourir toutes les surfaces pour l'intérieur (préfixe int_)
    for surface_key, surface_value in surfaces.items():
        if surface_key.startswith('int_') and surface_value > 0:
            print(f"DEBUG INT: Surface trouvée: {surface_key} = {surface_value}")
            
            # Extraire la section (int_salon_lavage -> salon)
            parts = surface_key.split('_')
            if len(parts) >= 2:
                section = parts[1]  # salon, cuisine, etc.
                type_travail = '_'.join(parts[2:]) if len(parts) > 2 else 'base'
                
                if section not in surfaces_par_section_int:
                    surfaces_par_section_int[section] = {}
                
                surfaces_par_section_int[section][type_travail] = surface_value
                types_travaux_int.add(type_travail)
                print(f"DEBUG INT: Ajouté {section} -> {type_travail}: {surface_value}")
        else:
            if surface_key.startswith('int_'):
                print(f"DEBUG INT: Surface intérieure ignorée (valeur 0): {surface_key}")
    
    print(f"DEBUG INT: Sections trouvées: {list(surfaces_par_section_int.keys())}")
    print(f"DEBUG INT: Types de travaux: {list(types_travaux_int)}")
    
    # Affichage des surfaces INTÉRIEURES
    if surfaces_par_section_int:
        c2.setFont("Helvetica-Bold", 14)
        c2.setFillColor(colors.Color(31/255, 41/255, 55/255))
        c2.drawString(left_col_x, y_left, "SURFACES INTÉRIEURES")
        y_left -= 25
        
        # Afficher chaque section INTÉRIEUR avec ses types de travaux
        for section, types in surfaces_par_section_int.items():
            # Nom de section propre
            if section == "salon":
                section_nom = "Salon"
            elif section == "cuisine":
                section_nom = "Cuisine"
            elif section == "chambre":
                section_nom = "Chambre"
            elif section == "salle_bain":
                section_nom = "Salle de bain"
            elif section == "escalier":
                section_nom = "Escalier"
            else:
                section_nom = section.replace('_', ' ').title()
            
            c2.setFont("Helvetica-Bold", 12)
            c2.drawString(left_col_x, y_left, f"{section_nom}")
            y_left -= 18
            
            c2.setFont("Helvetica", 11)
            # Afficher chaque type de travail pour cette section
            for type_travail, superficie in types.items():
                if superficie > 0:
                    if type_travail == 'base':
                        type_nom = "Surface de base"
                    else:
                        type_nom = type_travail.replace('_', ' ').title()
                    c2.drawString(left_col_x + 15, y_left, f"{type_nom}: {superficie} pi²")
                    y_left -= 14
            
            y_left -= 10
        
        y_left -= 20
    else:
        print(f"DEBUG INT: Aucune surface intérieure trouvée")
    
    # === PRODUITS APPLIQUÉS INTÉRIEUR (colonne droite) ===
    product_general_int = data.get("product", {})
    print(f"DEBUG INT: Recherche produits intérieur dans: {product_general_int}")
    
    # Chercher les produits appliqués INTÉRIEUR - filtrer pour int_
    produits_utilises_droite_int = []
    
    if product_general_int and product_general_int.get("products") and len(product_general_int["products"]) > 0:
        print(f"DEBUG INT: Analyse de {len(product_general_int['products'])} produits")
        for i, prod in enumerate(product_general_int["products"]):
            print(f"DEBUG INT: Produit {i+1}: {prod}")
            # Filtrer seulement les produits intérieurs
            if prod.get("type", "").startswith("int_"):
                print(f"DEBUG INT: Produit intérieur détecté: {prod.get('name')}")
                gallons_appliques_int = prod.get("gallons", 0)
                if gallons_appliques_int and gallons_appliques_int > 0:
                    produits_utilises_droite_int.append({
                        'produit': prod.get("name", "Produit"),
                        'gallons': gallons_appliques_int,
                        'section_name': prod.get("sectionName", ""),
                        'prix_unitaire': prod.get("pricePerGallon", prod.get("price", 100)),
                        'cout_total': prod.get("totalCost", gallons_appliques_int * (prod.get("pricePerGallon", prod.get("price", 100))))
                    })
                    print(f"DEBUG INT: Ajouté produit: {prod.get('name')} - {gallons_appliques_int} gal")
            else:
                print(f"DEBUG INT: Produit non-intérieur ignoré: {prod.get('name')} (type: {prod.get('type', 'N/A')})")
    else:
        print(f"DEBUG INT: Aucun produit trouvé")
    
    # Affichage des produits INTÉRIEUR
    if produits_utilises_droite_int:
        c2.setFont("Helvetica-Bold", 12)
        c2.drawString(right_col_x, y_right, "PRODUITS")
        y_right -= 20
        
        for produit in produits_utilises_droite_int:
            c2.setFont("Helvetica-Bold", 11)
            c2.drawString(right_col_x, y_right, f"• {produit['produit']}")
            y_right -= 15
            
            c2.setFont("Helvetica", 10)
            c2.drawString(right_col_x, y_right, f"Quantité: {produit['gallons']} gal")
            y_right -= 12
            
            if produit.get('section_name'):
                section_clean = produit['section_name'].replace('_', ' ').title()
                c2.drawString(right_col_x, y_right, f"Section: {section_clean}")
                y_right -= 12
            
            y_right -= 8
    else:
        print(f"DEBUG INT: Aucun produit intérieur à afficher")
    
    # === PIED DE PAGE INTÉRIEUR ===
    c2.setFont("Helvetica", 8)
    c2.drawString(50, 50, f"Page 2 - Intérieur - Estimation générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    c2.drawRightString(width-50, 50, "Calculateur Qwota")
    
    # Finaliser la deuxième page
    c2.save()
    overlay2.seek(0)
    
    # === FUSIONNER LES DEUX PAGES ===
    print(f"DEBUG INT: === DÉBUT FUSION DES PAGES ===")
    
    try:
        background = PdfReader(template_path)
        print(f"DEBUG INT: Template chargé avec succès")
    except Exception as e:
        print(f"DEBUG INT: ERREUR lecture template: {e}")
        print(f"DEBUG INT: Création d'un PDF sans template (pages blanches)")
        # Créer un PDF vide si pas de template
        temp_pdf = BytesIO()
        temp_canvas = canvas.Canvas(temp_pdf, pagesize=letter)
        temp_canvas.showPage()  # Page 1 vide
        temp_canvas.showPage()  # Page 2 vide  
        temp_canvas.save()
        temp_pdf.seek(0)
        background = PdfReader(temp_pdf)
        print(f"DEBUG INT: Template vide créé avec {len(background.pages)} pages")
    
    try:
        overlay_pdf = PdfReader(overlay)
        print(f"DEBUG INT: Overlay page 1 créé")
    except Exception as e:
        print(f"DEBUG INT: ERREUR overlay page 1: {e}")
        raise e
    
    try:
        overlay2_pdf = PdfReader(overlay2)
        print(f"DEBUG INT: Overlay page 2 créé")
    except Exception as e:
        print(f"DEBUG INT: ERREUR overlay page 2: {e}")
        raise e
    
    print(f"DEBUG INT: Template a {len(background.pages)} pages")
    for i, page in enumerate(background.pages):
        print(f"DEBUG INT: Page {i+1} du template disponible")
    
    writer = PdfWriter()
    
    # Page 1 - Extérieur
    try:
        page1 = background.pages[0]
        page1.merge_page(overlay_pdf.pages[0])
        writer.add_page(page1)
        print(f"DEBUG INT: [OK] Page 1 (extérieur) ajoutée avec succès")
    except Exception as e:
        print(f"DEBUG INT: [ERROR] ERREUR page 1: {e}")
        raise e
    
    # Page 2 - Intérieur
    if language != 'en':
        # Template français: ajouter overlay sur page 2
        try:
            if len(background.pages) > 1:
                page2 = background.pages[1]
                print(f"DEBUG INT: [OK] Utilisation page 2 du template")
            else:
                page2 = background.pages[0]
                print(f"DEBUG INT: [WARN] Réutilisation page 1 du template (pas de page 2)")

            page2.merge_page(overlay2_pdf.pages[0])
            writer.add_page(page2)
            print(f"DEBUG INT: [OK] Page 2 (intérieur) ajoutée avec succès")
        except Exception as e:
            print(f"DEBUG INT: [ERROR] ERREUR page 2: {e}")
            raise e
    else:
        # Template anglais: ajouter page 2 SANS overlay (juste le template vide)
        if len(background.pages) > 1:
            page2 = background.pages[1]
            writer.add_page(page2)
            print(f"DEBUG INT: [INFO] Template anglais - Page 2 ajoutée SANS overlay (template vide)")
        else:
            print(f"DEBUG INT: [WARN] Template anglais n'a qu'une page")
    
    print(f"DEBUG INT: [OK] PDF final créé avec {len(writer.pages)} pages")
    
    # Test d'écriture
    try:
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        print(f"DEBUG INT: [OK] PDF écrit avec succès, taille: {len(output.getvalue())} bytes")
        return output
    except Exception as e:
        print(f"DEBUG INT: [ERROR] ERREUR écriture PDF: {e}")
        raise e
