const U = () => window.SiteUtils;

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
  const categories = window.__categories || [];
  const courseLinks = categories.map((cat) => {
    const cls = activeSlug === cat.slug ? ' class="active"' : '';
    return `<a href="/courses/${cat.slug}/"${cls}>${U().escapeHtml(cat.title)}</a>`;
  }).join('');

  const homePrefix = activeSlug !== null && activeSlug !== undefined ? '/' : '';
  return `
    <a href="/courses/"${activeSlug === '' ? ' class="active"' : ''}>همه دوره\u200cها</a>
    ${courseLinks}
    <a href="${homePrefix}#associations">انجمن\u200cها</a>
    <a href="${homePrefix}#articles">مقالات</a>
    <a href="${homePrefix}#gallery">گالری</a>`;
}

function initLayout(activeSlug) {
  document.querySelectorAll('[data-site-nav]').forEach((el) => {
    el.innerHTML = renderNavLinks(activeSlug);
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

function renderCourseCard(course, index, options = {}) {
  const { PLACEHOLDER_EMOJIS, BADGE_CLASSES, LEVEL_LABELS, AGE_LABELS, formatPrice, mediaUrl, escapeHtml } = U();
  const { compact = false } = options;
  const emoji = PLACEHOLDER_EMOJIS[index % PLACEHOLDER_EMOJIS.length];
  const detailUrl = `/course/${encodeURIComponent(course.slug)}/`;
  const thumbInner = course.image
    ? `<img class="course-thumb" src="${mediaUrl(course.image)}" alt="${escapeHtml(course.title)}" loading="lazy">`
    : `<div class="course-thumb-placeholder" aria-hidden="true">${emoji}</div>`;

  const level = LEVEL_LABELS[course.level] || course.level;
  const categoryTitle = course.category?.title || '';
  const remaining = course.remaining_capacity ?? 0;
  const disabled = course.is_full ? 'disabled' : '';
  const enrollBtn = `<button type="button" class="btn-course" data-course-id="${course.id}" ${disabled}>
    ${course.is_full ? 'ظرفیت تکمیل' : 'ثبت\u200cنام'}
  </button>`;

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
  const { PLACEHOLDER_EMOJIS, formatDate, mediaUrl, escapeHtml } = U();
  const emoji = PLACEHOLDER_EMOJIS[(index + 2) % PLACEHOLDER_EMOJIS.length];
  const detailUrl = `/articles/${encodeURIComponent(article.slug)}/`;
  const thumb = article.image
    ? `<img class="article-thumb" src="${mediaUrl(article.image)}" alt="${escapeHtml(article.title)}" loading="lazy">`
    : `<div class="article-thumb article-thumb-placeholder" aria-hidden="true">${emoji}</div>`;

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
  U().bindFadeUp(container);
}

function renderAssociationCard(item, index) {
  const { PLACEHOLDER_EMOJIS, mediaUrl, escapeHtml } = U();
  const emoji = PLACEHOLDER_EMOJIS[(index + 1) % PLACEHOLDER_EMOJIS.length];
  const cardClass = `assoc-card-${(index % 5) + 1}`;
  const image = item.image
    ? `<img class="assoc-img" src="${mediaUrl(item.image)}" alt="${escapeHtml(item.title)}" loading="lazy">`
    : `<span class="assoc-icon" aria-hidden="true">${emoji}</span>`;

  return `
    <div class="assoc-card ${cardClass} fade-up" role="listitem">
      ${image}
      <div class="assoc-title">${escapeHtml(item.title)}</div>
      <div class="assoc-desc">${escapeHtml(item.description)}</div>
    </div>`;
}

function renderGalleryItem(image, index) {
  const { PLACEHOLDER_EMOJIS, mediaUrl, escapeHtml } = U();
  const emoji = PLACEHOLDER_EMOJIS[index % PLACEHOLDER_EMOJIS.length];
  const src = image.image ? mediaUrl(image.image) : '';
  const inner = src
    ? `<img src="${src}" alt="${escapeHtml(image.title || 'گالری')}" loading="lazy" style="width:100%;height:100%;object-fit:cover;">`
    : emoji;

  return `
    <div class="gallery-item fade-up" data-cat="${escapeHtml(image.category_slug || 'all')}" role="listitem"
         onclick='openLightbox(${JSON.stringify(src || emoji)}, ${JSON.stringify(image.title || "گالری")})' tabindex="0">
      <div class="gallery-item-inner">${inner}</div>
      <div class="gallery-overlay" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg></div>
    </div>`;
}

function renderCoursesGrid(courses, container, options = {}) {
  if (!container) return;
  if (!courses.length) {
    U().showEmpty(container, options.emptyMessage || 'هنوز دوره\u200cای در این دسته ثبت نشده است.');
    return;
  }
  container.innerHTML = courses.map((course, index) => renderCourseCard(course, index, options)).join('');
  U().bindCourseButtons(container);
  U().bindFadeUp(container);
}

window.SiteComponents = {
  initLayout, applySiteLogo, renderCoursesGrid, renderCourseCard,
  renderArticleCard, renderArticlesGrid, renderAssociationCard, renderGalleryItem,
};
