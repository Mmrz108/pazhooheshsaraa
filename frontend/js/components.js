const U = () => window.SiteUtils;

const DEFAULT_COURSE_CATEGORIES = [
  { slug: 'extracurricular', title: 'فوق برنامه', order: 1 },
  { slug: 'gifted', title: 'تیزهوشان', order: 2 },
  { slug: 'academy', title: 'آکادمی', order: 3 },
  { slug: 'olympiad', title: 'المپیاد', order: 4 },
  { slug: 'support', title: 'تقویتی', order: 5 },
];

const NAV_ITEMS = [
  { type: 'course', slug: 'extracurricular', title: 'فوق برنامه' },
  { type: 'course', slug: 'gifted', title: 'تیزهوشان' },
  { type: 'course', slug: 'academy', title: 'آکادمی' },
  { type: 'course', slug: 'olympiad', title: 'المپیاد' },
  { type: 'course', slug: 'support', title: 'تقویتی' },
  { type: 'anchor', href: '#associations', title: 'انجمن\u200cها' },
  { type: 'anchor', href: '#festivals', title: 'جشنواره\u200cها' },
];

function mergeCategories(apiCategories) {
  const merged = new Map(DEFAULT_COURSE_CATEGORIES.map((cat) => [cat.slug, { ...cat }]));
  (apiCategories || []).forEach((cat) => {
    if (cat?.slug) merged.set(cat.slug, { ...merged.get(cat.slug), ...cat });
  });
  return [...merged.values()].sort((a, b) => (a.order ?? 99) - (b.order ?? 99));
}

function renderLogoHtml() {
  const { SITE_LOGO, SITE_NAME, SITE_TAGLINE, escapeHtml } = U();
  return `
    <img class="logo-img" src="${SITE_LOGO}" alt="${escapeHtml(SITE_NAME)}" width="42" height="42">
    <div>
      <span class="logo-text">${escapeHtml(SITE_NAME)}</span>
      <span class="logo-sub">${escapeHtml(SITE_TAGLINE)}</span>
    </div>`;
}

function renderNavLinks(activeSlug) {
  const homePrefix = activeSlug !== null && activeSlug !== undefined ? '/' : '';
  return NAV_ITEMS.map((item) => {
    if (item.type === 'anchor') {
      const anchorHref = homePrefix ? `/${item.href}` : item.href;
      return `<a href="${anchorHref}">${U().escapeHtml(item.title)}</a>`;
    }
    const cls = activeSlug === item.slug ? ' class="active"' : '';
    return `<a href="/courses/${encodeURIComponent(item.slug)}/"${cls}>${U().escapeHtml(item.title)}</a>`;
  }).join('');
}

function syncSiteTopBar() {
  const top = document.querySelector('[data-site-top]');
  const spacer = document.querySelector('[data-site-top-spacer]');
  if (!top || !spacer) return;

  if (window.innerWidth <= 767) {
    const height = top.offsetHeight;
    spacer.style.display = 'block';
    spacer.style.height = `${height}px`;
    document.documentElement.style.setProperty('--site-top-height', `${height}px`);
    if (window.SiteUtils?.getPageType?.().type === 'home') {
      const navType = performance.getEntriesByType('navigation')[0]?.type;
      const shouldReset = navType === 'reload' || navType === 'back_forward' || !window.location.hash;
      if (shouldReset) {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }
    }
  } else {
    spacer.style.display = 'none';
    spacer.style.height = '0';
  }
}

function initLayout(activeSlug) {
  document.querySelectorAll('[data-site-nav]').forEach((el) => {
    el.innerHTML = renderNavLinks(activeSlug);
  });
  bindScrollNav();
  syncSiteTopBar();
  if (!window.__siteTopBarResizeBound) {
    window.addEventListener('resize', syncSiteTopBar, { passive: true });
    window.addEventListener('load', syncSiteTopBar, { passive: true });
    window.__siteTopBarResizeBound = true;
  }
  requestAnimationFrame(syncSiteTopBar);
}

function bindScrollNav() {
  const scrollLinks = document.querySelectorAll('.scroll-nav a');
  scrollLinks.forEach((link) => {
    link.addEventListener('click', function () {
      scrollLinks.forEach((l) => l.classList.remove('active'));
      this.classList.add('active');
    });
  });
}

function applySiteLogo(customUrl) {
  const { SITE_LOGO } = U();
  const src = customUrl || SITE_LOGO;
  document.querySelectorAll('.logo-img').forEach((img) => {
    img.onerror = () => {
      img.onerror = null;
      img.src = SITE_LOGO;
    };
    img.src = src;
  });
}

const COURSE_ICON_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>';
const ARTICLE_ICON_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';

function courseThumbPlaceholder() {
  return `<div class="course-thumb-placeholder" aria-hidden="true">${COURSE_ICON_SVG}</div>`;
}

function articleThumbPlaceholder() {
  return `<div class="article-thumb article-thumb-placeholder" aria-hidden="true">${ARTICLE_ICON_SVG}</div>`;
}

function courseHeroPlaceholder() {
  return `<div class="course-hero-placeholder" aria-hidden="true">${COURSE_ICON_SVG}</div>`;
}

function articleHeroPlaceholder() {
  return `<div class="article-hero-placeholder" aria-hidden="true">${ARTICLE_ICON_SVG}</div>`;
}

function bindThumbFallbacks(container) {
  if (!container) return;

  container.querySelectorAll('img[data-course-thumb-fallback], img.course-hero-img[data-course-thumb-fallback]').forEach((img) => {
    if (img.dataset.fallbackBound) return;
    img.dataset.fallbackBound = '1';
    img.addEventListener('error', () => {
      const placeholder = document.createElement('div');
      placeholder.className = img.classList.contains('course-hero-img')
        ? 'course-hero-placeholder'
        : 'course-thumb-placeholder';
      placeholder.setAttribute('aria-hidden', 'true');
      placeholder.innerHTML = COURSE_ICON_SVG;
      img.replaceWith(placeholder);
    }, { once: true });
  });

  container.querySelectorAll('img[data-article-thumb-fallback], img.article-hero-img[data-article-thumb-fallback]').forEach((img) => {
    if (img.dataset.fallbackBound) return;
    img.dataset.fallbackBound = '1';
    img.addEventListener('error', () => {
      const placeholder = document.createElement('div');
      placeholder.className = img.classList.contains('article-hero-img')
        ? 'article-hero-placeholder'
        : 'article-thumb article-thumb-placeholder';
      placeholder.setAttribute('aria-hidden', 'true');
      placeholder.innerHTML = ARTICLE_ICON_SVG;
      img.replaceWith(placeholder);
    }, { once: true });
  });
}

function renderCourseCard(course, index, options = {}) {
  const { BADGE_CLASSES, LEVEL_LABELS, AGE_LABELS, formatPrice, mediaUrl, escapeHtml } = U();
  const { compact = false } = options;
  const detailUrl = `/course/${encodeURIComponent(course.slug)}/`;
  const thumbInner = course.image
    ? `<img class="course-thumb" src="${mediaUrl(course.image)}" alt="${escapeHtml(course.title)}" loading="lazy" data-course-thumb-fallback>`
    : courseThumbPlaceholder();

  const level = LEVEL_LABELS[course.level] || course.level;
  const categoryTitle = course.category?.title || '';
  const remaining = course.remaining_capacity ?? 0;
  const registrationClosed = course.registration_open === false;
  const enrollBtn = course.is_full
    ? `<span class="btn-course btn-course-disabled" aria-disabled="true">ظرفیت تکمیل</span>`
    : registrationClosed
      ? `<span class="btn-course btn-course-disabled" aria-disabled="true">مهلت ثبت\u200cنام تمام شد</span>`
      : `<a href="${detailUrl}" class="btn-course">ثبت\u200cنام</a>`;

  if (compact) {
    return `
      <article class="course-card fade-up" role="listitem">
        <a href="${detailUrl}" class="course-card-link" aria-label="جزئیات ${escapeHtml(course.title)}">
          ${thumbInner}
          <div class="course-body">
            <div class="course-meta">
              <span class="badge ${BADGE_CLASSES[index % BADGE_CLASSES.length]}">${escapeHtml(categoryTitle || AGE_LABELS[course.age_group] || '')}</span>
              <span class="badge badge-green">${escapeHtml(level)}</span>
            </div>
            <h3 class="course-title">${escapeHtml(course.title)}</h3>
            <div class="course-info">
              <span class="course-info-item">${formatPrice(course.price)}</span>
              <span class="course-info-item">${remaining} جای خالی</span>
            </div>
          </div>
        </a>
        <div style="padding:0 1rem 1rem">${enrollBtn}</div>
      </article>`;
  }

  return `
    <article class="course-card fade-up" role="listitem">
      <a href="${detailUrl}" class="course-card-link" aria-label="جزئیات ${escapeHtml(course.title)}">
        ${thumbInner}
        <div class="course-body">
          <div class="course-meta">
            <span class="badge ${BADGE_CLASSES[index % BADGE_CLASSES.length]}">${escapeHtml(categoryTitle || AGE_LABELS[course.age_group] || '')}</span>
            <span class="badge badge-green">${escapeHtml(level)}</span>
          </div>
          <h3 class="course-title">${escapeHtml(course.title)}</h3>
          <div class="course-info">
            <span class="course-info-item">${formatPrice(course.price)}</span>
            <span class="course-info-item">${remaining} جای خالی</span>
          </div>
        </div>
      </a>
      <div class="course-actions" style="padding:0 1rem 1rem">
        <a href="${detailUrl}" class="btn-course-outline">جزئیات</a>
        ${enrollBtn}
      </div>
    </article>`;
}

function renderArticleCard(article, index) {
  const { formatDate, mediaUrl, escapeHtml } = U();
  const detailUrl = `/articles/${encodeURIComponent(article.slug)}/`;
  const thumb = article.image
    ? `<img class="article-thumb" src="${mediaUrl(article.image)}" alt="${escapeHtml(article.title)}" loading="lazy" data-article-thumb-fallback>`
    : articleThumbPlaceholder();

  return `
    <a href="${detailUrl}" class="article-card fade-up" role="listitem">
      ${thumb}
      <div class="article-body">
        <div class="article-cat">${escapeHtml(article.category?.title || 'مقاله')}</div>
        <h3 class="article-title">${escapeHtml(article.title)}</h3>
        <p class="article-excerpt">${escapeHtml(article.excerpt || '')}</p>
        <div class="article-date">${formatDate(article.publish_date)}</div>
      </div>
    </a>`;
}

function renderArticlesGrid(articles, container) {
  if (!container) return;
  if (!articles.length) {
    U().showEmpty(container, 'هنوز مقاله\u200cای منتشر نشده است.');
    return;
  }
  container.innerHTML = articles.map(renderArticleCard).join('');
  bindThumbFallbacks(container);
  U().bindFadeUp(container);
}

const TOPIC_ICON_PATHS = {
  robot: '<rect x="4" y="10" width="16" height="12" rx="2"/><path d="M9 10V6a3 3 0 0 1 6 0v4"/><circle cx="9" cy="16" r="1"/><circle cx="15" cy="16" r="1"/><path d="M12 6V4"/>',
  code: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
  astronomy: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
  biology: '<path d="M12 22s-8-4.5-8-11a8 8 0 0 1 16 0c0 6.5-8 11-8 11z"/><path d="M12 11v11"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  dna: '<path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/><path d="M6 7c2 2 4 2 6 0s4-2 6 0"/><path d="M6 17c2 2 4 2 6 0s4-2 6 0"/>',
  cells: '<circle cx="7" cy="7" r="3"/><circle cx="17" cy="17" r="3"/><path d="M9.5 9.5l5 5"/>',
  plant: '<path d="M7 20h10"/><path d="M12 20V10"/><path d="M12 10c-4-3-8-1.5-8 2a8 8 0 0 0 16 0c0-3.5-4-5-8-2z"/>',
  nano: '<circle cx="12" cy="12" r="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>',
  flask: '<path d="M10 2v6.3a4 4 0 0 0 .9 2.5L18 20a2 2 0 0 1-1.8 3H7.8A2 2 0 0 1 6 20l7.1-9.2a4 4 0 0 0 .9-2.5V2"/><line x1="9" y1="2" x2="15" y2="2"/>',
  transport: '<path d="M7 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M17 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/><path d="M5 17H3v-6l2-5h9l4 5h1a2 2 0 0 1 2 2v4h-2"/><path d="M9 17h6"/>',
  festival: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
  math: '<line x1="5" y1="8" x2="19" y2="8"/><path d="M7 4l10 16"/><path d="M17 4L7 20"/>',
  physics: '<circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="9" ry="3.5"/><ellipse cx="12" cy="12" rx="9" ry="3.5" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="3.5" transform="rotate(120 12 12)"/>',
  chemistry: '<path d="M9 3h6"/><path d="M10 3v6.8L4.8 18.2a1 1 0 0 0 .9 1.5h12.6a1 1 0 0 0 .9-1.5L14 9.8V3"/><circle cx="10" cy="16" r="1"/><circle cx="14.5" cy="15" r="0.8"/>',
};

const FESTIVAL_ICON_BY_SLUG = {
  literature: 'book',
  biotech: 'dna',
  'stem-cells': 'cells',
  coding: 'code',
  astronomy: 'astronomy',
  'medicinal-plants': 'plant',
  nano: 'nano',
  laboratory: 'flask',
  transport: 'transport',
};

function topicIconSvg(key, size = 28) {
  const paths = TOPIC_ICON_PATHS[key] || TOPIC_ICON_PATHS.festival;
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
}

function associationIconKey(item) {
  const slug = item.slug || '';
  const title = item.title || '';
  if (/ریاضی|math/i.test(title) || slug.includes('ریاضی') || slug.includes('math')) return 'math';
  if (/فیزیک|physics/i.test(title) || slug.includes('فیزیک') || slug.includes('physics')) return 'physics';
  if (/شیمی|chemistry|chem/i.test(title) || slug.includes('شیمی') || slug.includes('chemistry')) return 'chemistry';
  if (/ربات|robot/i.test(title) || slug.includes('ربات')) return 'robot';
  if (/برنامه|نرم|کد|code/i.test(title) || slug.includes('برنامه')) return 'code';
  if (/نجوم|astro/i.test(title) || slug.includes('نجوم')) return 'astronomy';
  if (/زیست|bio/i.test(title) || slug.includes('زیست')) return 'biology';
  return 'users';
}

function festivalIconKey(item) {
  const slug = (item.slug || '').toLowerCase();
  if (FESTIVAL_ICON_BY_SLUG[slug]) return FESTIVAL_ICON_BY_SLUG[slug];
  const title = item.title || '';
  if (/ادبیات|literature/i.test(title)) return 'book';
  if (/زیست|فناوری|biotech/i.test(title)) return 'dna';
  if (/سلول|stem/i.test(title)) return 'cells';
  if (/کد|برنامه|coding/i.test(title)) return 'code';
  if (/نجوم|astro/i.test(title)) return 'astronomy';
  if (/گیاه|plant/i.test(title)) return 'plant';
  if (/نانو|nano/i.test(title)) return 'nano';
  if (/آزمایش|lab/i.test(title)) return 'flask';
  if (/حمل|transport/i.test(title)) return 'transport';
  return 'festival';
}

function renderAssociationIcon(item) {
  const key = associationIconKey(item);
  return `<div class="assoc-icon-wrap" aria-hidden="true">${topicIconSvg(key)}</div>`;
}

function renderFestivalIcon(item) {
  const key = festivalIconKey(item);
  return `<div class="fest-icon-wrap" aria-hidden="true">${topicIconSvg(key)}</div>`;
}

function renderTopicHeroIcon(item, type) {
  const key = type === 'association' ? associationIconKey(item) : festivalIconKey(item);
  const tone = type === 'association' ? 'assoc' : 'fest';
  return `<div class="content-hero-icon content-hero-icon-${tone}" aria-hidden="true">${topicIconSvg(key, 80)}</div>`;
}

function renderAssociationCard(item, index) {
  const { escapeHtml } = U();
  const cardClass = `assoc-card-${(index % 5) + 1}`;
  const detailUrl = `/associations/${encodeURIComponent(item.slug)}/`;

  return `
    <a href="${detailUrl}" class="assoc-card ${cardClass} fade-up" role="listitem">
      ${renderAssociationIcon(item)}
      <div class="assoc-title">${escapeHtml(item.title)}</div>
      <div class="assoc-desc">${escapeHtml(item.description)}</div>
    </a>`;
}

function renderFestivalCard(item, index) {
  const { escapeHtml } = U();
  const cardClass = `fest-card-${(index % 9) + 1}`;
  const detailUrl = `/festivals/${encodeURIComponent(item.slug)}/`;

  return `
    <a href="${detailUrl}" class="fest-card ${cardClass} fade-up" role="listitem">
      ${renderFestivalIcon(item)}
      <div class="fest-title">${escapeHtml(item.title)}</div>
      <div class="fest-desc">${escapeHtml(item.description)}</div>
    </a>`;
}

function renderCoursesGrid(courses, container, options = {}) {
  if (!container) return;
  if (!courses.length) {
    U().showEmpty(container, options.emptyMessage || 'هنوز دوره\u200cای در این دسته ثبت نشده است.');
    return;
  }
  container.innerHTML = courses.map((course, index) => renderCourseCard(course, index, options)).join('');
  bindThumbFallbacks(container);
  U().bindCourseButtons(container);
  U().bindFadeUp(container);
}

window.SiteComponents = {
  DEFAULT_COURSE_CATEGORIES,
  NAV_ITEMS,
  mergeCategories,
  initLayout, bindScrollNav, applySiteLogo, syncSiteTopBar, renderCoursesGrid, renderCourseCard,
  renderArticleCard, renderArticlesGrid, renderAssociationCard, renderFestivalCard,
  renderTopicHeroIcon, associationIconKey, festivalIconKey, bindThumbFallbacks,
  courseThumbPlaceholder, articleThumbPlaceholder, courseHeroPlaceholder, articleHeroPlaceholder,
};
