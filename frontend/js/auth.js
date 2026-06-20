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
  let datePickerLoaded = false;
  let verifying = false;
  let sendingOtp = false;
  let autoSendDone = false;

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
            <label class="auth-label" for="auth-birth-date">تاریخ تولد (شمسی) *</label>
            <input class="auth-input ltr" type="text" id="auth-birth-date" placeholder="مثال: 1385/03/15" readonly>
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
      loadDatePicker();
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
    if (sendingOtp) return;

    mobile = v;
    sessionStorage.setItem('auth_mobile', mobile);
    const btn = $('#auth-send-btn');
    sendingOtp = true;
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
        saveSession(data);
        stopTimers();
        close();
        toast(`خوش آمدید ${data.user.first_name}!`, 'success');
        setTimeout(() => { window.location.href = '/dashboard/'; }, 600);
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
    const birthDate = resolveGregorianBirthDate(birthInput);
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
        toast('تاریخ تولد نامعتبر است. از تقویم انتخاب کنید یا فرمت ۱۳۸۵/۰۳/۱۵ را وارد کنید', 'error');
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
      saveSession(data);
      sessionStorage.removeItem('auth_mobile');
      close();
      toast('ثبت‌نام با موفقیت انجام شد', 'success');
      setTimeout(() => { window.location.href = '/dashboard/'; }, 600);
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

  async function loadDatePicker() {
    if (datePickerLoaded) return;
    try {
      loadStylesheet('https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/css/persian-datepicker.min.css');
      await loadScript('https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js');
      await loadScript('https://cdn.jsdelivr.net/npm/persian-date@1.1.0/dist/persian-date.min.js');
      await loadScript('https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/js/persian-datepicker.min.js');
      const $inp = window.jQuery('#auth-birth-date');
      const syncGregorian = (unix) => {
        try {
          const pd = new window.persianDate(unix);
          const greg = pd.toCalendar('gregorian').format('YYYY-MM-DD');
          const inp = document.getElementById('auth-birth-date');
          if (inp) {
            inp.dataset.gregorian = greg;
            showFieldErr('auth-birth-date-err', false);
          }
        } catch {
          /* onSelect may fail; submit will parse display value */
        }
      };
      $inp.persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValue: false,
        persianDigit: true,
        observer: true,
        calendar: { persian: { locale: 'fa' } },
        onSelect: syncGregorian,
      });
      $inp.on('change', () => {
        const state = $inp.data('datepicker')?.getState?.();
        if (state?.selected?.unix) syncGregorian(state.selected.unix);
        else resolveGregorianBirthDate(document.getElementById('auth-birth-date'));
      });
      datePickerLoaded = true;
    } catch {
      const inp = $('#auth-birth-date');
      if (inp) {
        inp.removeAttribute('readonly');
        inp.placeholder = 'مثال: 1385/03/15';
        inp.addEventListener('change', () => { resolveGregorianBirthDate(inp); });
        inp.addEventListener('blur', () => { resolveGregorianBirthDate(inp); });
      }
    }
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
        btn.textContent = formatUserLabel(user);
        btn.setAttribute('aria-label', 'پنل کاربری');
      } else {
        btn.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" stroke="white" fill="none" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> ورود / ثبت‌نام`;
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
