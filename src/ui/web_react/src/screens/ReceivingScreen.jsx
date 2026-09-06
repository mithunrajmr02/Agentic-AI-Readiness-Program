import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, CheckCircle, RefreshCw, Inbox, Search } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * STEWARD Receiving & Purchase Orders Screen (/receiving)
 * Railway Process Track for warehouse receiving operations.
 */
export default function ReceivingScreen() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPOModal, setShowPOModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const [newPO, setNewPO] = useState({
    supplier_id: '',
    order_date: new Date().toISOString().split('T')[0],
    expected_delivery: '',
    items: [{ product_id: '', quantity_ordered: 50, unit_cost: 100 }],
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [poRes, suppRes, prodRes] = await Promise.all([
        axios.get(`${API_BASE}/orders`),
        axios.get(`${API_BASE}/suppliers`),
        axios.get(`${API_BASE}/products`),
      ]);
      setOrders(poRes.data || []);
      setSuppliers(suppRes.data || []);
      setProducts(prodRes.data || []);
    } catch (err) {
      console.error('Error fetching orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreatePO = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/orders`, {
        supplier_id: parseInt(newPO.supplier_id),
        order_date: newPO.order_date,
        expected_delivery: newPO.expected_delivery || null,
        items: newPO.items.map((item) => ({
          product_id: parseInt(item.product_id),
          quantity_ordered: parseInt(item.quantity_ordered),
          unit_cost: parseFloat(item.unit_cost),
        })),
      });
      setShowPOModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to create PO: ' + describeApiError(err));
    }
  };

  const handleQuickReceivePO = async (orderId) => {
    try {
      await axios.patch(`${API_BASE}/orders/${orderId}/receive`);
      fetchData();
    } catch (err) {
      alert('Failed to receive PO: ' + describeApiError(err));
    }
  };

  const filteredOrders = orders.filter((o) => {
    return (
      !searchQuery ||
      o.po_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(o.id).includes(searchQuery)
    );
  });

  const columns = [
    {
      key: 'po_number',
      label: 'PO NUMBER',
      width: '150px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'supplier_id',
      label: 'SUPPLIER',
      render: (val) => {
        const supp = suppliers.find((s) => s.id === val);
        return supp ? (
          <div>
            <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{supp.name}</div>
            <div style={{ fontSize: '11px', color: 'var(--ink-3)' }}>{supp.supplier_code}</div>
          </div>
        ) : (
          `Supplier #${val}`
        );
      },
    },
    {
      key: 'order_date',
      label: 'ORDER DATE',
      width: '120px',
      render: (val) => <span className="t-mono" style={{ fontSize: '12px', color: 'var(--ink-2)' }}>{val || '—'}</span>,
    },
    {
      key: 'expected_delivery',
      label: 'EXPECTED ARRIVAL',
      width: '140px',
      render: (val, row) => {
        const isOverdue = val && new Date(val) < new Date('2026-08-25') && row.status !== 'received';
        return (
          <div>
            <span className="t-mono" style={{ fontSize: '12px', color: isOverdue ? 'var(--critical)' : 'var(--ink-2)', fontWeight: isOverdue ? 700 : 500 }}>
              {val || '—'}
            </span>
            {isOverdue && (
              <div style={{ fontSize: '10px', color: 'var(--critical)', fontWeight: 600 }}>Overdue</div>
            )}
          </div>
        );
      },
    },
    {
      key: 'total_amount',
      label: 'TOTAL VALUE',
      width: '130px',
      align: 'right',
      render: (val) => (
        <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>
          ₹{val ? val.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'STATUS',
      width: '140px',
      render: (val) => {
        const isReceived = val === 'received';
        const isDraft = val === 'draft';
        return (
          <span
            className={`badge ${isReceived ? 'badge-success' : isDraft ? 'badge-neutral' : 'badge-warning'}`}
            style={{ fontSize: '10px' }}
          >
            {val || 'submitted'}
          </span>
        );
      },
    },
    {
      key: 'actions',
      label: '',
      width: '200px',
      render: (_, row) => (
        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
          {row.status !== 'received' && (
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/receiving/${row.po_number || row.id}`);
              }}
            >
              Partial / Dock Entry →
            </button>
          )}
          {row.status !== 'received' && (
            <button
              type="button"
              className="btn btn-success btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                handleQuickReceivePO(row.id);
              }}
              title="Full receipt"
            >
              Receive
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="receiving-screen" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="t-hero" style={{ margin: 0 }}>Receiving & Purchase Orders</h1>
          <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
            Inbound replenishment orders, delivery timelines, and dock receipt intake.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--ink-3)' }} />
            <input
              type="text"
              placeholder="Search PO number…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ paddingLeft: '32px', fontSize: 'var(--t-meta-size)' }}
            />
          </div>

          <button type="button" className="btn btn-outline btn-sm" onClick={fetchData} title="Refresh orders">
            <RefreshCw size={14} /> Refresh
          </button>

          <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowPOModal(true)}>
            <Plus size={15} /> Create PO
          </button>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={filteredOrders}
          loading={loading}
          onRowClick={(row) => navigate(`/receiving/${row.po_number || row.id}`)}
        />
      </Card>

      {/* Create PO Modal */}
      {showPOModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="card-header">
              <span className="card-title">Raise Replenishment Purchase Order</span>
              <button
                type="button"
                onClick={() => setShowPOModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ink-3)' }}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreatePO} style={{ padding: '1.5rem' }}>
              <div className="form-group">
                <label className="form-label">Vendor / Supplier</label>
                <select
                  required
                  value={newPO.supplier_id}
                  onChange={(e) => setNewPO({ ...newPO, supplier_id: e.target.value })}
                  className="form-control"
                >
                  <option value="">Select supplier…</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.supplier_code})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Order Date</label>
                  <input
                    type="date"
                    required
                    value={newPO.order_date}
                    onChange={(e) => setNewPO({ ...newPO, order_date: e.target.value })}
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Expected Delivery Date</label>
                  <input
                    type="date"
                    value={newPO.expected_delivery}
                    onChange={(e) => setNewPO({ ...newPO, expected_delivery: e.target.value })}
                    className="form-control"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Product Item</label>
                <select
                  required
                  value={newPO.items[0]?.product_id || ''}
                  onChange={(e) => {
                    const prodId = e.target.value;
                    const foundProd = products.find((p) => String(p.id) === String(prodId));
                    const updated = [...newPO.items];
                    updated[0] = {
                      ...updated[0],
                      product_id: prodId,
                      unit_cost: foundProd ? foundProd.cost_price : updated[0].unit_cost,
                    };
                    setNewPO({ ...newPO, items: updated });
                  }}
                  className="form-control"
                >
                  <option value="">Select product SKU…</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.sku} — {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    required
                    value={newPO.items[0]?.quantity_ordered || 50}
                    onChange={(e) => {
                      const updated = [...newPO.items];
                      updated[0] = { ...updated[0], quantity_ordered: e.target.value };
                      setNewPO({ ...newPO, items: updated });
                    }}
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit Cost (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newPO.items[0]?.unit_cost || 100}
                    onChange={(e) => {
                      const updated = [...newPO.items];
                      updated[0] = { ...updated[0], unit_cost: e.target.value };
                      setNewPO({ ...newPO, items: updated });
                    }}
                    className="form-control"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowPOModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Submit Purchase Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
