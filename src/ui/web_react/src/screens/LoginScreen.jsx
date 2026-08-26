import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE, describeApiError } from '../lib/api';

/**
 * 07-UX-ARCHITECTURE.md Decomposed LoginScreen
 */
export default function LoginScreen({ onAuthenticated }) {
  const [email, setEmail] = useState('admin@retail.com');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = new URLSearchParams({ username: email, password });
      const res = await axios.post(`${API_BASE}/auth/login`, body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      onAuthenticated(res.data.access_token, email);
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Incorrect email or password.'
          : `Could not reach the API: ${describeApiError(err)}`
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--surface-1)',
      padding: '1rem',
    }}>
      <form onSubmit={submit} style={{
        background: 'var(--surface-0)',
        padding: '2.5rem',
        borderRadius: 'var(--radius-lg)',
        width: '100%',
        maxWidth: '400px',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-overlay)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1rem',
          }}>
            ST
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--ink-1)' }}>Steward</div>
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Autonomous Replenishment Control Tower</div>
          </div>
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            required
            autoComplete="username"
            onChange={(e) => setEmail(e.target.value)}
            className="form-control"
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            required
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
            className="form-control"
          />
        </div>

        {error && (
          <div style={{
            background: 'rgba(196, 38, 46, 0.1)',
            color: 'var(--critical)',
            border: '1px solid rgba(196, 38, 46, 0.3)',
            padding: '0.7rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--t-meta-size)',
            marginBottom: '1rem',
            whiteSpace: 'pre-line',
          }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={busy}
          style={{ width: '100%', marginTop: '0.5rem' }}
        >
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
