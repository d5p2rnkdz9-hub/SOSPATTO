/* ===============================================
   SOS PERMESSO - MAIN APPLICATION SCRIPT
   =============================================== */

// ===============================================
// UTILITY: DEVICE DETECTION
// ===============================================

function isMobile() {
  return window.innerWidth <= 768;
}

function isHomepage() {
  const path = window.location.pathname;
  return path === '/' || path === '/index.html' || path.endsWith('/Sito_Nuovo/') || path.endsWith('/Sito_Nuovo/index.html');
}

// ===============================================
// MOBILE MENU TOGGLE
// ===============================================

const menuToggle = document.getElementById('menu-toggle');
const navMenu = document.getElementById('nav-menu');
const navWrapper = navMenu?.parentElement;

// Mobile navigation mapping - on mobile, these should scroll to sections
// instead of going to separate pages (except Collabora which stays external)
const mobileNavMapping = {
  'Database': '#database',
  'Guide': '#guide',
  'Test': '#test'
  // Collabora stays as an external link to the in-house app
};

if (menuToggle && navWrapper) {
  menuToggle.addEventListener('click', () => {
    navWrapper.classList.toggle('active');
    menuToggle.textContent = navWrapper.classList.contains('active') ? '✕' : '☰';
    // Prevent body scroll when menu is open
    document.body.style.overflow = navWrapper.classList.contains('active') ? 'hidden' : '';
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!menuToggle.contains(e.target) && !navWrapper.contains(e.target)) {
      navWrapper.classList.remove('active');
      menuToggle.textContent = '☰';
      document.body.style.overflow = '';
    }
  });

  // Handle mobile navigation - redirect to sections on homepage
  navWrapper.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      const linkText = link.textContent.trim();
      const sectionId = mobileNavMapping[linkText];

      // On mobile, redirect to homepage sections (except Collabora)
      if (isMobile() && sectionId) {
        e.preventDefault();

        // Close menu
        navWrapper.classList.remove('active');
        menuToggle.textContent = '☰';
        document.body.style.overflow = '';

        if (isHomepage()) {
          // Already on homepage, just scroll to section
          const target = document.querySelector(sectionId);
          if (target) {
            const headerOffset = 80;
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
            window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
          }
        } else {
          // Navigate to homepage with anchor
          window.location.href = '/' + sectionId;
        }
      } else {
        // Desktop or Collabora - close menu and let default behavior happen
        navWrapper.classList.remove('active');
        menuToggle.textContent = '☰';
        document.body.style.overflow = '';
      }
    });
  });

  // Close menu when clicking dropdown links
  navWrapper.querySelectorAll('.dropdown-link').forEach(link => {
    link.addEventListener('click', () => {
      navWrapper.classList.remove('active');
      menuToggle.textContent = '☰';
      document.body.style.overflow = '';
    });
  });
}

// ===============================================
// DROPDOWN ARIA STATE MANAGEMENT
// ===============================================

// Update aria-expanded on hover (desktop only)
function initDropdownAria() {
  if (window.innerWidth > 768) {
    const dropdownParents = document.querySelectorAll('.has-dropdown');

    dropdownParents.forEach(parent => {
      const link = parent.querySelector('.nav-link');
      if (!link) return;

      // Mouse events
      parent.addEventListener('mouseenter', () => {
        link.setAttribute('aria-expanded', 'true');
      });

      parent.addEventListener('mouseleave', () => {
        link.setAttribute('aria-expanded', 'false');
      });

      // Keyboard support - focus within dropdown
      parent.addEventListener('focusin', () => {
        link.setAttribute('aria-expanded', 'true');
      });

      parent.addEventListener('focusout', (e) => {
        // Only close if focus leaves the entire dropdown parent
        if (!parent.contains(e.relatedTarget)) {
          link.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initDropdownAria);

// Re-initialize on resize (in case viewport crosses 768px threshold)
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(initDropdownAria, 250);
});

// Language switching is now handled by nav dropdown links (static href attributes)
// The nav.liquid template generates correct IT/EN/FR URLs server-side

// ===============================================
// SCROLL ANIMATIONS (Intersection Observer)
// ===============================================

// SCROLL REVEAL ANIMATION - DISABLED
// Was causing elements to be hidden until scrolled into view
// const observerOptions = {
//   threshold: 0.1,
//   rootMargin: '0px 0px -50px 0px'
// };
//
// const animateOnScroll = new IntersectionObserver((entries) => {
//   entries.forEach(entry => {
//     if (entry.isIntersecting) {
//       entry.target.classList.add('slide-up');
//       animateOnScroll.unobserve(entry.target);
//     }
//   });
// }, observerOptions);
//
// document.addEventListener('DOMContentLoaded', () => {
//   const elementsToAnimate = document.querySelectorAll('.card, .section-header, .alert');
//   elementsToAnimate.forEach((element, index) => {
//     element.style.opacity = '0';
//     element.classList.add(`stagger-${Math.min(index % 6 + 1, 6)}`);
//     animateOnScroll.observe(element);
//   });
// });

// ===============================================
// ADD ANIMATION CLASSES TO BUTTONS
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.btn');

  buttons.forEach(button => {
    // Add squeeze effect on click
    button.classList.add('squeeze-click');

    // Add hover bounce to primary buttons
    if (button.classList.contains('btn-primary')) {
      button.closest('.card')?.classList.add('hover-lift');
    }
  });
});

// ===============================================
// SMOOTH SCROLL FOR ANCHOR LINKS
// ===============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');

    // Only prevent default for internal anchors
    if (href !== '#' && href.startsWith('#')) {
      e.preventDefault();

      const target = document.querySelector(href);
      if (target) {
        const headerOffset = isMobile() ? 80 : 140; // Smaller offset on mobile
        const elementPosition = target.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    }
  });
});

// ===============================================
// STICKY HEADER ON SCROLL
// ===============================================

let lastScroll = 0;
let scrollTicking = false;
const header = document.querySelector('.header');

window.addEventListener('scroll', () => {
  if (!scrollTicking) {
    requestAnimationFrame(() => {
      const currentScroll = window.pageYOffset;
      if (currentScroll > 100) {
        header.style.boxShadow = 'var(--shadow-md)';
      } else {
        header.style.boxShadow = 'var(--shadow-sm)';
      }
      lastScroll = currentScroll;
      scrollTicking = false;
    });
    scrollTicking = true;
  }
}, { passive: true });

// ===============================================
// CARD HOVER EFFECTS
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.card');

  cards.forEach(card => {
    // Add icon animation on hover
    card.addEventListener('mouseenter', () => {
      const icon = card.querySelector('.card-icon');
      if (icon) {
        icon.classList.add('emoji-bounce');
      }
    });

    card.addEventListener('mouseleave', () => {
      const icon = card.querySelector('.card-icon');
      if (icon) {
        icon.classList.remove('emoji-bounce');
      }
    });
  });
});

// ===============================================
// LOAD CONTENT FROM JSON (for multilingual support)
// ===============================================

async function loadContent(lang = 'it') {
  try {
    const response = await fetch(`../data/content-${lang}.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const content = await response.json();
    return content;
  } catch (error) {
    console.error('Error loading content:', error);
    // Fallback to Italian if there's an error
    if (lang !== 'it') {
      return loadContent('it');
    }
    return null;
  }
}

// ===============================================
// ANALYTICS & TRACKING (placeholder)
// ===============================================

function trackEvent(eventName, eventData = {}) {
  // Placeholder for analytics tracking
  console.log('Track Event:', eventName, eventData);

  // Example: Google Analytics
  // if (typeof gtag !== 'undefined') {
  //   gtag('event', eventName, eventData);
  // }
}

// Track CTA clicks
document.addEventListener('DOMContentLoaded', () => {
  // Track CTAs that go to the in-house app (formerly tracked Typeform links)
  const ctaButtons = document.querySelectorAll('a[href*="app.sospermesso.it"]');

  ctaButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      const buttonText = button.textContent.trim();
      trackEvent('cta_click', {
        button_text: buttonText,
        destination: button.href
      });
    });
  });
});

// ===============================================
// UTILITY FUNCTIONS
// ===============================================

// Debounce function for scroll events
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Check if element is in viewport
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

// ===============================================
// ACCESSIBILITY ENHANCEMENTS
// ===============================================

// Add focus visible class for keyboard navigation
document.addEventListener('DOMContentLoaded', () => {
  let isUsingKeyboard = false;

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      isUsingKeyboard = true;
      document.body.classList.add('keyboard-navigation');
    }
  });

  document.addEventListener('mousedown', () => {
    isUsingKeyboard = false;
    document.body.classList.remove('keyboard-navigation');
  });
});

// ===============================================
// CONSOLE MESSAGE
// ===============================================

console.log(
  '%c🏮 SOS Permesso',
  'font-size: 24px; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'
);
console.log(
  '%cCompleto, aggiornato, nella tua lingua',
  'font-size: 14px; color: #666;'
);
console.log(
  '%c💛 Made with care for the immigrant community in Italy',
  'font-size: 12px; color: #FF3B3B;'
);

// ===============================================
// EXPORT FOR MODULE USE (if needed)
// ===============================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    loadContent,
    trackEvent,
    debounce,
    isInViewport
  };
}

// ===============================================
// MOBILE HEADER LANGUAGE SWITCHER
// ===============================================
// Shown only on mobile. Options carry data-lang; the localized URL for the
// current page is computed in JS (mirrors the Liquid logic in nav.liquid).
// Idempotent: a data flag prevents double-binding if this ever runs twice.
function initLanguageSwitcher() {
  const switcher = document.querySelector('.language-switcher');
  if (!switcher || switcher.dataset.langWired === '1') return;
  switcher.dataset.langWired = '1';

  const toggle = switcher.querySelector('#language-toggle');
  const options = switcher.querySelectorAll('.language-option');
  const PREFIX_RE = /^\/(en|fr|es|tr|bn|ru|ar|ur|fa|zh)(\/|$)/;

  function localizedUrl(target) {
    let path = window.location.pathname || '/';
    const m = path.match(PREFIX_RE);
    if (m) {
      path = path.slice(m[1].length + 1); // strip "/xx"
      if (path === '') path = '/';
    }
    const hash = window.location.hash || '';
    if (target === 'it') return path + hash;
    return '/' + target + (path === '/' ? '/' : path) + hash;
  }

  // Highlight the current language in the dropdown
  const current = (window.location.pathname || '/').match(PREFIX_RE);
  const currentLang = current ? current[1] : 'it';
  options.forEach(opt => {
    if (opt.getAttribute('data-lang') === currentLang) opt.classList.add('active-lang');
  });

  if (toggle) {
    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      switcher.classList.toggle('open');
    });
  }

  options.forEach(opt => {
    opt.addEventListener('click', () => {
      const target = opt.getAttribute('data-lang');
      if (target) window.location.href = localizedUrl(target);
    });
  });

  // Close when tapping outside the switcher
  document.addEventListener('click', (e) => {
    if (!switcher.contains(e.target)) switcher.classList.remove('open');
  });
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLanguageSwitcher);
} else {
  initLanguageSwitcher();
}
