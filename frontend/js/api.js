/**
 * Base URL for backend API — same origin when served by Django.
 */
const API_BASE_URL = '/api';

async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
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
