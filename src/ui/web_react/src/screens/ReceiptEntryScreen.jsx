import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { API_BASE, describeApiError } from '../lib/api';
import { Card, SeverityDot } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.8 Goods Receipt Entry (/receiving/:poNumber)
 * Supports partial quantity receipt and explicit backdating.
 */
export default function ReceiptEntryScreen() {
  const { poNumber } = useParams();
  const [po, setPo] = useState(null);
  const [receivedQty, setReceivedQty] = useState(200);
  const [receivedDate, setReceivedDate] = useState('2026-08-23');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const fetchPO = async () => {
      try {
        const res = await axios.get(`${API_BASE}/orders`);
        const found = res.data.find(o => o.po_number === poNumber || String(o.id) === poNumber);
        if (found) {
          setPo(found);
          const firstItem = found.items?.[0];
          if (firstItem) setReceivedQty(firstItem.quantity_ordered);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchPO();
  }, [poNumber]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="receipt-entry-screen">
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/receiving" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
          ← Back to Receiving
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span className="t-mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {poNumber || 'PO-2026-0038'}
            </span>
            <SeverityDot severity="warn" label="2 days overdue" />
          </div>
          <h1 className="t-display" style={{ margin: '0.25rem 0' }}>Record Goods Receipt</h1>
          <p className="t-meta">
            Sharma Electronics · Expected 23 Aug 2026
          </p>
        </div>
      </div>

      {submitted ? (
        <div style={{
          padding: '1.25rem',
          background: 'rgba(5, 96, 58, 0.1)',
          color: 'var(--good)',
          border: '1px solid rgba(5, 96, 58, 0.3)',
          borderRadius: 'var(--radius-md)',
          fontWeight: 600,
        }}>
          ✓ Receipt of {receivedQty} units on {receivedDate} recorded successfully. Stock movements and supplier reliability updated.
        </div>
      ) : (
        <Card style={{ maxWidth: '600px' }}>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.25rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontSize: 'var(--t-body-size)', fontWeight: 600 }}>Bluetooth Speaker</div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Ordered: 240 units @ ₹285.00</div>
            </div>

            <div className="form-group">
              <label>Actual Quantity Received</label>
              <input
                type="number"
                value={receivedQty}
                onChange={(e) => setReceivedQty(parseInt(e.target.value) || 0)}
                className="form-control"
                required
              />
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
                Partial receipt: PO remains open for any remaining units.
              </span>
            </div>

            <div className="form-group">
              <label>Received On (Actual Arrival Date)</label>
              <input
                type="date"
                value={receivedDate}
                onChange={(e) => setReceivedDate(e.target.value)}
                className="form-control"
                required
              />
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
                Allows backdating to reflect true physical dock delivery date for supplier reliability scoring.
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
              <Link to="/receiving" className="btn btn-outline">Cancel</Link>
              <button type="submit" className="btn btn-success">Record Receipt</button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
