const SITE_LOGO = '/images/logo.jpg';
const SITE_NAME = 'پژوهش سرای شهید حجتی';
const SITE_TAGLINE = 'نجف آباد · اصفهان';

const LEVEL_LABELS = {
  beginner: 'مقدماتی',
  intermediate: 'متوسط',
  advanced: 'پیشرفته',
};

const AGE_LABELS = {
  children: 'کودکان',
  teens: 'نوجوانان',
  adults: 'بزرگسالان',
  all: 'همه سنین',
};

const BADGE_CLASSES = ['badge-blue', 'badge-purple', 'badge-cyan', 'badge-amber', 'badge-green'];
const PLACEHOLDER_EMOJIS = ['🐍', '⚡', '🤖', '🧠', '⭐', '💻', '🔬', '🏆'];

function formatPrice(price) {
  return Number(price).toLocaleString('fa-IR') + ' تومان';
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}

function mediaUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return path.startsWith('/') ? path : `/media/${path}`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

function getPageType() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';

  const courseMatch = path.match(/^\/course\/([^/]+)$/i);
  if (courseMatch) return { type: 'course', slug: decodeURIComponent(courseMatch[1]) };

  if (path === '/courses') {
    const params = new URLSearchParams(window.location.search);
    return { type: 'courses', category: params.get('category') || '' };
  }

  const categoryMatch = path.match(/^\/courses\/([^/]+)$/i);
  if (categoryMatch) return { type: 'courses', category: decodeURIComponent(categoryMatch[1]) };

  if (path === '/articles') return { type: 'articles' };

  const articleMatch = path.match(/^\/articles\/([^/]+)$/i);
  if (articleMatch) return { type: 'article', slug: decodeURIComponent(articleMatch[1]) };

  const associationMatch = path.match(/^\/associations\/([^/]+)$/i);
  if (associationMatch) return { type: 'association', slug: decodeURIComponent(associationMatch[1]) };

  const academyMatch = path.match(/^\/academies\/([^/]+)$/i);
  if (academyMatch) return { type: 'academy', slug: decodeURIComponent(academyMatch[1]) };

  const festivalMatch = path.match(/^\/festivals\/([^/]+)$/i);
  if (festivalMatch) return { type: 'festival', slug: decodeURIComponent(festivalMatch[1]) };

  if (path === '/designer') return { type: 'designer' };

  return { type: 'home' };
}

function setSEO({ title, description, canonical, jsonLd }) {
  if (title) document.title = title;
  let metaDesc = document.querySelector('meta[name="description"]');
  if (!metaDesc) {
    metaDesc = document.createElement('meta');
    metaDesc.name = 'description';
    document.head.appendChild(metaDesc);
  }
  if (description) metaDesc.content = description;

  let canonicalLink = document.querySelector('link[rel="canonical"]');
  if (canonical) {
    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.rel = 'canonical';
      document.head.appendChild(canonicalLink);
    }
    canonicalLink.href = canonical;
  }

  const oldLd = document.getElementById('structured-data');
  if (oldLd) oldLd.remove();
  if (jsonLd) {
    const script = document.createElement('script');
    script.id = 'structured-data';
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(jsonLd);
    document.head.appendChild(script);
  }
}

function showEmpty(container, message) {
  if (!container) return;
  container.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function bindFadeUp(container) {
  if (!container) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  container.querySelectorAll('.fade-up').forEach((el) => observer.observe(el));
}

const PENDING_ENROLLMENT_KEY = 'pending_enrollment_course_id';

function setPendingEnrollment(courseId) {
  sessionStorage.setItem(PENDING_ENROLLMENT_KEY, String(courseId));
}

function getPendingEnrollment() {
  const id = sessionStorage.getItem(PENDING_ENROLLMENT_KEY);
  return id ? Number(id) : null;
}

function clearPendingEnrollment() {
  sessionStorage.removeItem(PENDING_ENROLLMENT_KEY);
}

async function startCoursePayment(courseId, btn) {
  const defaultLabel = 'ثبت\u200cنام در دوره';
  if (btn) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'در حال انتقال...';
  }
  try {
    const result = await apiFetch('/payments/start/', {
      method: 'POST',
      body: JSON.stringify({ course_id: Number(courseId) }),
    });
    clearPendingEnrollment();
    if (result.payment_url) {
      window.location.href = result.payment_url;
      return true;
    }
    throw new Error('آدرس درگاه پرداخت دریافت نشد');
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = btn.dataset.originalText || defaultLabel;
    }
    alert(err.detail || err.message || 'خطا در شروع پرداخت');
    return false;
  }
}

async function resumePendingEnrollment() {
  const courseId = getPendingEnrollment();
  if (!courseId || !localStorage.getItem('access_token')) return false;
  return startCoursePayment(courseId, null);
}

async function enrollCourse(courseId, btn) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    setPendingEnrollment(courseId);
    if (window.AuthModal?.open) {
      window.AuthModal.open();
      return;
    }
    const returnPath = `${window.location.pathname}${window.location.search}`;
    window.location.href = `/login/?auth=1&return=${encodeURIComponent(returnPath)}`;
    return;
  }
  await startCoursePayment(courseId, btn);
}

function bindCourseButtons(container) {
  container?.querySelectorAll('[data-enroll-course]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      enrollCourse(btn.dataset.enrollCourse, btn);
    });
  });
}

function scrollToSiteEnd(behavior = 'smooth') {
  const top = Math.max(
    document.documentElement.scrollHeight,
    document.body.scrollHeight,
  ) - window.innerHeight;
  window.scrollTo({ top: Math.max(0, top), behavior });
}

function bindContactLinks() {
  if (window.__contactLinksBound) return;
  window.__contactLinksBound = true;

  document.querySelectorAll('a[href="#contact"]:not(.bottom-nav-item)').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      scrollToSiteEnd();
      history.replaceState(null, '', '#contact');
    });
  });
}

function bindBottomNav() {
  if (window.__bottomNavBound) return;
  window.__bottomNavBound = true;

  const navItems = document.querySelectorAll('.bottom-nav-item');
  if (!navItems.length) return;

  navItems.forEach((item) => {
    item.addEventListener('click', function (event) {
      if (this.getAttribute('href') === '#contact') {
        event.preventDefault();
        scrollToSiteEnd();
        history.replaceState(null, '', '#contact');
      }

      navItems.forEach((navItem) => {
        navItem.classList.remove('active');
        navItem.removeAttribute('aria-current');
      });
      this.classList.add('active');
      this.setAttribute('aria-current', 'page');
    });
  });
}

window.SiteUtils = {
  SITE_LOGO, SITE_NAME, SITE_TAGLINE,
  LEVEL_LABELS, AGE_LABELS, BADGE_CLASSES, PLACEHOLDER_EMOJIS,
  formatPrice, formatDate, mediaUrl, escapeHtml,
  getPageType, setSEO, showEmpty, bindFadeUp, bindCourseButtons, enrollCourse,
  resumePendingEnrollment, setPendingEnrollment, getPendingEnrollment, startCoursePayment,
  scrollToSiteEnd, bindContactLinks, bindBottomNav,
};
