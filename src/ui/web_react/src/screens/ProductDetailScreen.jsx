import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Card, Table, MetricTile, ProvenanceMark } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.6 Product Detail (/inventory/:sku)
 * Velocity, movement ledger audit, ROP divergence.
 */
export default function ProductDetailScreen() {
  const { sku } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${API_BASE}/products`);
        const found = res.data.find(p => p.sku === sku || String(p.id) === sku);
        if (found) {
          // Fetch full movement details
          const detailRes = await axios.get(`${API_BASE}/products/${found.id}`, {
            params: { movement_limit: 50 }
          });
          setProduct(detailRes.data);
        } else {
          setError(`Product ${sku} not found.`);
        }
      } catch (err) {
        setError(describeApiError(err));
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [sku]);

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading product details for {sku}…</div>;
  }

  if (error || !product) {
    return (
      <div style={{ padding: '2rem' }}>
        <Link to="/inventory">← Back to Inventory</Link>
        <p style={{ color: 'var(--critical)', marginTop: '1rem' }}>{error || 'Product not found.'}</p>
      </div>
    );
  }

  const movements = product.movements || [];

  const columns = [
    {
      key: 'recorded_at',
      label: 'RECORDED AT',
      width: '180px',
      render: (val) => val ? new Date(val).toLocaleString('en-IN') : '—',
    },
    {
      key: 'movement_type',
      label: 'TYPE',
      width: '120px',
      render: (val) => <span className="badge badge-primary">{val}</span>,
    },
    {
      key: 'quantity',
      label: 'QUANTITY',
      width: '120px',
      align: 'right',
      render: (val) => {
        const isIn = val > 0;
        return (
          <strong style={{ color: isIn ? 'var(--good)' : 'var(--critical)' }}>
            {isIn ? `+${val}` : val}
          </strong>
        );
      },
    },
    {
      key: 'reference_number',
      label: 'REFERENCE',
      render: (val) => val || '—',
    },
    {
      key: 'notes',
      label: 'NOTES',
      render: (val) => val || '—',
    },
    {
      key: 'recorded_by',
      label: 'RECORDED BY',
      width: '140px',
      render: (val) => val || '—',
    },
  ];

  return (
    <div className="product-detail-screen">
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/inventory" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
          ← Back to Inventory
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span className="t-mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>{product.sku}</span>
            <span className="badge badge-primary">{product.category}</span>
          </div>
          <h1 className="t-display" style={{ margin: '0.25rem 0' }}>{product.name}</h1>
          <p className="t-meta">Unit: {product.unit_of_measure} · Cost: ₹{product.cost_price?.toFixed(2)} · Selling: ₹{product.unit_price?.toFixed(2)}</p>
        </div>
      </div>

      <div className="stats-grid">
        <MetricTile
          label="On Hand"
          value={product.stock_level?.quantity_on_hand ?? 0}
          suffix={` ${product.unit_of_measure}`}
          tier="T1"
          disclosure="real"
        />
        <MetricTile
          label="Available"
          value={product.stock_level?.quantity_available ?? 0}
          suffix={` ${product.unit_of_measure}`}
          tier="T1"
          disclosure="real"
        />
        <MetricTile
          label="Configured ROP"
          value={product.reorder_point}
          tier="T1"
          disclosure="real"
          detail={`Reorder quantity: ${product.reorder_quantity}`}
        />
        <MetricTile
          label="Measured Velocity"
          value={null}
          tier="T3"
          disclosure="synthetic"
          formula="Σ sales / distinct sale days"
          missingInput="≥ 14 distinct sale events in 30 days"
        />
      </div>

      <Card title="Stock Movement Ledger (Audit Trail)">
        <Table
          columns={columns}
          rows={movements}
          emptyState="No stock movements recorded for this product yet."
        />
      </Card>
    </div>
  );
}
