import React from 'react';
import { LogOut, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import AuthorityBadge from '../components/AuthorityBadge';

/**
 * STEWARD Global Header Bar
 * Anchors:
 * 1. Simulation clock tick & heartbeat
 * 2. Autonomy Mode selector (autonomous, assisted, shadow, off)
 * 3. Emergency Kill Switch (◼ STOP)
 * 4. User identity & sign-out
 */
export default function Header({
  currentUser,
  autonomyMode = 'assisted',
  onAutonomyModeChange,
  killSwitchEngaged = false,
  onToggleKillSwitch,
  onSignOut,
  clockOffsetDays = 0,
}) {
  const email = currentUser?.email || 'admin@retail.com';
  const role = currentUser?.role || 'manager';
  const initials = email.slice(0, 2).toUpperCase();

  return (
    <header
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'var(--surface-0)',
        borderBottom: '1px solid var(--border)',
        padding: '0.75rem 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Simulation / Tick indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontSize: 'var(--t-meta-size)',
            color: 'var(--ink-2)',
            background: 'var(--surface-1)',
            padding: '0.25rem 0.65rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
          }}
        >
          <Clock size={14} color="var(--accent)" />
          <span className="t-mono" style={{ fontWeight: 600 }}>tick 08:00</span>
          <CheckCircle size={13} color="var(--good)" />
          {clockOffsetDays !== 0 && (
            <span style={{ color: 'var(--warn)', fontWeight: 600 }}>
              (offset: +{clockOffsetDays}d)
            </span>
          )}
        </div>
      </div>

      {/* Autonomy Mode, Kill Switch, User Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Autonomy Mode Selector */}
        {role === 'manager' && onAutonomyModeChange ? (
          <select
            value={autonomyMode}
            onChange={(e) => onAutonomyModeChange(e.target.value)}
            style={{
              fontSize: 'var(--t-meta-size)',
              fontWeight: 600,
              padding: '0.3rem 0.65rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border)',
              background: 'var(--surface-1)',
              color: 'var(--ink-1)',
              cursor: 'pointer',
            }}
          >
            <option value="autonomous">Mode: Autonomous</option>
            <option value="assisted">Mode: Assisted</option>
            <option value="shadow">Mode: Shadow</option>
            <option value="off">Mode: Off</option>
          </select>
        ) : (
          <AuthorityBadge mode={autonomyMode} />
        )}

        {/* Emergency Stop Kill Switch */}
        <button
          type="button"
          onClick={onToggleKillSwitch}
          className="btn"
          style={{
            padding: '0.3rem 0.85rem',
            fontSize: 'var(--t-meta-size)',
            fontWeight: 700,
            background: killSwitchEngaged ? 'var(--critical)' : 'var(--surface-0)',
            color: killSwitchEngaged ? '#ffffff' : 'var(--critical)',
            border: `1.5px solid var(--critical)`,
            gap: '0.4rem',
            borderRadius: 'var(--radius-sm)',
          }}
          title={
            killSwitchEngaged
              ? 'Kill switch is ENGAGED. Click to disengage.'
              : 'Emergency stop: Immediately pause all autonomous executions.'
          }
        >
          <ShieldAlert size={15} />
          {killSwitchEngaged ? 'EMERGENCY STOP ENGAGED' : '◼ STOP'}
        </button>

        {/* User Profile Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem 0.65rem',
            borderRadius: 'var(--radius-full)',
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'var(--accent)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 700,
            }}
          >
            {initials}
          </div>
          <div style={{ fontSize: 'var(--t-meta-size)' }}>
            <span style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{email}</span>
            <span style={{ color: 'var(--ink-3)', marginLeft: '0.35rem', textTransform: 'capitalize' }}>
              ({role})
            </span>
          </div>
        </div>

        {/* Sign out */}
        {onSignOut && (
          <button
            type="button"
            className="btn btn-outline"
            style={{ padding: '0.3rem 0.55rem' }}
            onClick={onSignOut}
            title="Sign out"
          >
            <LogOut size={15} />
          </button>
        )}
      </div>
    </header>
  );
}
