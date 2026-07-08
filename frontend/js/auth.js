/**
 * Unified OTP auth modal — login & registration flow.
 */
const AuthModal = (() => {
  const OTP_IDS = ['auth-o1', 'auth-o2', 'auth-o3', 'auth-o4', 'auth-o5', 'auth-o6'];
  let mobile = '';
  let termsOk = false;
  let otpTimer = null;
  let resendTimer = null;
  let expiresIn = 120;
  let resendCooldown = 60;
  let otpSecondsLeft = 0;
  let resendSecondsLeft = 0;
  let birthSelectsReady = false;
  let verifying = false;
  let sendingOtp = false;
  let autoSendDone = false;

  const USER_PANEL_ICON = '<svg class="btn-user-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4zm0 2c-3.31 0-6 1.79-6 4v1h12v-1c0-2.21-2.69-4-6-4z"/></svg>';
  const LOGIN_ICON = '<svg class="btn-login-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4zm0 2c-3.31 0-6 1.79-6 4v1h12v-1c0-2.21-2.69-4-6-4z"/></svg>';

  function $(sel, root = document) { return root.querySelector(sel); }
  function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }

  function toEn(s) {
    const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
    const arabicDigits = '٠١٢٣٤٥٦٧٨٩';
    let out = String(s)
      .replace(/[۰-۹]/g, (d) => String(persianDigits.indexOf(d)))
      .replace(/[٠-٩]/g, (d) => String(arabicDigits.indexOf(d)));
    out = out.replace(/[０-９]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0xFEE0));
    return out;
  }

  function digitsOnly(s, maxLen) {
    const v = toEn(s).replace(/\D/g, '');
    return maxLen ? v.slice(0, maxLen) : v;
  }

  function toast(msg, type = 'info') {
    let wrap = $('.auth-toast-wrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.className = 'auth-toast-wrap';
      wrap.setAttribute('aria-live', 'polite');
      document.body.appendChild(wrap);
    }
    const el = document.createElement('div');
    el.className = `auth-toast ${type}`;
    el.textContent = msg;
    wrap.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  function saveSession(data) {
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    clearAdminSession();
    window.dispatchEvent(new CustomEvent('auth:login', { detail: data.user }));
  }

  async function finishAuthFlow(data, welcomeMessage) {
    saveSession(data);
    sessionStorage.removeItem('auth_mobile');
    stopTimers();
    close();

    const pendingId = window.SiteUtils?.getPendingEnrollment?.();
    if (pendingId) {
      if (welcomeMessage) toast(welcomeMessage, 'success');
      await window.SiteUtils.startCoursePayment(pendingId, null);
      return;
    }

    if (welcomeMessage) toast(welcomeMessage, 'success');
    setTimeout(() => { window.location.href = '/dashboard/'; }, 600);
  }

  function clearAdminSession() {
    fetch('/api/auth/clear-admin-session/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
    }).catch(() => {});
  }

  function mountModal() {
    if ($('#auth-modal-overlay')) return;

    document.body.insertAdjacentHTML('beforeend', `
<div class="auth-modal-overlay" id="auth-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
  <div class="auth-modal">
    <div class="auth-modal-bar"></div>
    <div class="auth-modal-head">
      <div class="auth-modal-title" id="auth-modal-title">ورود / ثبت‌نام</div>
      <button type="button" class="auth-modal-close" id="auth-modal-close" aria-label="بستن">
        <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div class="auth-modal-body">

      <div class="auth-step active" id="auth-step-phone" data-step="phone">
        <div class="auth-lead">
          <h2>خوش آمدید</h2>
          <p>شماره موبایل خود را وارد کنید تا کد تأیید ارسال شود</p>
        </div>
        <div class="auth-field">
          <label class="auth-label" for="auth-phone">شماره موبایل</label>
          <input class="auth-input ltr" type="tel" id="auth-phone" maxlength="11" inputmode="numeric" lang="en" placeholder="09121234567" autocomplete="tel">
          <div class="auth-error" id="auth-phone-err">شماره موبایل معتبر نیست</div>
          <div class="auth-hint">کد ۶ رقمی OTP پیامک می‌شود</div>
        </div>
        <div class="auth-terms" id="auth-terms-row" role="checkbox" aria-checked="false" tabindex="0">
          <div class="auth-check" id="auth-terms-check"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg></div>
          <span>با ورود، قوانین و مقررات پژوهش‌سرا را می‌پذیرم.</span>
        </div>
        <button type="button" class="auth-btn" id="auth-send-btn" disabled>ارسال کد تأیید</button>
      </div>

      <div class="auth-step" id="auth-step-otp" data-step="otp">
        <div class="auth-lead">
          <h2>کد تأیید</h2>
          <p>کد ۶ رقمی ارسال‌شده را وارد کنید</p>
          <div class="auth-phone-tag" id="auth-phone-show"></div>
          <button type="button" class="auth-resend" id="auth-edit-phone" style="display:block;margin:0.25rem auto 0">تغییر شماره</button>
        </div>
        <div class="auth-otp-boxes" dir="ltr">
          ${OTP_IDS.map((id, i) => `<input class="auth-otp-inp" id="${id}" type="text" inputmode="numeric" maxlength="1" aria-label="رقم ${i + 1}">`).join('')}
        </div>
        <div class="auth-error show" id="auth-otp-err" style="text-align:center;display:none"></div>
        <div class="auth-timer-row">
          <span id="auth-otp-timer">اعتبار: 2:00</span>
          <button type="button" class="auth-resend" id="auth-resend-btn" disabled>ارسال مجدد</button>
        </div>
        <button type="button" class="auth-btn" id="auth-verify-btn" disabled>تأیید و ادامه</button>
      </div>

      <div class="auth-step" id="auth-step-profile" data-step="profile">
        <div class="auth-lead">
          <h2>تکمیل اطلاعات</h2>
          <p>برای تکمیل ثبت‌نام، فرم زیر را پر کنید</p>
        </div>
        <form id="auth-profile-form" novalidate>
          <div class="auth-row">
            <div class="auth-field">
              <label class="auth-label" for="auth-first-name">نام *</label>
              <input class="auth-input" type="text" id="auth-first-name" autocomplete="given-name">
              <div class="auth-error" id="auth-first-name-err">نام را وارد کنید</div>
            </div>
            <div class="auth-field">
              <label class="auth-label" for="auth-last-name">نام خانوادگی *</label>
              <input class="auth-input" type="text" id="auth-last-name" autocomplete="family-name">
              <div class="auth-error" id="auth-last-name-err">نام خانوادگی را وارد کنید</div>
            </div>
          </div>
          <div class="auth-field">
            <label class="auth-label" for="auth-father-name">نام پدر *</label>
            <input class="auth-input" type="text" id="auth-father-name">
            <div class="auth-error" id="auth-father-name-err">نام پدر را وارد کنید</div>
          </div>
          <div class="auth-field">
            <label class="auth-label" for="auth-national-code">کد ملی *</label>
            <input class="auth-input ltr" type="text" id="auth-national-code" maxlength="14" inputmode="numeric" lang="en" dir="ltr" autocomplete="off" autocorrect="off" spellcheck="false">
            <div class="auth-error" id="auth-national-code-err">کد ملی باید ۱۰ رقم معتبر باشد</div>
            <div class="auth-hint">با کیبورد فارسی یا انگلیسی قابل ورود است</div>
          </div>
          <div class="auth-field">
            <label class="auth-label" id="auth-birth-label">تاریخ تولد (شمسی) *</label>
            <div class="auth-birth-row" role="group" aria-labelledby="auth-birth-label">
              <select class="auth-input auth-birth-select" id="auth-birth-year" aria-label="سال">
                <option value="">سال</option>
              </select>
              <select class="auth-input auth-birth-select" id="auth-birth-month" aria-label="ماه" disabled>
                <option value="">ماه</option>
              </select>
              <select class="auth-input auth-birth-select" id="auth-birth-day" aria-label="روز" disabled>
                <option value="">روز</option>
              </select>
            </div>
            <input type="hidden" id="auth-birth-date">
            <div class="auth-error" id="auth-birth-date-err">تاریخ تولد را انتخاب کنید</div>
          </div>
          <button type="submit" class="auth-btn" id="auth-register-btn">ثبت‌نام و ورود</button>
        </form>
      </div>

    </div>
  </div>
</div>`);

    bindEvents();
  }

  function bindEvents() {
    $('#auth-modal-close')?.addEventListener('click', close);
    $('#auth-modal-overlay')?.addEventListener('click', (e) => {
      if (e.target.id === 'auth-modal-overlay') close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && $('#auth-modal-overlay')?.classList.contains('open')) close();
    });

    bindDigitField('#auth-phone', onPhoneInput);
    $('#auth-phone')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (!$('#auth-send-btn')?.disabled) sendOtp();
      }
    });
    $('#auth-terms-row')?.addEventListener('click', toggleTerms);
    $('#auth-terms-row')?.addEventListener('keydown', (e) => {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggleTerms(); }
    });
    $('#auth-send-btn')?.addEventListener('click', sendOtp);
    $('#auth-verify-btn')?.addEventListener('click', verifyOtp);
    $('#auth-resend-btn')?.addEventListener('click', resendOtp);
    $('#auth-edit-phone')?.addEventListener('click', () => goStep('phone'));
    $('#auth-profile-form')?.addEventListener('submit', completeRegistration);
    bindDigitField('#auth-national-code', onNationalCodeInput);

    OTP_IDS.forEach((id, idx) => {
      const inp = document.getElementById(id);
      inp?.addEventListener('input', () => onOtpInput(inp, idx));
      inp?.addEventListener('keydown', (e) => onOtpKey(e, inp, idx));
      inp?.addEventListener('paste', onOtpPaste);
    });

    $$('[data-auth-open]').forEach((el) => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        if (localStorage.getItem('access_token')) {
          window.location.href = '/dashboard/';
          return;
        }
        open();
      });
    });

    if (new URLSearchParams(window.location.search).get('auth') === '1') {
      setTimeout(open, 300);
      history.replaceState({}, '', window.location.pathname);
    }
  }

  function open() {
    mountModal();
    resetState();
    goStep('phone');
    $('#auth-modal-overlay')?.classList.add('open');
    setTimeout(() => $('#auth-phone')?.focus(), 200);
  }

  function close() {
    stopTimers();
    $('#auth-modal-overlay')?.classList.remove('open');
  }

  function resetState() {
    mobile = '';
    termsOk = false;
    sendingOtp = false;
    autoSendDone = false;
    $('#auth-phone').value = '';
    $('#auth-phone')?.classList.remove('error');
    $('#auth-phone-err')?.classList.remove('show');
    $('#auth-terms-check')?.classList.remove('on');
    $('#auth-terms-row')?.setAttribute('aria-checked', 'false');
    updateSendBtn();
    clearOtpInputs();
    hideErr('auth-otp-err');
    $$('.auth-error').forEach((el) => el.classList.remove('show'));
  }

  function goStep(step) {
    $$('.auth-step').forEach((el) => el.classList.toggle('active', el.dataset.step === step));
    if (step === 'otp') {
      setTimeout(() => document.getElementById(OTP_IDS[0])?.focus(), 150);
    }
    if (step === 'phone') {
      autoSendDone = false;
    }
    if (step === 'profile') {
      initBirthDateSelects();
    }
  }

  function bindDigitField(selector, handler) {
    const el = $(selector);
    if (!el) return;
    el.addEventListener('input', handler);
    el.addEventListener('compositionend', handler);
    el.addEventListener('paste', () => setTimeout(handler, 0));
    el.addEventListener('blur', handler);
  }

  function onNationalCodeInput() {
    const el = $('#auth-national-code');
    if (!el) return;
    const v = digitsOnly(el.value, 10);
    el.value = v;
    el.classList.remove('error');
    showFieldErr('auth-national-code-err', false);
  }

  function onPhoneInput() {
    const el = $('#auth-phone');
    const v = toEn(el.value).replace(/\D/g, '').slice(0, 11);
    el.value = v;
    mobile = v;
    el.classList.remove('error');
    $('#auth-phone-err')?.classList.remove('show');
    updateSendBtn();
    maybeAutoSendOtp();
  }

  function maybeAutoSendOtp() {
    const v = toEn($('#auth-phone')?.value || '').replace(/\D/g, '');
    if (autoSendDone || sendingOtp || v.length !== 11 || !v.startsWith('09') || !termsOk) return;
    autoSendDone = true;
    sendOtp();
  }

  function toggleTerms() {
    termsOk = !termsOk;
    $('#auth-terms-check')?.classList.toggle('on', termsOk);
    $('#auth-terms-row')?.setAttribute('aria-checked', String(termsOk));
    updateSendBtn();
    maybeAutoSendOtp();
  }

  function updateSendBtn() {
    const v = toEn($('#auth-phone')?.value || '').replace(/\D/g, '');
    const valid = v.length === 11 && v.startsWith('09');
    const btn = $('#auth-send-btn');
    if (btn) btn.disabled = !(valid && termsOk);
  }

  function setLoading(btn, loading, label) {
    if (!btn) return;
    btn.disabled = loading;
    if (loading) {
      btn.dataset.label = btn.textContent;
      btn.innerHTML = `<span>${label || 'لطفاً صبر کنید...'}</span><span class="auth-spin"></span>`;
    } else {
      btn.textContent = btn.dataset.label || btn.textContent;
    }
  }

  async function sendOtp() {
    if (sendingOtp) return;

    const v = toEn($('#auth-phone')?.value || '').replace(/\D/g, '');
    if (v.length !== 11 || !v.startsWith('09')) {
      autoSendDone = false;
      $('#auth-phone')?.classList.add('error');
      $('#auth-phone-err')?.classList.add('show');
      return;
    }
    if (!termsOk) {
      autoSendDone = false;
      toast('لطفاً قوانین و مقررات را بپذیرید', 'error');
      return;
    }

    sendingOtp = true;
    mobile = v;
    sessionStorage.setItem('auth_mobile', mobile);
    const btn = $('#auth-send-btn');
    setLoading(btn, true, 'در حال ارسال...');
    try {
      const data = await apiFetch('/auth/send-otp/', {
        method: 'POST',
        body: JSON.stringify({ mobile }),
      });
      expiresIn = data.expires_in || 120;
      resendCooldown = data.resend_cooldown || 60;
      otpSecondsLeft = expiresIn;
      resendSecondsLeft = resendCooldown;
      const masked = mobile.slice(0, 4) + ' *** ' + mobile.slice(-4);
      if ($('#auth-phone-show')) $('#auth-phone-show').textContent = masked;
      toast(data.message || 'کد تأیید ارسال شد', 'success');
      goStep('otp');
      startTimers();
      clearOtpInputs();
    } catch (err) {
      autoSendDone = false;
      toast(err.detail || 'خطا در ارسال کد', 'error');
      if (err.code === 'resend_cooldown' && err.cooldown) {
        resendSecondsLeft = err.cooldown;
      }
    } finally {
      sendingOtp = false;
      setLoading(btn, false);
      btn.textContent = 'ارسال کد تأیید';
      updateSendBtn();
    }
  }

  async function resendOtp() {
    const btn = $('#auth-resend-btn');
    if (btn?.disabled) return;
    try {
      const data = await apiFetch('/auth/resend-otp/', {
        method: 'POST',
        body: JSON.stringify({ mobile }),
      });
      expiresIn = data.expires_in || 120;
      resendCooldown = data.resend_cooldown || 60;
      otpSecondsLeft = expiresIn;
      resendSecondsLeft = resendCooldown;
      startTimers();
      clearOtpInputs();
      toast('کد جدید ارسال شد', 'success');
    } catch (err) {
      toast(err.detail || 'خطا در ارسال مجدد', 'error');
      if (err.cooldown) resendSecondsLeft = err.cooldown;
    }
  }

  function getOtpCode() {
    return OTP_IDS.map((id) => toEn(document.getElementById(id)?.value || '')).join('').replace(/\D/g, '');
  }

  async function verifyOtp() {
    const code = getOtpCode();
    if (code.length !== 6 || verifying) return;

    const verifyMobile = mobile || sessionStorage.getItem('auth_mobile') || '';
    if (!verifyMobile) {
      toast('شماره موبایل یافت نشد. دوباره وارد کنید.', 'error');
      goStep('phone');
      return;
    }
    mobile = verifyMobile;

    verifying = true;
    const btn = $('#auth-verify-btn');
    setLoading(btn, true, 'در حال بررسی...');
    hideErr('auth-otp-err');
    try {
      const data = await apiFetch('/auth/verify-otp/', {
        method: 'POST',
        body: JSON.stringify({ mobile, code }),
      });
      if (data.requires_registration) {
        toast('لطفاً اطلاعات خود را تکمیل کنید', 'info');
        goStep('profile');
      } else {
        await finishAuthFlow(data, `خوش آمدید ${data.user.first_name}!`);
      }
    } catch (err) {
      showOtpErr(err.detail || 'کد تأیید نادرست است');
      OTP_IDS.forEach((id) => document.getElementById(id)?.classList.add('err'));
      setTimeout(clearOtpInputs, 1200);
    } finally {
      verifying = false;
      setLoading(btn, false);
      btn.textContent = 'تأیید و ادامه';
    }
  }

  function validateNationalCode(code) {
    if (!/^\d{10}$/.test(code)) return false;
    if (new Set(code).size === 1) return false;
    const check = parseInt(code[9], 10);
    const sum = [...code.slice(0, 9)].reduce((acc, d, i) => acc + parseInt(d, 10) * (10 - i), 0);
    const rem = sum % 11;
    return rem < 2 ? check === rem : check === 11 - rem;
  }

  function nationalCodeIssue(code) {
    if (!code) return 'empty';
    if (code.length !== 10) return 'length';
    if (!validateNationalCode(code)) return 'checksum';
    return null;
  }

  const JALALI_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
  ];

  function isJalaliLeap(year) {
    const a = (year - (year > 0 ? 474 : 473)) % 2820 + 474;
    return (((a + 38) * 682) % 2816) < 682;
  }

  function jalaliMonthLength(year, month) {
    if (month >= 1 && month <= 6) return 31;
    if (month >= 7 && month <= 11) return 30;
    return isJalaliLeap(year) ? 30 : 29;
  }

  function currentJalaliYear() {
    try {
      if (window.persianDate) {
        return new window.persianDate().year();
      }
    } catch {
      /* fall through */
    }
    return new Date().getFullYear() - 621;
  }

  function fillSelectOptions(select, items, placeholder) {
    if (!select) return;
    select.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach(({ value, label }) => {
      const opt = document.createElement('option');
      opt.value = String(value);
      opt.textContent = label;
      select.appendChild(opt);
    });
  }

  function refreshBirthDayOptions() {
    const year = parseInt($('#auth-birth-year')?.value || '', 10);
    const month = parseInt($('#auth-birth-month')?.value || '', 10);
    const daySelect = $('#auth-birth-day');
    if (!daySelect) return;

    if (!year || !month) {
      daySelect.disabled = true;
      fillSelectOptions(daySelect, [], 'روز');
      return;
    }

    const currentDay = parseInt(daySelect.value || '', 10);
    const days = jalaliMonthLength(year, month);
    const items = Array.from({ length: days }, (_, i) => {
      const day = i + 1;
      return { value: day, label: String(day).replace(/\d/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[d]) };
    });
    fillSelectOptions(daySelect, items, 'روز');
    daySelect.disabled = false;
    if (currentDay && currentDay <= days) {
      daySelect.value = String(currentDay);
    }
  }

  function syncBirthDateFromSelects() {
    const hidden = $('#auth-birth-date');
    const year = parseInt($('#auth-birth-year')?.value || '', 10);
    const month = parseInt($('#auth-birth-month')?.value || '', 10);
    const day = parseInt($('#auth-birth-day')?.value || '', 10);
    if (!hidden || !year || !month || !day) {
      if (hidden) delete hidden.dataset.gregorian;
      return '';
    }

    const jalaliText = `${year}/${String(month).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
    hidden.value = jalaliText;

    if (window.persianDate) {
      try {
        const greg = new window.persianDate([year, month, day])
          .toCalendar('gregorian')
          .format('YYYY-MM-DD');
        hidden.dataset.gregorian = greg;
        showFieldErr('auth-birth-date-err', false);
        return greg;
      } catch {
        delete hidden.dataset.gregorian;
        return '';
      }
    }
    return resolveGregorianBirthDate(hidden);
  }

  function bindBirthDateSelects() {
    const yearSelect = $('#auth-birth-year');
    const monthSelect = $('#auth-birth-month');
    const daySelect = $('#auth-birth-day');
    if (!yearSelect || yearSelect.dataset.bound === '1') return;
    yearSelect.dataset.bound = '1';

    yearSelect.addEventListener('change', () => {
      const hasYear = !!yearSelect.value;
      monthSelect.disabled = !hasYear;
      if (!hasYear) {
        monthSelect.value = '';
        daySelect.value = '';
        daySelect.disabled = true;
        fillSelectOptions(daySelect, [], 'روز');
      }
      refreshBirthDayOptions();
      syncBirthDateFromSelects();
    });

    monthSelect.addEventListener('change', () => {
      refreshBirthDayOptions();
      syncBirthDateFromSelects();
    });

    daySelect.addEventListener('change', syncBirthDateFromSelects);
  }

  async function initBirthDateSelects() {
    if (birthSelectsReady) {
      syncBirthDateFromSelects();
      return;
    }

    try {
      await loadScript('https://cdn.jsdelivr.net/npm/persian-date@1.1.0/dist/persian-date.min.js');
    } catch {
      /* conversion may fail without library */
    }

    const endYear = currentJalaliYear();
    const startYear = Math.max(1320, endYear - 80);
    const years = [];
    for (let year = endYear; year >= startYear; year -= 1) {
      const label = String(year).replace(/\d/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[d]);
      years.push({ value: year, label });
    }
    fillSelectOptions($('#auth-birth-year'), years, 'سال');

    const months = JALALI_MONTHS.map((label, index) => ({
      value: index + 1,
      label,
    }));
    fillSelectOptions($('#auth-birth-month'), months, 'ماه');

    bindBirthDateSelects();
    birthSelectsReady = true;
  }

  function resolveGregorianBirthDate(birthInput) {
    if (!birthInput) return '';
    if (birthInput.dataset.gregorian) return birthInput.dataset.gregorian;

    const raw = toEn(birthInput.value || '').trim();
    if (!raw) return '';

    const jalali = raw.match(/^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$/);
    if (jalali && window.persianDate) {
      try {
        const greg = new window.persianDate([
          parseInt(jalali[1], 10),
          parseInt(jalali[2], 10),
          parseInt(jalali[3], 10),
        ]).toCalendar('gregorian').format('YYYY-MM-DD');
        birthInput.dataset.gregorian = greg;
        return greg;
      } catch {
        /* fall through */
      }
    }

    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
      birthInput.dataset.gregorian = raw;
      return raw;
    }
    return '';
  }

  function showFieldErr(id, show) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('show', show);
  }

  async function completeRegistration(e) {
    e.preventDefault();
    const firstName = $('#auth-first-name')?.value.trim();
    const lastName = $('#auth-last-name')?.value.trim();
    const fatherName = $('#auth-father-name')?.value.trim();
    const nationalCode = digitsOnly($('#auth-national-code')?.value || '', 10);
    const birthInput = $('#auth-birth-date');
    const birthDate = syncBirthDateFromSelects() || resolveGregorianBirthDate(birthInput);
    const regMobile = mobile || sessionStorage.getItem('auth_mobile') || '';

    const ncIssue = nationalCodeIssue(nationalCode);
    const ncErrEl = $('#auth-national-code-err');

    showFieldErr('auth-first-name-err', !firstName);
    showFieldErr('auth-last-name-err', !lastName);
    showFieldErr('auth-father-name-err', !fatherName);
    if (ncErrEl) {
      if (ncIssue === 'length') {
        ncErrEl.textContent = 'کد ملی باید دقیقاً ۱۰ رقم باشد';
      } else if (ncIssue === 'checksum') {
        ncErrEl.textContent = 'کد ملی نامعتبر است. رقم‌ها را دوباره بررسی کنید';
      } else if (ncIssue === 'empty') {
        ncErrEl.textContent = 'کد ملی را وارد کنید';
      }
    }
    showFieldErr('auth-national-code-err', !!ncIssue);
    showFieldErr('auth-birth-date-err', !birthDate);

    if (!firstName || !lastName || !fatherName || ncIssue || !birthDate) {
      if (!birthDate && birthInput?.value?.trim()) {
        toast('تاریخ تولد نامعتبر است. سال، ماه و روز را کامل انتخاب کنید', 'error');
      } else {
        toast('لطفاً همه فیلدهای الزامی را تکمیل کنید', 'error');
      }
      return;
    }

    if (!regMobile) {
      toast('شماره موبایل یافت نشد. لطفاً دوباره کد تأیید را وارد کنید.', 'error');
      goStep('phone');
      return;
    }
    mobile = regMobile;

    const btn = $('#auth-register-btn');
    setLoading(btn, true, 'در حال ثبت‌نام...');
    try {
      const data = await apiFetch('/auth/complete-registration/', {
        method: 'POST',
        body: JSON.stringify({
          mobile: regMobile,
          first_name: firstName,
          last_name: lastName,
          father_name: fatherName,
          national_code: nationalCode,
          birth_date: birthDate,
        }),
      });
      await finishAuthFlow(data, 'ثبت\u200cنام با موفقیت انجام شد');
    } catch (err) {
      const fieldMsg = err.national_code?.[0] || err.birth_date?.[0] || err.mobile?.[0];
      if (err.national_code) showFieldErr('auth-national-code-err', true);
      if (err.birth_date) showFieldErr('auth-birth-date-err', true);
      toast(fieldMsg || err.detail || 'خطا در ثبت‌نام', 'error');
    } finally {
      setLoading(btn, false);
      btn.textContent = 'ثبت‌نام و ورود';
    }
  }

  function onOtpInput(el, idx) {
    let v = toEn(el.value).replace(/\D/g, '');
    if (v.length > 1) v = v.slice(-1);
    el.value = v;
    el.classList.remove('err');
    el.classList.toggle('filled', !!v);
    if (v && idx < OTP_IDS.length - 1) document.getElementById(OTP_IDS[idx + 1])?.focus();
    const full = getOtpCode().length === 6;
    if ($('#auth-verify-btn')) $('#auth-verify-btn').disabled = !full;
  }

  function onOtpKey(e, el, idx) {
    if (e.key === 'Backspace' && !el.value && idx > 0) {
      const prev = document.getElementById(OTP_IDS[idx - 1]);
      if (prev) { prev.value = ''; prev.classList.remove('filled'); prev.focus(); }
    }
  }

  function onOtpPaste(e) {
    e.preventDefault();
    const text = toEn((e.clipboardData || window.clipboardData).getData('text')).replace(/\D/g, '').slice(0, 6);
    OTP_IDS.forEach((id, i) => {
      const inp = document.getElementById(id);
      if (!inp) return;
      inp.value = text[i] || '';
      inp.classList.toggle('filled', !!text[i]);
    });
    if ($('#auth-verify-btn')) $('#auth-verify-btn').disabled = text.length !== 6;
  }

  function clearOtpInputs() {
    OTP_IDS.forEach((id) => {
      const inp = document.getElementById(id);
      if (inp) { inp.value = ''; inp.className = 'auth-otp-inp'; }
    });
    if ($('#auth-verify-btn')) $('#auth-verify-btn').disabled = true;
  }

  function showOtpErr(msg) {
    const el = $('#auth-otp-err');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
  }

  function hideErr(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  }

  function startTimers() {
    stopTimers();
    renderTimers();
    otpTimer = setInterval(() => {
      otpSecondsLeft = Math.max(0, otpSecondsLeft - 1);
      renderTimers();
      if (otpSecondsLeft <= 0) stopTimers();
    }, 1000);
    resendTimer = setInterval(() => {
      resendSecondsLeft = Math.max(0, resendSecondsLeft - 1);
      renderTimers();
    }, 1000);
  }

  function stopTimers() {
    if (otpTimer) clearInterval(otpTimer);
    if (resendTimer) clearInterval(resendTimer);
    otpTimer = null;
    resendTimer = null;
  }

  function renderTimers() {
    const om = Math.floor(otpSecondsLeft / 60);
    const os = otpSecondsLeft % 60;
    const t = $('#auth-otp-timer');
    if (t) t.textContent = `اعتبار: ${om}:${String(os).padStart(2, '0')}`;
    const rb = $('#auth-resend-btn');
    if (rb) {
      rb.disabled = resendSecondsLeft > 0;
      rb.textContent = resendSecondsLeft > 0 ? `ارسال مجدد (${resendSecondsLeft})` : 'ارسال مجدد';
    }
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function loadStylesheet(href) {
    if (document.querySelector(`link[href="${href}"]`)) return;
    const l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = href;
    document.head.appendChild(l);
  }

  function formatUserLabel(user) {
    const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim();
    return name || 'پنل من';
  }

  async function refreshUserSession() {
    if (!localStorage.getItem('access_token')) return;
    try {
      const profile = await apiFetch('/dashboard/profile/');
      localStorage.setItem('user', JSON.stringify(profile));
      if (!profile.is_staff) clearAdminSession();
      updateHeaderAuthState();
    } catch {
      /* keep cached user if profile fetch fails */
    }
  }

  function updateHeaderAuthState() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const actions = document.querySelector('[data-header-actions]');

    document.querySelectorAll('[data-auth-open]').forEach((btn) => {
      if (user) {
        const label = formatUserLabel(user);
        btn.innerHTML = `${USER_PANEL_ICON}<span class="btn-primary-text btn-user-name">${label}</span>`;
        btn.classList.add('is-user-panel');
        btn.setAttribute('aria-label', `پنل کاربری ${label}`);
      } else {
        btn.innerHTML = `${LOGIN_ICON}<span class="btn-primary-text">ورود / ثبت‌نام</span>`;
        btn.classList.remove('is-user-panel');
        btn.setAttribute('aria-label', 'ورود یا ثبت‌نام');
      }
    });

    let adminBtn = document.querySelector('[data-admin-panel]');
    if (user?.is_staff) {
      if (!adminBtn && actions) {
        adminBtn = document.createElement('a');
        adminBtn.href = '/site-management/';
        adminBtn.className = 'btn-secondary';
        adminBtn.setAttribute('data-admin-panel', '');
        adminBtn.textContent = 'مدیریت وبسایت';
        adminBtn.setAttribute('aria-label', 'ورود به مدیریت وبسایت');
        actions.insertBefore(adminBtn, actions.querySelector('[data-auth-open]'));
      }
    } else if (adminBtn) {
      adminBtn.remove();
    }
  }

  function init() {
    mountModal();
    window.addEventListener('auth:login', updateHeaderAuthState);
    window.addEventListener('auth:logout', updateHeaderAuthState);
    updateHeaderAuthState();
    refreshUserSession();
  }

  return { init, open, close, toast, updateHeaderAuthState, refreshUserSession };
})();

document.addEventListener('DOMContentLoaded', () => AuthModal.init());
window.AuthModal = AuthModal;
