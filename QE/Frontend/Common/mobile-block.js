/**
 * BLOCAGE IMMÉDIAT MOBILE POUR COACH/DIRECTION
 * Ce script doit être chargé EN PREMIER dans le <head>
 * AVANT tout autre script, CSS ou contenu
 */
(function() {
  'use strict';

  var userRole = localStorage.getItem('userRole');

  if (userRole === 'coach' || userRole === 'direction') {
    var isSmallScreen = window.innerWidth <= 768;
    var mobileUA = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    var isTablet = /iPad/i.test(navigator.userAgent) || (window.innerWidth > 768);

    if (isSmallScreen && mobileUA && !isTablet) {
      // Arrêter TOUT immédiatement
      document.documentElement.innerHTML = '<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Qwota</title><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"><style>*{margin:0;padding:0;box-sizing:border-box}html,body{height:100%}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;flex-direction:column;gap:1.5rem;text-align:center;padding:2rem;color:#f1f5f9}.icon{font-size:5rem;color:#60a5fa}.message{font-size:1.5rem;font-weight:700;max-width:300px;line-height:1.4}.submessage{font-size:1rem;color:#94a3b8;max-width:280px}</style></head><body><i class="fas fa-desktop icon"></i><div class="message">Application disponible uniquement sur PC</div><div class="submessage">L\'accès Coach et Direction nécessite un ordinateur</div></body>';

      // Empêcher tout autre chargement
      window.stop();
      throw new Error('MOBILE_BLOCKED');
    }
  }
})();
