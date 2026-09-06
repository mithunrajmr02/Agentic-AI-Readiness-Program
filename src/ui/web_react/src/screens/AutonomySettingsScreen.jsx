import React, { useState } from 'react';
import { Card, AuthorityBadge } from '../components';
import { Sliders, ShieldCheck, ShieldAlert, CheckCircle2, Lock } from 'lucide-react';

/**
 * STEWARD Autonomy Policies & Blast Radius Settings (/settings/autonomy)
 * Category-level autonomy dials, financial thresholds, and fail-safe bounds.
 */
export default function AutonomySettingsScreen() {
  const [globalMode, setGlobalMode] = useState('assisted');
  const [thresholds, setThresholds] = useState({
    maxAutoPOAmount: 50000,
    dailyVelocityCap: 500,
    minDataPointsRequired: 5,
  });
  const [categoryOverrides, setCategoryOverrides] = useState({
    grocery: 'autonomous',
    electronics: 'assisted',
    clothing: 'assisted',
    household: 'autonomous',
    personal_care: 'assisted',
  });
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="autonomy-settings-screen" style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div>
        <h1 className="t-hero" style={{ margin: 0 }}>Autonomy Policies & Guardrails</h1>
        <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
          Configure operational authority, approval thresholds, and automated action boundaries (Manual §10).
        </p>
      </div>

      {saved && (
        <div
          style={{
            padding: '1rem 1.25rem',
            background: 'var(--good-light)',
            color: 'var(--good)',
            border: '1px solid var(--good-border)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={18} />
          Autonomy policies updated and published across all autonomous replenishment nodes.
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Global Autonomy Mode */}
        <Card title="Global Default Operating Authority">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            {[
              { id: 'autonomous', label: 'Autonomous', desc: 'Auto-executes within policy bounds' },
              { id: 'assisted', label: 'Assisted', desc: 'Recommends orders; requires approval' },
              { id: 'shadow', label: 'Shadow Mode', desc: 'Logs counterfactual decisions only' },
              { id: 'off', label: 'Off / Manual', desc: 'All agent triggers disabled' },
            ].map((mode) => (
              <div
                key={mode.id}
                onClick={() => setGlobalMode(mode.id)}
                style={{
                  background: globalMode === mode.id ? 'var(--accent-light)' : 'var(--surface-1)',
                  border: globalMode === mode.id ? '2px solid var(--accent)' : '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '1rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--ink-1)', fontSize: '13px' }}>{mode.label}</span>
                  {globalMode === mode.id && <CheckCircle2 size={15} color="var(--accent)" />}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--ink-3)' }}>{mode.desc}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Financial Blast Radius Caps */}
        <Card title="Financial Blast Radius Caps">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Max Autonomous PO Amount (₹)</label>
              <input
                type="number"
                value={thresholds.maxAutoPOAmount}
                onChange={(e) => setThresholds({ ...thresholds, maxAutoPOAmount: parseInt(e.target.value) || 0 })}
                className="form-control"
              />
              <span style={{ fontSize: '11px', color: 'var(--ink-3)', marginTop: '0.35rem', display: 'block' }}>
                Orders exceeding this ceiling escalate to Store Manager approval queue (Manual §10).
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">Data Sufficiency History Floor (Sales)</label>
              <input
                type="number"
                value={thresholds.minDataPointsRequired}
                onChange={(e) => setThresholds({ ...thresholds, minDataPointsRequired: parseInt(e.target.value) || 0 })}
                className="form-control"
              />
              <span style={{ fontSize: '11px', color: 'var(--ink-3)', marginTop: '0.35rem', display: 'block' }}>
                SKUs with fewer historical sales trigger policy refusal (Manual §3).
              </span>
            </div>
          </div>
        </Card>

        {/* Category Specific Overrides */}
        <Card title="Category Level Authority Dials">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(categoryOverrides).map(([cat, mode]) => (
              <div
                key={cat}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem 1rem',
                  background: 'var(--surface-1)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <span style={{ fontWeight: 600, textTransform: 'capitalize', color: 'var(--ink-1)' }}>{cat}</span>
                <select
                  value={mode}
                  onChange={(e) => setCategoryOverrides({ ...categoryOverrides, [cat]: e.target.value })}
                  className="form-control"
                  style={{ width: '160px', padding: '0.35rem 0.65rem', fontSize: 'var(--t-meta-size)' }}
                >
                  <option value="autonomous">Autonomous</option>
                  <option value="assisted">Assisted</option>
                  <option value="shadow">Shadow</option>
                  <option value="off">Off</option>
                </select>
              </div>
            ))}
          </div>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '0.65rem 1.75rem', fontWeight: 700 }}>
            Save & Enforce Policies
          </button>
        </div>
      </form>
    </div>
  );
}
