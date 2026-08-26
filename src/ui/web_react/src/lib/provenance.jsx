import React from 'react';

/**
 * Format currency in Indian Rupees (INR)
 */
export function formatINR(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

/**
 * Format numeric quantities
 */
export function formatQty(val, unit = '') {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return `${Number(val).toLocaleString('en-IN')}${unit ? ` ${unit}` : ''}`;
}

/**
 * Format timestamps
 */
export function formatDateTime(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

/**
 * Format relative duration / time ago
 */
export function formatTimeAgo(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    const diffMs = Date.now() - d.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return isoString;
  }
}
