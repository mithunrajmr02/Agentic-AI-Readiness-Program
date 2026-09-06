import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE, describeApiError } from '../lib/api';

/**
 * STEWARD Enterprise Sign-In Screen
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
          : `Could not connect to authentication service: ${describeApiError(err)}`
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--surface-1)',
        padding: '1.5rem',
      }}
    >
      <form
        onSubmit={submit}
        style={{
          background: 'var(--surface-0)',
          padding: '2.75rem',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '420px',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-overlay)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.75rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.1rem',
              letterSpacing: '-0.03em',
              boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
            }}
          >
            ST
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--ink-1)', letterSpacing: '-0.02em' }}>
              STEWARD
            </div>
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', fontWeight: 500 }}>
              Autonomous Replenishment Control Tower
            </div>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Email Address</label>
          <input
            type="email"
            value={email}
            required
            autoComplete="username"
            onChange={(e) => setEmail(e.target.value)}
            className="form-control"
            placeholder="admin@retail.com"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            type="password"
            value={password}
            required
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
            className="form-control"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div
            style={{
              background: 'var(--critical-light)',
              color: 'var(--critical)',
              border: '1px solid var(--critical-border)',
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--t-meta-size)',
              marginBottom: '1rem',
              whiteSpace: 'pre-line',
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={busy}
          style={{ width: '100%', padding: '0.75rem', marginTop: '0.5rem', fontWeight: 700 }}
        >
          {busy ? 'Signing in…' : 'Sign in'}
        </button>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
          Enterprise Autonomous Operations & Governance
        </div>
      </form>
    </div>
  );
}
