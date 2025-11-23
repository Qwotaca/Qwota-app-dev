"""
Générateur de GQP en HTML (avec support vidéo)
Remplace le PDF pour permettre l'affichage de vidéos
"""

import os
import uuid
from datetime import datetime

def generate_gqp_html(infos: dict, media_urls: list) -> str:
    """
    Génère le HTML pour un GQP

    Args:
        infos: dict avec nom, prenom, adresse, telephone, courriel, endroit, etapes, heure, montant
        media_urls: liste de dicts avec {'url': str, 'type': 'image' ou 'video'}

    Returns:
        str: contenu HTML complet
    """

    # Préparer les données
    nom_complet = f"{infos.get('prenom', '')} {infos.get('nom', '')}".strip()
    telephone = infos.get('telephone', '')
    adresse = infos.get('adresse', '')
    courriel = infos.get('courriel', '')
    endroit = infos.get('endroit', '').replace('\n', '<br>')
    etapes = infos.get('etapes', '').replace('\n', '<br>')
    heure = infos.get('heure', '')
    montant = infos.get('montant', '')

    # Simplifier l'adresse (2 premières parties)
    adresse_parts = adresse.split(',')[:2]
    adresse_simplifiee = ', '.join(adresse_parts).strip()

    # Générer le HTML des médias avec index pour la lightbox
    media_html = ""
    for idx, media in enumerate(media_urls):
        if media['type'] == 'video':
            media_html += f'''
            <div class="media-item" onclick="openLightbox({idx})">
                <video playsinline muted>
                    <source src="{media['url']}" type="video/mp4">
                </video>
                <div class="media-overlay">
                    <i class="fas fa-play-circle"></i>
                </div>
            </div>
            '''
        else:
            media_html += f'''
            <div class="media-item" onclick="openLightbox({idx})">
                <img src="{media['url']}" alt="Photo du projet" loading="lazy">
                <div class="media-overlay">
                    <i class="fas fa-search-plus"></i>
                </div>
            </div>
            '''

    # Générer le JS array pour la lightbox
    media_js_array = "["
    for media in media_urls:
        media_type = media['type']
        media_url = media['url']
        media_js_array += f'{{"url": "{media_url}", "type": "{media_type}"}},'
    media_js_array += "]"

    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GQP - {nom_complet}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        /* Scrollbar personnalisée discrète */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(100, 116, 139, 0.4);
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(100, 116, 139, 0.6);
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f172a;
            min-height: 100vh;
            color: #f1f5f9;
            padding: 20px;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 24px;
            padding: 24px;
            background: #1e293b;
            border-radius: 16px;
            border: 1px solid #334155;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            color: #60a5fa;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            color: #94a3b8;
            font-size: 13px;
        }}

        .card {{
            background: #1e293b;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid #334155;
        }}

        .card-title {{
            font-size: 14px;
            font-weight: 600;
            color: #60a5fa;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .card-title i {{
            font-size: 16px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}

        @media (max-width: 600px) {{
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 18px;
            }}
            .header .subtitle {{
                font-size: 11px;
            }}
            .footer-item .label {{
                font-size: 10px;
            }}
            .footer-item .value {{
                font-size: 15px;
            }}
        }}

        .info-item {{
            background: rgba(255, 255, 255, 0.03);
            padding: 14px;
            border-radius: 10px;
            border: 1px solid #334155;
        }}

        .info-label {{
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}

        .info-value {{
            font-size: 14px;
            color: #f1f5f9;
            word-break: break-word;
        }}

        .content-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}

        @media (max-width: 600px) {{
            .content-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .content-box {{
            background: rgba(255, 255, 255, 0.02);
            padding: 16px;
            border-radius: 10px;
            min-height: 150px;
            border: 1px solid #334155;
        }}

        .content-box h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #60a5fa;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .content-box p {{
            font-size: 13px;
            line-height: 1.6;
            color: #e2e8f0;
        }}

        .footer-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 16px;
        }}

        .footer-item {{
            background: rgba(52, 211, 153, 0.1);
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }}

        .footer-item .label {{
            font-size: 11px;
            color: #34d399;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}

        .footer-item .value {{
            font-size: 15px;
            font-weight: 700;
            color: #34d399;
        }}

        /* Médias (images et vidéos) */
        .media-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;
        }}

        .media-item {{
            border-radius: 10px;
            overflow: hidden;
            background: rgba(0, 0, 0, 0.3);
            aspect-ratio: 4/3;
            border: 1px solid #334155;
            cursor: pointer;
            position: relative;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .media-item:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }}

        .media-item img,
        .media-item video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .media-item video {{
            background: #000;
        }}

        .media-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s;
        }}

        .media-item:hover .media-overlay {{
            opacity: 1;
        }}

        .media-overlay i {{
            font-size: 32px;
            color: white;
        }}

        .no-media {{
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }}

        .no-media i {{
            font-size: 40px;
            margin-bottom: 12px;
            opacity: 0.5;
        }}

        /* Lightbox */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 9999;
            align-items: center;
            justify-content: center;
        }}

        .lightbox.active {{
            display: flex;
        }}

        .lightbox-content {{
            max-width: 60vw;
            max-height: 85vh;
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .lightbox-content img {{
            max-width: 60vw;
            max-height: 80vh;
            object-fit: contain;
            border-radius: 8px;
        }}

        .lightbox-content video {{
            max-width: 60vw;
            max-height: 80vh;
            border-radius: 8px;
            background: #000;
        }}

        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-size: 24px;
            cursor: pointer;
            transition: background 0.2s;
            z-index: 10001;
        }}

        .lightbox-close:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}

        .lightbox-nav {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s;
            z-index: 10010;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }}

        .lightbox-nav:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}

        .lightbox-prev {{
            left: 20px;
        }}

        .lightbox-next {{
            right: 20px;
        }}

        .lightbox-counter {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 14px;
            background: rgba(0, 0, 0, 0.5);
            padding: 8px 16px;
            border-radius: 20px;
        }}

        /* Logo Qwota */
        .logo {{
            text-align: center;
            margin-top: 24px;
            padding: 16px;
            color: #64748b;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GQP pour {nom_complet or 'Client'}</h1>
            <p class="subtitle">Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>

        <!-- Informations client -->
        <div class="card">
            <div class="card-title">
                <i class="fas fa-user"></i>
                Informations du client
            </div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Nom complet</div>
                    <div class="info-value">{nom_complet or 'Non spécifié'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Téléphone</div>
                    <div class="info-value">{telephone or 'Non spécifié'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Adresse</div>
                    <div class="info-value">{adresse_simplifiee or 'Non spécifiée'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Courriel</div>
                    <div class="info-value">{courriel or 'Non spécifié'}</div>
                </div>
            </div>
        </div>

        <!-- Détails du projet -->
        <div class="card">
            <div class="card-title">
                <i class="fas fa-clipboard-list"></i>
                Détails du projet
            </div>
            <div class="content-grid">
                <div class="content-box">
                    <h3><i class="fas fa-tasks"></i> Étapes à réaliser</h3>
                    <p>{etapes or 'Aucune étape spécifiée'}</p>
                </div>
                <div class="content-box">
                    <h3><i class="fas fa-map-marker-alt"></i> Endroits concernés</h3>
                    <p>{endroit or 'Aucun endroit spécifié'}</p>
                </div>
            </div>

            <div class="footer-info">
                <div class="footer-item">
                    <div class="label">Temps estimé</div>
                    <div class="value">{heure or '--'}</div>
                </div>
                <div class="footer-item">
                    <div class="label">Montant</div>
                    <div class="value">{montant or '--'}</div>
                </div>
            </div>
        </div>

        <!-- Médias -->
        <div class="card">
            <div class="card-title">
                <i class="fas fa-images"></i>
                Photos et vidéos du projet
            </div>
            {'<div class="media-grid">' + media_html + '</div>' if media_html else '<div class="no-media"><i class="fas fa-photo-video"></i><p>Aucun média ajouté</p></div>'}
        </div>

        <div class="logo">
            <p>Généré avec Qwota</p>
        </div>
    </div>

    <!-- Lightbox -->
    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" onclick="closeLightbox()">
            <i class="fas fa-times"></i>
        </button>
        <button class="lightbox-nav lightbox-prev" onclick="prevMedia()">
            <i class="fas fa-chevron-left"></i>
        </button>
        <div class="lightbox-content" id="lightbox-content"></div>
        <button class="lightbox-nav lightbox-next" onclick="nextMedia()">
            <i class="fas fa-chevron-right"></i>
        </button>
        <div class="lightbox-counter" id="lightbox-counter"></div>
    </div>

    <script>
        const mediaList = {media_js_array};
        let currentIndex = 0;

        function openLightbox(index) {{
            currentIndex = index;
            showMedia();
            document.getElementById('lightbox').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeLightbox() {{
            document.getElementById('lightbox').classList.remove('active');
            document.body.style.overflow = '';
            // Pause video if playing
            const video = document.querySelector('#lightbox-content video');
            if (video) video.pause();
        }}

        function showMedia() {{
            const content = document.getElementById('lightbox-content');
            const counter = document.getElementById('lightbox-counter');
            const media = mediaList[currentIndex];

            if (media.type === 'video') {{
                content.innerHTML = `<video controls autoplay playsinline>
                    <source src="${{media.url}}" type="video/mp4">
                </video>`;
            }} else {{
                content.innerHTML = `<img src="${{media.url}}" alt="Photo du projet">`;
            }}

            counter.textContent = `${{currentIndex + 1}} / ${{mediaList.length}}`;
        }}

        function nextMedia() {{
            currentIndex = (currentIndex + 1) % mediaList.length;
            showMedia();
        }}

        function prevMedia() {{
            currentIndex = (currentIndex - 1 + mediaList.length) % mediaList.length;
            showMedia();
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (!document.getElementById('lightbox').classList.contains('active')) return;

            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') nextMedia();
            if (e.key === 'ArrowLeft') prevMedia();
        }});

        // Close on background click
        document.getElementById('lightbox').addEventListener('click', (e) => {{
            if (e.target.id === 'lightbox') closeLightbox();
        }});
    </script>
</body>
</html>'''

    return html
