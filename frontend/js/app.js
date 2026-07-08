async function loadCategories() {
  const C = window.SiteComponents;
  try {
    const data = await apiFetch('/courses/categories/');
    window.__categories = C.mergeCategories(data.results || data);
  } catch {
    window.__categories = C.mergeCategories([]);
  }
  const footerCats = document.querySelector('[data-footer-categories]');
  if (footerCats && window.__categories.length) {
    footerCats.innerHTML = window.__categories.map((c) =>
      `<li><a href="/courses/${c.slug}/"><span aria-hidden="true">›</span> ${window.SiteUtils.escapeHtml(c.title)}</a></li>`
    ).join('');
  }
}

async function loadSettings() {
  const { mediaUrl } = window.SiteUtils;
  const C = window.SiteComponents;
  try {
    const s = await apiFetch('/settings/');
    if (s.about_text) {
      document.querySelectorAll('[data-about-text]').forEach((el) => {
        el.textContent = s.about_text;
      });
    }
    if (s.phone) document.querySelectorAll('[data-site-phone]').forEach((el) => { el.textContent = s.phone; });
    if (s.email) document.querySelectorAll('[data-site-email]').forEach((el) => { el.textContent = s.email; });
    if (s.address) document.querySelectorAll('[data-site-address]').forEach((el) => { el.textContent = s.address; });
    const eitaa = document.querySelector('.float-btn-eitaa');
    if (eitaa) {
      eitaa.href = s.eitaa_link || 'https://eitaa.com/psdnj1';
      eitaa.target = '_blank';
      eitaa.rel = 'noopener noreferrer';
    }
    const heroBg = document.querySelector('.hero-bg');
    if (heroBg && s.hero_image) {
      heroBg.style.background =
        `linear-gradient(135deg, rgba(37,99,235,0.92) 0%, rgba(124,58,237,0.88) 50%, rgba(6,182,212,0.8) 100%), url('${mediaUrl(s.hero_image)}') center/cover no-repeat`;
    }
    if (s.logo) {
      C.applySiteLogo(mediaUrl(s.logo));
    } else {
      C.applySiteLogo();
    }
  } catch (err) {
    console.warn('Settings API:', err);
    C.applySiteLogo();
  }
}

function bindHorizontalReel(reel, prev, next, cardSelector) {
  if (!reel) return;

  const scrollByCard = (direction) => {
    const card = reel.querySelector(cardSelector);
    const amount = card ? card.offsetWidth + 16 : 300;
    reel.scrollBy({ left: direction * amount, behavior: 'smooth' });
  };

  prev?.addEventListener('click', () => scrollByCard(1));
  next?.addEventListener('click', () => scrollByCard(-1));
}

function bindCoursesReel() {
  bindHorizontalReel(
    document.querySelector('[data-courses-reel]'),
    document.querySelector('[data-reel-prev]'),
    document.querySelector('[data-reel-next]'),
    '.course-card',
  );
}

function bindArticlesReel() {
  bindHorizontalReel(
    document.querySelector('[data-articles-reel]'),
    document.querySelector('[data-articles-reel-prev]'),
    document.querySelector('[data-articles-reel-next]'),
    '.article-card',
  );
}

function isHomePath() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  return path === '/' || path === '/index.html';
}

function getNavigationType() {
  const nav = performance.getEntriesByType('navigation')[0];
  return nav?.type || 'navigate';
}

function scrollToHomeTop() {
  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }
  window.scrollTo(0, 0);
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
}

function shouldResetHomeScrollPosition() {
  const type = getNavigationType();
  return type === 'reload' || type === 'back_forward' || !window.location.hash;
}

function resetHomeTopNavState() {
  document.querySelectorAll('.scroll-nav a').forEach((link) => link.classList.remove('active'));
  document.querySelectorAll('.bottom-nav-item').forEach((item) => {
    const isHome = item.getAttribute('href') === '#home';
    item.classList.toggle('active', isHome);
    if (isHome) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
}

function applyHomeScrollOnLoad() {
  if (!isHomePath()) return;

  const navType = getNavigationType();
  const resetScroll = shouldResetHomeScrollPosition();

  if ((navType === 'reload' || navType === 'back_forward') && window.location.hash) {
    history.replaceState(null, '', window.location.pathname + window.location.search);
  }

  if (resetScroll) {
    scrollToHomeTop();
    resetHomeTopNavState();
    return;
  }

  requestAnimationFrame(() => {
    const target = document.querySelector(window.location.hash);
    target?.scrollIntoView({ block: 'start' });
  });
}

function bindHomeReloadScroll() {
  if (window.__homeReloadScrollBound) return;
  window.__homeReloadScrollBound = true;
  window.addEventListener('pageshow', (event) => {
    if (!isHomePath()) return;
    if (event.persisted) {
      if (window.location.hash) {
        history.replaceState(null, '', window.location.pathname + window.location.search);
      }
      scrollToHomeTop();
      resetHomeTopNavState();
      return;
    }
    applyHomeScrollOnLoad();
  });
}

function hideHomeCoursesSection() {
  document.querySelector('#courses')?.remove();
  document.querySelector('.divider-courses')?.remove();
}

async function initHomePage() {
  const { showEmpty, bindFadeUp, bindCourseButtons, setSEO, escapeHtml } = window.SiteUtils;
  const C = window.SiteComponents;

  setSEO({
    title: 'پژوهش\u200cسرا | مرکز آموزش علوم و فناوری',
    description: 'آموزش برنامه\u200cنویسی، رباتیک، هوش مصنوعی، المپیاد و آکادمی — پژوهش\u200cسرا',
    canonical: window.location.origin + '/',
  });

  applyHomeScrollOnLoad();
  bindHomeReloadScroll();

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();
  applyHomeScrollOnLoad();

  const coursesTrack = document.querySelector('#courses .courses-track');
  const articlesTrack = document.querySelector('#articles .articles-track');
  const assocGrid = document.querySelector('#associations .assoc-grid');
  const festGrid = document.querySelector('#festivals .fest-grid');

  try {
    const data = await apiFetch('/courses/?limit=6');
    const courses = data.results || data;
    if (courses.length) {
      coursesTrack.innerHTML = courses.map((course, index) => C.renderCourseCard(course, index, { compact: true })).join('');
      C.bindThumbFallbacks(coursesTrack);
      bindCourseButtons(coursesTrack);
      bindCoursesReel();
    } else {
      hideHomeCoursesSection();
    }
  } catch {
    if (coursesTrack) {
      showEmpty(coursesTrack, 'خطا در بارگذاری دوره\u200cها. سرور را بررسی کنید و صفحه را رفرش کنید.');
    }
  }

  try {
    const data = await apiFetch('/articles/?limit=6');
    const articles = data.results || data;
    if (articles.length) {
      articlesTrack.innerHTML = articles.map(C.renderArticleCard).join('');
      C.bindThumbFallbacks(articlesTrack);
      bindArticlesReel();
      bindFadeUp(document.querySelector('#articles'));
    } else {
      showEmpty(articlesTrack, 'هنوز مقاله\u200cای منتشر نشده است.');
    }
  } catch {
    showEmpty(articlesTrack, 'خطا در بارگذاری مقالات.');
  }

  try {
    const data = await apiFetch('/associations/');
    const items = data.results || data;
    if (items.length) {
      assocGrid.innerHTML = items.map(C.renderAssociationCard).join('');
    } else {
      showEmpty(assocGrid, 'هنوز انجمنی ثبت نشده است.');
    }
  } catch {
    showEmpty(assocGrid, 'خطا در بارگذاری انجمن\u200cها.');
  }

  try {
    const data = await apiFetch('/festivals/');
    const festivals = data.results || data;
    if (festivals.length) {
      festGrid.innerHTML = festivals.map(C.renderFestivalCard).join('');
    } else {
      showEmpty(festGrid, 'هنوز جشنواره\u200cای ثبت نشده است.');
    }
  } catch {
    showEmpty(festGrid, 'خطا در بارگذاری جشنواره\u200cها.');
  }

  bindFadeUp(document);
  initPageScripts();
  loadSettings().then(() => applyHomeScrollOnLoad());
  requestAnimationFrame(() => applyHomeScrollOnLoad());
}

async function initCoursesPage(activeCategory) {
  const { setSEO, escapeHtml } = window.SiteUtils;
  const C = window.SiteComponents;

  await loadCategories();
  C.initLayout(activeCategory || '');
  C.applySiteLogo();

  const filtersEl = document.querySelector('[data-course-filters]');
  const grid = document.querySelector('[data-courses-grid]');
  let allCourses = [];
  let currentFilter = activeCategory || 'all';
  if (currentFilter !== 'all' && !(window.__categories || []).some((c) => c.slug === currentFilter)) {
    currentFilter = 'all';
  }

  const renderFilters = () => {
    if (!filtersEl) return;
    const categories = window.__categories || [];
    const buttons = [
      `<button type="button" class="course-filter${currentFilter === 'all' ? ' active' : ''}" data-filter="all" role="tab" aria-selected="${currentFilter === 'all'}">همه</button>`,
      ...categories.map((cat) => {
        const active = currentFilter === cat.slug ? ' active' : '';
        return `<button type="button" class="course-filter${active}" data-filter="${escapeHtml(cat.slug)}" role="tab" aria-selected="${currentFilter === cat.slug}">${escapeHtml(cat.title)}</button>`;
      }),
    ];
    filtersEl.innerHTML = buttons.join('');
    filtersEl.querySelectorAll('[data-filter]').forEach((btn) => {
      btn.addEventListener('click', () => {
        currentFilter = btn.dataset.filter;
        const url = currentFilter === 'all' ? '/courses/' : `/courses/${currentFilter}/`;
        window.history.replaceState({}, '', url);
        C.initLayout(currentFilter === 'all' ? '' : currentFilter);
        renderFilters();
        renderCourses();
      });
    });
  };

  const renderCourses = () => {
    const filtered = currentFilter === 'all'
      ? allCourses
      : allCourses.filter((course) => course.category?.slug === currentFilter);
    C.renderCoursesGrid(filtered, grid, {
      emptyMessage: 'هنوز دوره\u200cای در این دسته ثبت نشده است.',
    });
  };

  try {
    const data = await apiFetch('/courses/?page_size=100');
    allCourses = data.results || data;
    const activeCat = (window.__categories || []).find((c) => c.slug === currentFilter);
    const pageTitle = activeCat
      ? `دوره\u200cهای ${activeCat.title} | پژوهش\u200cسرا`
      : 'دوره\u200cهای آموزشی | پژوهش\u200cسرا';
    const pageDesc = activeCat?.description || 'لیست همه دوره\u200cهای آموزشی پژوهش\u200cسرا';

    setSEO({
      title: pageTitle,
      description: pageDesc,
      canonical: `${window.location.origin}${currentFilter === 'all' ? '/courses/' : `/courses/${currentFilter}/`}`,
    });

    renderFilters();
    renderCourses();
  } catch {
    setSEO({ title: 'دوره\u200cهای آموزشی | پژوهش\u200cسرا' });
    window.SiteUtils.showEmpty(grid, 'خطا در بارگذاری دوره\u200cها.');
  }

  initPageScripts();
  loadSettings();
}

async function initCourseDetailPage(slug) {
  const { setSEO, formatPrice, formatDate, mediaUrl, escapeHtml, bindCourseButtons } = window.SiteUtils;
  const C = window.SiteComponents;
  const container = document.querySelector('[data-course-detail]');

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();

  try {
    const course = await apiFetch(`/courses/${encodeURIComponent(slug)}/`);
    const categoryTitle = course.category?.title || '';
    const pageTitle = `${course.title} | پژوهش\u200cسرا`;
    const hero = course.image
      ? `<img class="course-hero-img" src="${mediaUrl(course.image)}" alt="${escapeHtml(course.title)}" data-course-thumb-fallback>`
      : C.courseHeroPlaceholder();
    const scheduleText = (course.schedule || '').trim();
    const registrationClosed = course.registration_open === false;
    const deadlineLine = course.registration_deadline_jalali
      ? `<li><span>فرصت ثبت\u200cنام تا</span><span>${escapeHtml(course.registration_deadline_jalali)}</span></li>`
      : '';
    const scheduleSection = `
      <section class="course-schedule" aria-labelledby="course-schedule-heading">
        <h2 class="course-schedule-title" id="course-schedule-heading">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          روزها و ساعت برگزاری
        </h2>
        <div class="schedule-box">${scheduleText
          ? escapeHtml(scheduleText).replace(/\n/g, '<br>')
          : '<span class="schedule-placeholder">زمان برگزاری به\u200cزودی از طریق پنل مدیریت اعلام می\u200cشود.</span>'}</div>
      </section>`;

    setSEO({
      title: pageTitle,
      description: course.description?.slice(0, 160) || pageTitle,
      canonical: `${window.location.origin}/course/${slug}/`,
      jsonLd: {
        '@context': 'https://schema.org',
        '@type': 'Course',
        name: course.title,
        description: course.description,
        provider: { '@type': 'Organization', name: 'پژوهش\u200cسرا' },
        offers: {
          '@type': 'Offer',
          price: course.price,
          priceCurrency: 'IRR',
        },
      },
    });

    if (container) {
      container.innerHTML = `
        <nav class="breadcrumb" aria-label="مسیر">
          <a href="/">صفحه اصلی</a> ›
          <a href="/courses/">دوره\u200cها</a> ›
          ${categoryTitle ? `<a href="/courses/${escapeHtml(course.category.slug)}/">${escapeHtml(categoryTitle)}</a> ›` : ''}
          <span>${escapeHtml(course.title)}</span>
        </nav>
        <div class="course-detail">
          <div>
            <div class="course-hero">${hero}</div>
            <div class="course-content" style="background:#fff;border:1.5px solid #E2E8F0;border-radius:16px;margin-top:1rem">
              <div class="course-badges">
                ${categoryTitle ? `<span class="badge badge-blue">${escapeHtml(categoryTitle)}</span>` : ''}
                <span class="badge badge-green">${escapeHtml(window.SiteUtils.LEVEL_LABELS[course.level] || course.level)}</span>
              </div>
              <h1 class="course-title">${escapeHtml(course.title)}</h1>
              <p class="course-desc">${escapeHtml(course.description || '')}</p>
              ${scheduleSection}
            </div>
          </div>
          <aside class="course-sidebar">
            <div class="price-box">${formatPrice(course.price)}</div>
            <ul class="info-list">
              <li><span>ظرفیت باقی\u200cمانده</span><span>${course.remaining_capacity ?? 0} نفر</span></li>
              <li><span>تاریخ شروع</span><span>${escapeHtml(course.start_date_jalali || formatDate(course.start_date))}</span></li>
              <li><span>تاریخ پایان</span><span>${escapeHtml(course.end_date_jalali || formatDate(course.end_date))}</span></li>
              <li><span>گروه سنی</span><span>${escapeHtml(window.SiteUtils.AGE_LABELS[course.age_group] || course.age_group)}</span></li>
              ${deadlineLine}
              ${scheduleText ? `<li><span>زمان برگزاری</span><span>${escapeHtml(scheduleText).replace(/\n/g, ' · ')}</span></li>` : ''}
            </ul>
            <button type="button" class="btn-enroll" data-enroll-course="${course.id}" ${course.is_full || registrationClosed ? 'disabled' : ''}>
              ${registrationClosed ? 'مهلت ثبت\u200cنام تمام شده' : course.is_full ? 'ظرفیت تکمیل شده' : 'ثبت\u200cنام در دوره'}
            </button>
          </aside>
        </div>`;
      bindCourseButtons(container);
      C.bindThumbFallbacks(container);
    }
  } catch {
    setSEO({ title: 'دوره یافت نشد | پژوهش\u200cسرا' });
    if (container) {
      container.innerHTML = '<div class="empty-state">دوره مورد نظر یافت نشد. <a href="/courses/">بازگشت به لیست دوره\u200cها</a></div>';
    }
  }

  initPageScripts();
  loadSettings();
}

async function initArticlesPage() {
  const { setSEO } = window.SiteUtils;
  const C = window.SiteComponents;
  const grid = document.querySelector('[data-articles-grid]');

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();

  setSEO({
    title: 'مقالات | پژوهش\u200cسرا',
    description: 'آخرین مقالات آموزشی و علمی پژوهش\u200cسرا',
    canonical: `${window.location.origin}/articles/`,
  });

  try {
    const data = await apiFetch('/articles/?page_size=100');
    const articles = data.results || data;
    C.renderArticlesGrid(articles, grid);
  } catch {
    window.SiteUtils.showEmpty(grid, 'خطا در بارگذاری مقالات.');
  }

  initPageScripts();
  loadSettings();
}

async function initArticleDetailPage(slug) {
  const { setSEO, formatDate, mediaUrl, escapeHtml } = window.SiteUtils;
  const C = window.SiteComponents;
  const container = document.querySelector('[data-article-detail]');

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();

  try {
    const article = await apiFetch(`/articles/${encodeURIComponent(slug)}/`);
    const categoryTitle = article.category?.title || '';
    const pageTitle = `${article.title} | پژوهش\u200cسرا`;
    const hero = article.image
      ? `<img class="article-hero-img" src="${mediaUrl(article.image)}" alt="${escapeHtml(article.title)}" data-article-thumb-fallback>`
      : C.articleHeroPlaceholder();

    setSEO({
      title: pageTitle,
      description: article.excerpt?.slice(0, 160) || pageTitle,
      canonical: `${window.location.origin}/articles/${slug}/`,
      jsonLd: {
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: article.title,
        description: article.excerpt,
        datePublished: article.publish_date,
        author: { '@type': 'Organization', name: 'پژوهش\u200cسرا' },
      },
    });

    if (container) {
      container.innerHTML = `
        <nav class="breadcrumb" aria-label="مسیر">
          <a href="/">صفحه اصلی</a> ›
          <a href="/articles/">مقالات</a> ›
          <span>${escapeHtml(article.title)}</span>
        </nav>
        <div class="article-hero">${hero}</div>
        <article class="article-content">
          ${categoryTitle ? `<div class="article-cat">${escapeHtml(categoryTitle)}</div>` : ''}
          <h1 class="article-title">${escapeHtml(article.title)}</h1>
          <div class="article-date">${formatDate(article.publish_date)}</div>
          ${article.excerpt ? `<p class="article-excerpt">${escapeHtml(article.excerpt)}</p>` : ''}
          <div class="article-body">${escapeHtml(article.content || '')}</div>
        </article>`;
      C.bindThumbFallbacks(container);
    }
  } catch {
    setSEO({ title: 'مقاله یافت نشد | پژوهش\u200cسرا' });
    if (container) {
      container.innerHTML = '<div class="empty-state">مقاله مورد نظر یافت نشد. <a href="/articles/">بازگشت به لیست مقالات</a></div>';
    }
  }

  initPageScripts();
  loadSettings();
}

async function initContentDetailPage({ apiPath, listPath, listLabel, notFoundLabel, containerSelector, iconType }) {
  const { setSEO, escapeHtml } = window.SiteUtils;
  const C = window.SiteComponents;
  const container = document.querySelector(containerSelector);
  const page = window.SiteUtils.getPageType();
  const slug = page.slug;

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();

  try {
    const item = await apiFetch(`${apiPath}${encodeURIComponent(slug)}/`);
    const pageTitle = `${item.title} | پژوهش\u200cسرا`;
    const hero = C.renderTopicHeroIcon(item, iconType);

    setSEO({
      title: pageTitle,
      description: item.description?.slice(0, 160) || pageTitle,
      canonical: `${window.location.origin}${window.location.pathname}`,
    });

    if (container) {
      container.innerHTML = `
        <nav class="breadcrumb" aria-label="مسیر">
          <a href="/">صفحه اصلی</a> ›
          <a href="${listPath}">${escapeHtml(listLabel)}</a> ›
          <span>${escapeHtml(item.title)}</span>
        </nav>
        <div class="content-hero">${hero}</div>
        <article class="content-body">
          <h1 class="content-title">${escapeHtml(item.title)}</h1>
          ${item.description ? `<p class="content-excerpt">${escapeHtml(item.description)}</p>` : ''}
          <div class="content-text">${escapeHtml(item.content || '')}</div>
        </article>`;
    }
  } catch {
    setSEO({ title: `${notFoundLabel} | پژوهش\u200cسرا` });
    if (container) {
      container.innerHTML = `<div class="empty-state">${escapeHtml(notFoundLabel)}. <a href="${listPath}">بازگشت</a></div>`;
    }
  }

  initPageScripts();
  loadSettings();
}

async function initAssociationDetailPage(slug) {
  await initContentDetailPage({
    apiPath: '/associations/',
    listPath: '/#associations',
    listLabel: 'انجمن\u200cها',
    notFoundLabel: 'انجمن مورد نظر یافت نشد',
    containerSelector: '[data-association-detail]',
    iconType: 'association',
  });
}

async function initFestivalDetailPage(slug) {
  await initContentDetailPage({
    apiPath: '/festivals/',
    listPath: '/#festivals',
    listLabel: 'جشنواره\u200cها',
    notFoundLabel: 'جشنواره مورد نظر یافت نشد',
    containerSelector: '[data-festival-detail]',
    iconType: 'festival',
  });
}

function initPageScripts() {
  document.querySelectorAll('.fade-up').forEach((el) => {
    if (!el.classList.contains('visible')) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('visible');
            observer.unobserve(e.target);
          }
        });
      }, { threshold: 0.1 });
      observer.observe(el);
    }
  });

  window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    if (!header) return;
    header.style.boxShadow = window.scrollY > 10 ? '0 2px 20px rgba(0,0,0,0.08)' : 'none';
  }, { passive: true });
}

document.addEventListener('DOMContentLoaded', async () => {
  const page = window.SiteUtils.getPageType();
  if (page.type === 'course') {
    await initCourseDetailPage(page.slug);
  } else if (page.type === 'courses') {
    await initCoursesPage(page.category);
  } else if (page.type === 'article') {
    await initArticleDetailPage(page.slug);
  } else if (page.type === 'articles') {
    await initArticlesPage();
  } else if (page.type === 'association') {
    await initAssociationDetailPage(page.slug);
  } else if (page.type === 'festival') {
    await initFestivalDetailPage(page.slug);
  } else {
    await initHomePage();
  }
});
