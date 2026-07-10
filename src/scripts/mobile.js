/* ===============================================
   SOS PERMESSO - MOBILE INTERACTIONS
   Touch gestures and mobile-specific features
   =============================================== */

// ===============================================
// SWIPE GESTURES FOR MOBILE
// ===============================================

class SwipeDetector {
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      threshold: options.threshold || 50,
      restraint: options.restraint || 100,
      allowedTime: options.allowedTime || 300,
      ...options
    };

    this.startX = 0;
    this.startY = 0;
    this.startTime = 0;
    this.distX = 0;
    this.distY = 0;
    this.elapsedTime = 0;

    this.init();
  }

  init() {
    this.element.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
    this.element.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
  }

  handleTouchStart(e) {
    const touchObj = e.changedTouches[0];
    this.startX = touchObj.pageX;
    this.startY = touchObj.pageY;
    this.startTime = new Date().getTime();
  }

  handleTouchEnd(e) {
    const touchObj = e.changedTouches[0];
    this.distX = touchObj.pageX - this.startX;
    this.distY = touchObj.pageY - this.startY;
    this.elapsedTime = new Date().getTime() - this.startTime;

    if (this.elapsedTime <= this.options.allowedTime) {
      if (Math.abs(this.distX) >= this.options.threshold && Math.abs(this.distY) <= this.options.restraint) {
        const direction = this.distX < 0 ? 'left' : 'right';
        this.handleSwipe(direction);
      }
    }
  }

  handleSwipe(direction) {
    if (this.options.onSwipeLeft && direction === 'left') {
      this.options.onSwipeLeft();
    }
    if (this.options.onSwipeRight && direction === 'right') {
      this.options.onSwipeRight();
    }
  }
}

// ===============================================
// MOBILE MENU WITH SWIPE
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
  const navMenu = document.getElementById('nav-menu');
  const navWrapper = navMenu?.parentElement;
  const menuToggle = document.getElementById('menu-toggle');

  if (navWrapper && window.innerWidth <= 768) {
    // Add swipe to close menu
    new SwipeDetector(navWrapper, {
      onSwipeLeft: () => {
        navWrapper.classList.remove('active');
        if (menuToggle) menuToggle.textContent = '☰';
      }
    });

    // Close menu on backdrop click
    navWrapper.addEventListener('click', (e) => {
      if (e.target === navWrapper) {
        navWrapper.classList.remove('active');
        if (menuToggle) menuToggle.textContent = '☰';
      }
    });
  }
});

// ===============================================
// PULL TO REFRESH (optional)
// ===============================================

let pullStartY = 0;
let pullMoveY = 0;
let pullRefreshActive = false;

function initPullToRefresh() {
  if (window.innerWidth > 768) return; // Desktop only

  document.addEventListener('touchstart', (e) => {
    if (window.pageYOffset === 0) {
      pullStartY = e.touches[0].screenY;
      pullRefreshActive = true;
    }
  }, { passive: true });

  document.addEventListener('touchmove', (e) => {
    if (!pullRefreshActive) return;

    pullMoveY = e.touches[0].screenY;
    const pullDistance = pullMoveY - pullStartY;

    if (pullDistance > 100 && window.pageYOffset === 0) {
      // Show refresh indicator (implement if needed)
      console.log('Pull to refresh triggered');
    }
  }, { passive: true });

  document.addEventListener('touchend', () => {
    pullRefreshActive = false;
    pullStartY = 0;
    pullMoveY = 0;
  }, { passive: true });
}

// Uncomment to enable pull to refresh
// initPullToRefresh();

// ===============================================
// MOBILE VIEWPORT HEIGHT FIX (for iOS)
// ===============================================

function setVH() {
  const vh = window.innerHeight * 0.01;
  document.documentElement.style.setProperty('--vh', `${vh}px`);
}

setVH();
window.addEventListener('resize', setVH);
window.addEventListener('orientationchange', setVH);

// ===============================================
// MOBILE CARD CAROUSEL (for horizontal scroll)
// ===============================================

class CardCarousel {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    if (!this.container || window.innerWidth > 768) return;

    this.init();
  }

  init() {
    // Add scroll snap
    this.container.style.scrollSnapType = 'x mandatory';
    this.container.style.overflowX = 'auto';
    this.container.style.display = 'flex';
    this.container.style.gap = 'var(--spacing-md)';

    const cards = this.container.querySelectorAll('.card');
    cards.forEach(card => {
      card.style.scrollSnapAlign = 'start';
      card.style.minWidth = '280px';
    });

    // Add scroll indicators
    this.addScrollIndicators();
  }

  addScrollIndicators() {
    const cards = this.container.querySelectorAll('.card');
    if (cards.length <= 1) return;

    const indicators = document.createElement('div');
    indicators.className = 'carousel-indicators';
    indicators.style.cssText = `
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 1rem;
    `;

    cards.forEach((_, index) => {
      const dot = document.createElement('span');
      dot.className = 'indicator-dot';
      dot.style.cssText = `
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--gray-light);
        transition: background-color 0.3s;
      `;
      if (index === 0) {
        dot.style.backgroundColor = 'var(--taxi-yellow)';
      }
      indicators.appendChild(dot);
    });

    this.container.parentElement.appendChild(indicators);

    // Update active indicator on scroll
    this.container.addEventListener('scroll', () => {
      const scrollLeft = this.container.scrollLeft;
      const cardWidth = cards[0].offsetWidth;
      const activeIndex = Math.round(scrollLeft / cardWidth);

      indicators.querySelectorAll('.indicator-dot').forEach((dot, index) => {
        dot.style.backgroundColor = index === activeIndex
          ? 'var(--taxi-yellow)'
          : 'var(--gray-light)';
      });
    });
  }
}

// ===============================================
// LAZY LOADING FOR MOBILE PERFORMANCE
// ===============================================

function initLazyLoading() {
  const images = document.querySelectorAll('img[data-src]');

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));
}

if ('IntersectionObserver' in window) {
  initLazyLoading();
}

// ===============================================
// MOBILE SCROLL POSITION MEMORY
// ===============================================

let scrollPositions = {};

window.addEventListener('beforeunload', () => {
  scrollPositions[window.location.pathname] = window.pageYOffset;
  sessionStorage.setItem('scrollPositions', JSON.stringify(scrollPositions));
});

window.addEventListener('load', () => {
  const saved = sessionStorage.getItem('scrollPositions');
  if (saved) {
    scrollPositions = JSON.parse(saved);
    const savedPosition = scrollPositions[window.location.pathname];
    if (savedPosition) {
      window.scrollTo(0, savedPosition);
    }
  }
});

// ===============================================
// MOBILE PERFORMANCE MONITORING
// ===============================================

function checkMobilePerformance() {
  if (!window.performance || window.innerWidth > 768) return;

  window.addEventListener('load', () => {
    const perfData = window.performance.timing;
    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;

    console.log('📱 Mobile Performance:');
    console.log(`⏱️  Page Load Time: ${pageLoadTime}ms`);

    // Warn if slow
    if (pageLoadTime > 3000) {
      console.warn('⚠️  Page load is slow on mobile. Consider optimizing.');
    }
  });
}

checkMobilePerformance();

// ===============================================
// MOBILE ONLINE/OFFLINE DETECTION
// ===============================================

function showNetworkStatus() {
  const showMessage = (message, type = 'info') => {
    const existing = document.querySelector('.network-status');
    if (existing) existing.remove();

    const statusBar = document.createElement('div');
    statusBar.className = `network-status alert alert-${type}`;
    statusBar.style.cssText = `
      position: fixed;
      top: 70px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9999;
      min-width: 200px;
      animation: slideDown 0.3s ease;
    `;
    statusBar.textContent = message;

    document.body.appendChild(statusBar);

    setTimeout(() => {
      statusBar.style.animation = 'slideUp 0.3s ease';
      setTimeout(() => statusBar.remove(), 300);
    }, 3000);
  };

  window.addEventListener('online', () => {
    showMessage('✅ Connessione ripristinata', 'success');
  });

  window.addEventListener('offline', () => {
    showMessage('⚠️ Nessuna connessione internet', 'warning');
  });
}

if (window.innerWidth <= 768) {
  showNetworkStatus();
}

// ===============================================
// MOBILE HAPTIC FEEDBACK (for supported devices)
// ===============================================

function vibrate(pattern = 10) {
  if ('vibrate' in navigator) {
    navigator.vibrate(pattern);
  }
}

// Add haptic feedback to buttons
document.addEventListener('DOMContentLoaded', () => {
  if (window.innerWidth <= 768) {
    const buttons = document.querySelectorAll('.btn, .card-link');
    buttons.forEach(button => {
      button.addEventListener('touchstart', () => {
        vibrate(10);
      }, { passive: true });
    });
  }
});

// ===============================================
// MOBILE SAFE AREA UTILITIES
// ===============================================

function getSafeAreaInsets() {
  const style = getComputedStyle(document.documentElement);
  return {
    top: style.getPropertyValue('--safe-area-inset-top') || '0px',
    bottom: style.getPropertyValue('--safe-area-inset-bottom') || '0px',
    left: style.getPropertyValue('--safe-area-inset-left') || '0px',
    right: style.getPropertyValue('--safe-area-inset-right') || '0px'
  };
}

// ===============================================
// EXPORT FOR MODULE USE
// ===============================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SwipeDetector,
    CardCarousel,
    vibrate,
    getSafeAreaInsets
  };
}
