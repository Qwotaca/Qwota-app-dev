/**
 * QWOTA SPA ROUTER
 * Système de routing pour Single Page Application
 * Navigation fluide sans rechargement de page
 */

class Router {
  constructor() {
    this.contentContainer = document.getElementById('app-content');
    this.loader = document.getElementById('page-loader');
    this.currentPath = window.location.pathname;

    // Initialize
    this.init();
  }

  init() {
    // Intercept all link clicks
    this.interceptLinks();

    // Handle browser back/forward
    window.addEventListener('popstate', (event) => {
      if (event.state && event.state.path) {
        this.loadPage(event.state.path, false);
      }
    });

    // Load initial page
    const initialPath = window.location.pathname;
    this.loadPage(initialPath, true);

    console.log('[Router] Initialized');
  }

  interceptLinks() {
    // Intercept clicks on sidebar links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');

      if (!link) return;

      const href = link.getAttribute('href');

      // Skip external links and special links
      if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto:')) {
        return;
      }

      // Intercept internal navigation
      e.preventDefault();
      this.navigateTo(href);
    });
  }

  async navigateTo(path) {
    if (this.currentPath === path) {
      console.log('[Router] Already on this page:', path);
      return;
    }

    console.log('[Router] Navigating to:', path);

    // Update browser history
    window.history.pushState({ path }, '', path);

    // Load page content
    await this.loadPage(path, true);
  }

  async loadPage(path, updateHistory = false) {
    try {
      // Show loader
      this.showLoader();

      // Fade out current content
      this.contentContainer.classList.add('loading');

      // Fetch page content
      const response = await fetch(`/api/page-content?path=${encodeURIComponent(path)}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Update content
      this.contentContainer.innerHTML = data.content;

      // Update page title
      if (data.title) {
        document.getElementById('page-title').textContent = data.title;
      }

      // Update active menu item
      this.updateActiveMenuItem(path);

      // Fade in new content
      this.contentContainer.classList.remove('loading');

      // Hide loader
      this.hideLoader();

      // Execute page scripts if any
      this.executePageScripts();

      // Update current path
      this.currentPath = path;

      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });

      console.log('[Router] Page loaded successfully:', path);

    } catch (error) {
      console.error('[Router] Error loading page:', error);

      this.contentContainer.innerHTML = `
        <div class="flex flex-col items-center justify-center min-h-[60vh]">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle text-6xl text-red-500 mb-4"></i>
            <h2 class="text-2xl font-bold mb-2" style="color: var(--text-light);">Erreur de chargement</h2>
            <p class="text-lg mb-4" style="color: var(--text-muted);">Impossible de charger la page demandée</p>
            <p class="text-sm mb-6" style="color: var(--text-gray);">${error.message}</p>
            <button onclick="window.location.reload()" class="btn-primary">
              <i class="fas fa-redo mr-2"></i>
              Recharger la page
            </button>
          </div>
        </div>
      `;

      this.contentContainer.classList.remove('loading');
      this.hideLoader();
    }
  }

  updateActiveMenuItem(path) {
    // Remove active class from all menu items
    const allMenuItems = document.querySelectorAll('#sidebar-menu a');
    allMenuItems.forEach(item => {
      item.classList.remove('menu-active');
    });

    // Add active class to current page
    const activeItem = document.querySelector(`#sidebar-menu a[href="${path}"]`);
    if (activeItem) {
      activeItem.classList.add('menu-active');
    }

    console.log('[Router] Active menu updated:', path);
  }

  executePageScripts() {
    // Execute any inline scripts in the loaded content
    const scripts = this.contentContainer.querySelectorAll('script');
    scripts.forEach(oldScript => {
      const newScript = document.createElement('script');

      // Copy attributes
      Array.from(oldScript.attributes).forEach(attr => {
        newScript.setAttribute(attr.name, attr.value);
      });

      // Copy content
      newScript.textContent = oldScript.textContent;

      // Replace old script with new one
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });

    console.log('[Router] Page scripts executed');
  }

  showLoader() {
    if (this.loader) {
      this.loader.classList.add('active');
    }
  }

  hideLoader() {
    if (this.loader) {
      this.loader.classList.remove('active');
    }
  }

  // Public method to force reload current page
  reload() {
    this.loadPage(this.currentPath, false);
  }

  // Public method to go back
  back() {
    window.history.back();
  }

  // Public method to go forward
  forward() {
    window.history.forward();
  }
}

// Initialize router when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.router = new Router();
  });
} else {
  window.router = new Router();
}

// Export for use in other scripts
window.Router = Router;

console.log('[Router] Script loaded');
