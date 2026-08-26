import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, RefreshCw } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.7 Suppliers Directory (/suppliers)
 * Decomposed supplier catalog and registration from App.jsx
 */
export default function SuppliersScreen() {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [newSupplier, setNewSupplier] = useState({
    name: '', supplier_code: '', contact_email: '', payment_terms_days: 30, lead_time_days: 7
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/suppliers`);
      setSuppliers(res.data);
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/suppliers`, {
        ...newSupplier,
        payment_terms_days: parseInt(newSupplier.payment_terms_days),
        lead_time_days: parseInt(newSupplier.lead_time_days)
      });
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to create supplier: ' + describeApiError(err));
    }
  };

  const columns = [
    {
      key: 'supplier_code',
      label: 'CODE',
      width: '130px',
      render: (val) => <strong>{val}</strong>,
    },
    {
      key: 'name',
      label: 'SUPPLIER NAME',
      render: (val) => <span style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'contact_email',
      label: 'CONTACT EMAIL',
      render: (val) => val || '—',
    },
    {
      key: 'payment_terms_days',
      label: 'TERMS',
      width: '130px',
      render: (val) => `Net ${val} days`,
    },
    {
      key: 'lead_time_days',
      label: 'LEAD TIME',
      width: '130px',
      render: (val) => `${val} days`,
    },
    {
      key: 'is_active',
      label: 'STATUS',
      width: '120px',
      render: (val) => (
        <span className={`badge ${val !== false ? 'badge-success' : 'badge-danger'}`}>
          {val !== false ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '',
      width: '120px',
      render: (_, row) => (
        <button
          className="btn btn-outline"
          style={{ padding: '0.25rem 0.6rem', fontSize: '11px' }}
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/suppliers/${row.id}`);
          }}
        >
          Scorecard ↗
        </button>
      ),
    },
  ];

  return (
    <div className="suppliers-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Supplier Directory</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Approved vendors, reliability scorecards, and lead times.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline" onClick={fetchData}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={15} /> Register Supplier
          </button>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={suppliers}
          loading={loading}
          onRowClick={(row) => navigate(`/suppliers/${row.id}`)}
        />
      </Card>

      {/* Register Supplier Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">Register New Supplier</div>
              <button className="close-btn" onClick={() => setShowModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreateSupplier}>
              <div className="form-group">
                <label>Supplier Name</label>
                <input
                  type="text"
                  className="form-control"
                  required
                  value={newSupplier.name}
                  onChange={e => setNewSupplier({...newSupplier, name: e.target.value})}
                  placeholder="e.g. Reliable Wholesale Ltd"
                />
              </div>
              <div className="form-group">
                <label>Supplier Code (Unique)</label>
                <input
                  type="text"
                  className="form-control"
                  required
                  value={newSupplier.supplier_code}
                  onChange={e => setNewSupplier({...newSupplier, supplier_code: e.target.value})}
                  placeholder="e.g. SUP-0004"
                />
              </div>
              <div className="form-group">
                <label>Contact Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={newSupplier.contact_email}
                  onChange={e => setNewSupplier({...newSupplier, contact_email: e.target.value})}
                  placeholder="orders@supplier.com"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Payment Terms (Days)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={newSupplier.payment_terms_days}
                    onChange={e => setNewSupplier({...newSupplier, payment_terms_days: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Lead Time (Days)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={newSupplier.lead_time_days}
                    onChange={e => setNewSupplier({...newSupplier, lead_time_days: e.target.value})}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Supplier</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
