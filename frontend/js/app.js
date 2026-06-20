async function loadCategories() {
  try {
    const data = await apiFetch('/courses/categories/');
    window.__categories = data.results || data;
  } catch {
    window.__categories = [
      { slug: 'extracurricular', title: 'فوق برنامه' },
      { slug: 'gifted', title: 'تیزهوشان' },
      { slug: 'olympiad', title: 'المپیاد' },
      { slug: 'support', title: 'تقویتی' },
    ];
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

async function initHomePage() {
  const { showEmpty, bindFadeUp, bindCourseButtons, setSEO, escapeHtml } = window.SiteUtils;
  const C = window.SiteComponents;

  setSEO({
    title: 'پژوهش\u200cسرا | مرکز آموزش علوم و فناوری',
    description: 'آموزش برنامه\u200cنویسی، رباتیک، هوش مصنوعی، المپیاد و تیزهوشان — پژوهش\u200cسرا',
    canonical: window.location.origin + '/',
  });

  await loadCategories();
  C.initLayout(null);
  C.applySiteLogo();

  const coursesTrack = document.querySelector('#courses .courses-track');
  const articlesTrack = document.querySelector('#articles .articles-track');
  const assocGrid = document.querySelector('#associations .assoc-grid');
  const galleryMasonry = document.querySelector('#gallery .gallery-masonry');
  const galleryFilters = document.querySelector('#gallery .gallery-filters');

  try {
    const data = await apiFetch('/courses/?limit=6');
    const courses = data.results || data;
    if (courses.length) {
      coursesTrack.innerHTML = courses.map((course, index) => C.renderCourseCard(course, index, { compact: true })).join('');
      bindCourseButtons(coursesTrack);
      bindCoursesReel();
    } else {
      showEmpty(coursesTrack, 'هنوز دوره\u200cای ثبت نشده است.');
    }
  } catch {
    showEmpty(coursesTrack, 'خطا در بارگذاری دوره\u200cها.');
  }

  try {
    const data = await apiFetch('/articles/?limit=6');
    const articles = data.results || data;
    if (articles.length) {
      articlesTrack.innerHTML = articles.map(C.renderArticleCard).join('');
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
    const data = await apiFetch('/gallery/images/?limit=12');
    const items = data.results || data;
    if (items.length) {
      if (galleryFilters) {
        const cats = [...new Map(items.filter((i) => i.category_slug).map((i) => [i.category_slug, i.category_title])).entries()];
        galleryFilters.innerHTML =
          `<button class="gallery-filter active" onclick="filterGallery(this, 'all')" aria-pressed="true">همه</button>` +
          cats.map(([slug, title]) =>
            `<button class="gallery-filter" onclick="filterGallery(this, '${slug}')" aria-pressed="false">${escapeHtml(title)}</button>`
          ).join('');
      }
      galleryMasonry.innerHTML = items.map(C.renderGalleryItem).join('');
    } else {
      showEmpty(galleryMasonry, 'هنوز تصویری در گالری ثبت نشده است.');
    }
  } catch {
    showEmpty(galleryMasonry, 'خطا در بارگذاری گالری.');
  }

  bindFadeUp(document);
  initPageScripts();
  loadSettings();
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
    const PLACEHOLDER_EMOJIS = window.SiteUtils.PLACEHOLDER_EMOJIS;
    const emoji = PLACEHOLDER_EMOJIS[course.id % PLACEHOLDER_EMOJIS.length];
    const hero = course.image
      ? `<img class="course-hero-img" src="${mediaUrl(course.image)}" alt="${escapeHtml(course.title)}">`
      : `<div class="course-hero-placeholder" aria-hidden="true">${emoji}</div>`;

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
            </div>
          </div>
          <aside class="course-sidebar">
            <div class="price-box">${formatPrice(course.price)}</div>
            <ul class="info-list">
              <li><span>ظرفیت باقی\u200cمانده</span><span>${course.remaining_capacity ?? 0} نفر</span></li>
              <li><span>تاریخ شروع</span><span>${formatDate(course.start_date)}</span></li>
              <li><span>تاریخ پایان</span><span>${formatDate(course.end_date)}</span></li>
              <li><span>گروه سنی</span><span>${escapeHtml(window.SiteUtils.AGE_LABELS[course.age_group] || course.age_group)}</span></li>
            </ul>
            <button type="button" class="btn-enroll" data-course-id="${course.id}" ${course.is_full ? 'disabled' : ''}>
              ${course.is_full ? 'ظرفیت تکمیل شده' : 'ثبت\u200cنام در دوره'}
            </button>
          </aside>
        </div>`;
      bindCourseButtons(container);
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
    const PLACEHOLDER_EMOJIS = window.SiteUtils.PLACEHOLDER_EMOJIS;
    const emoji = PLACEHOLDER_EMOJIS[article.id % PLACEHOLDER_EMOJIS.length];
    const hero = article.image
      ? `<img class="article-hero-img" src="${mediaUrl(article.image)}" alt="${escapeHtml(article.title)}">`
      : `<div class="article-hero-placeholder" aria-hidden="true">${emoji}</div>`;

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
  } else {
    await initHomePage();
  }
});
