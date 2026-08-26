import React from 'react';
import { Card, AuthorityBadge } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.9 Autonomy Policies Settings (/settings/autonomy)
 * Category mode dials, blast radius caps, read-only policy thresholds citing manual §10.
 */
export default function AutonomySettingsScreen() {
  return (
    <div className="autonomy-settings-screen">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 className="t-display" style={{ margin: 0 }}>Autonomy Policies</h1>
        <p className="t-meta" style={{ marginTop: '0.25rem' }}>
          Configure autonomy modes, spend caps, and blast-radius controls per category.
        </p>
      </div>

      {/* READ-ONLY POLICY CITATION NOTICE */}
      <div style={{
        background: 'var(--surface-0)',
        border: '1px solid var(--border)',
        borderLeft: '4px solid var(--accent)',
        borderRadius: 'var(--radius-md)',
        padding: '1rem 1.25rem',
        marginBottom: '1.5rem',
      }}>
        <div style={{ fontWeight: 700, color: 'var(--ink-1)', marginBottom: '0.25rem' }}>
          Policy Rule §10 (Governed by Operating Manual)
        </div>
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', margin: 0, fontStyle: 'italic' }}>
          "Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission."
        </p>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.5rem' }}>
          ⓘ Read-only in software. To change this threshold, update §10 of your Operations Manual.
        </div>
      </div>

      {/* CATEGORY DIALS */}
      <Card title="Category Autonomy Modes" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            { cat: 'Grocery', mode: 'assisted', limit: '₹50,000', blast: 5 },
            { cat: 'Electronics', mode: 'assisted', limit: '₹50,000', blast: 2 },
            { cat: 'Clothing', mode: 'shadow', limit: '₹50,000', blast: 10 },
            { cat: 'Household', mode: 'assisted', limit: '₹50,000', blast: 5 },
            { cat: 'Personal Care', mode: 'assisted', limit: '₹50,000', blast: 5 },
          ].map(c => (
            <div key={c.cat} style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.75rem 1rem',
              background: 'var(--surface-1)',
              borderRadius: 'var(--radius-sm)',
            }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{c.cat}</div>
                <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
                  Max spend per PO: {c.limit} · Max blast radius: {c.blast} SKUs
                </div>
              </div>
              <AuthorityBadge mode={c.mode} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
