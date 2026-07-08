/**
 * Base URL for backend API — same origin when served by Django.
 */
const API_BASE_URL = '/api';

async function _doFetch(endpoint, options, headers) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        credentials: options.credentials ?? 'same-origin',
        headers,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw { status: response.status, ...data };
    }
    return data;
}

async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
        return await _doFetch(endpoint, options, headers);
    } catch (err) {
        if (err.status !== 401 || !token) throw err;

        // Access token expired — try to refresh
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            try {
                const rr = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh: refreshToken }),
                });
                if (rr.ok) {
                    const { access } = await rr.json();
                    localStorage.setItem('access_token', access);
                    headers['Authorization'] = `Bearer ${access}`;
                    return await _doFetch(endpoint, options, headers);
                }
            } catch {
                /* refresh network error — fall through to clear tokens */
            }
        }

        // Refresh failed or no refresh token — clear session and retry without auth
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.dispatchEvent(new CustomEvent('auth:logout'));
        delete headers['Authorization'];
        return await _doFetch(endpoint, options, headers);
    }
}
