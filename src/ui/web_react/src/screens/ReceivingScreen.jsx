import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, CheckCircle, RefreshCw } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.8 Receiving & POs (/receiving)
 * Decomposed PO creation and goods receipt from App.jsx
 */
export default function ReceivingScreen() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPOModal, setShowPOModal] = useState(false);

  const [newPO, setNewPO] = useState({
    supplier_id: '', order_date: new Date().toISOString().split('T')[0],
    expected_delivery: '', items: [{ product_id: '', quantity_ordered: 50, unit_cost: 100 }]
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [poRes, suppRes, prodRes] = await Promise.all([
        axios.get(`${API_BASE}/orders`),
        axios.get(`${API_BASE}/suppliers`),
        axios.get(`${API_BASE}/products`),
      ]);
      setOrders(poRes.data);
      setSuppliers(suppRes.data);
      setProducts(prodRes.data);
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
        items: newPO.items.map(item => ({
          product_id: parseInt(item.product_id),
          quantity_ordered: parseInt(item.quantity_ordered),
          unit_cost: parseFloat(item.unit_cost)
        }))
      });
      setShowPOModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to create PO: ' + describeApiError(err));
    }
  };

  const handleReceivePO = async (orderId) => {
    try {
      await axios.patch(`${API_BASE}/orders/${orderId}/receive`);
      fetchData();
    } catch (err) {
      alert('Failed to receive PO: ' + describeApiError(err));
    }
  };

  const columns = [
    {
      key: 'po_number',
      label: 'PO NUMBER',
      width: '140px',
      render: (val) => <strong className="t-mono">{val}</strong>,
    },
    {
      key: 'supplier_id',
      label: 'SUPPLIER',
      render: (val) => {
        const supp = suppliers.find(s => s.id === val);
        return supp ? `${supp.supplier_code} — ${supp.name}` : `Supplier #${val}`;
      },
    },
    {
      key: 'order_date',
      label: 'ORDER DATE',
      width: '120px',
      render: (val) => val || '—',
    },
    {
      key: 'expected_delivery',
      label: 'EXPECTED',
      width: '120px',
      render: (val) => val || '—',
    },
    {
      key: 'total_amount',
      label: 'TOTAL (₹)',
      width: '130px',
      align: 'right',
      render: (val) => `₹${val?.toLocaleString('en-IN')}`,
    },
    {
      key: 'status',
      label: 'STATUS',
      width: '130px',
      render: (val) => (
        <span className={`badge ${
          val === 'received' ? 'badge-success' :
          val === 'draft' ? 'badge-primary' : 'badge-warning'
        }`}>
          {val}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'ACTIONS',
      width: '190px',
      render: (_, row) => (
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          {row.status !== 'received' && (
            <button
              className="btn btn-success"
              style={{ padding: '0.25rem 0.6rem', fontSize: '11px' }}
              onClick={(e) => {
                e.stopPropagation();
                handleReceivePO(row.id);
              }}
            >
              <CheckCircle size={12} /> Receive Quick
            </button>
          )}
          <button
            className="btn btn-outline"
            style={{ padding: '0.25rem 0.6rem', fontSize: '11px' }}
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/receiving/${row.po_number}`);
            }}
          >
            Entry ↗
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="receiving-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Receiving & Purchase Orders</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Goods receipt, backdating, and purchase order processing.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline" onClick={fetchData}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowPOModal(true)}>
            <Plus size={15} /> Raise PO
          </button>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={orders}
          loading={loading}
          onRowClick={(row) => navigate(`/receiving/${row.po_number}`)}
        />
      </Card>

      {/* Raise PO Modal */}
      {showPOModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">Raise Purchase Order</div>
              <button className="close-btn" onClick={() => setShowPOModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreatePO}>
              <div className="form-group">
                <label>Select Supplier</label>
                <select
                  className="form-control"
                  required
                  value={newPO.supplier_id}
                  onChange={e => setNewPO({...newPO, supplier_id: e.target.value})}
                >
                  <option value="">-- Select Active Supplier --</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.supplier_code} - {s.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Select Product to Order</label>
                <select
                  className="form-control"
                  required
                  value={newPO.items[0].product_id}
                  onChange={e => {
                    const prod = products.find(p => p.id === parseInt(e.target.value));
                    setNewPO({
                      ...newPO,
                      items: [{
                        product_id: e.target.value,
                        quantity_ordered: prod?.reorder_quantity || 50,
                        unit_cost: prod?.cost_price || 100
                      }]
                    });
                  }}
                >
                  <option value="">-- Select Product --</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.sku} - {p.name} (Cost: ₹{p.cost_price})</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Quantity Ordered</label>
                  <input
                    type="number"
                    className="form-control"
                    required
                    value={newPO.items[0].quantity_ordered}
                    onChange={e => {
                      const items = [...newPO.items];
                      items[0].quantity_ordered = e.target.value;
                      setNewPO({...newPO, items});
                    }}
                  />
                </div>
                <div className="form-group">
                  <label>Agreed Unit Cost (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    required
                    value={newPO.items[0].unit_cost}
                    onChange={e => {
                      const items = [...newPO.items];
                      items[0].unit_cost = e.target.value;
                      setNewPO({...newPO, items});
                    }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowPOModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Purchase Order</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
