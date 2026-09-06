import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, RefreshCw, Truck, Search, ShieldCheck } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * STEWARD Suppliers Directory Screen (/suppliers)
 */
export default function SuppliersScreen() {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const [newSupplier, setNewSupplier] = useState({
    name: '',
    supplier_code: '',
    contact_email: '',
    payment_terms_days: 30,
    lead_time_days: 7,
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/suppliers`);
      setSuppliers(res.data || []);
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
        lead_time_days: parseInt(newSupplier.lead_time_days),
      });
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to register supplier: ' + describeApiError(err));
    }
  };

  const filteredSuppliers = suppliers.filter((s) => {
    return (
      !searchQuery ||
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.supplier_code.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const columns = [
    {
      key: 'supplier_code',
      label: 'CODE',
      width: '130px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'name',
      label: 'SUPPLIER NAME & CONTACT',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: '11px', color: 'var(--ink-3)', marginTop: '0.15rem' }}>
            {row.contact_email || 'No email on file'}
          </div>
        </div>
      ),
    },
    {
      key: 'payment_terms_days',
      label: 'PAYMENT TERMS',
      width: '150px',
      render: (val) => <span className="t-mono" style={{ color: 'var(--ink-2)' }}>Net {val} days</span>,
    },
    {
      key: 'lead_time_days',
      label: 'CONTRACT LEAD TIME',
      width: '180px',
      render: (val) => (
        <span className="badge badge-neutral" style={{ fontSize: '11px' }}>
          {val} days SLA
        </span>
      ),
    },
    {
      key: 'is_active',
      label: 'STATUS',
      width: '130px',
      render: (val) => (
        <span className={`badge ${val !== false ? 'badge-success' : 'badge-danger'}`}>
          {val !== false ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '',
      width: '140px',
      render: (_, row) => (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/suppliers/${row.id}`);
            }}
          >
            Scorecard →
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="suppliers-screen" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="t-hero" style={{ margin: 0 }}>Suppliers & Sourcing Directory</h1>
          <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
            Contracted vendors, baseline lead times, and reliability telemetry.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--ink-3)' }} />
            <input
              type="text"
              placeholder="Search vendor…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ paddingLeft: '32px', fontSize: 'var(--t-meta-size)' }}
            />
          </div>

          <button type="button" className="btn btn-outline btn-sm" onClick={fetchData} title="Refresh directory">
            <RefreshCw size={14} /> Refresh
          </button>

          <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>
            <Plus size={15} /> Add Supplier
          </button>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={filteredSuppliers}
          loading={loading}
          onRowClick={(row) => navigate(`/suppliers/${row.id}`)}
        />
      </Card>

      {/* Add Supplier Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="card-header">
              <span className="card-title">Register Sourcing Supplier</span>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ink-3)' }}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateSupplier} style={{ padding: '1.5rem' }}>
              <div className="form-group">
                <label className="form-label">Supplier Name</label>
                <input
                  type="text"
                  required
                  value={newSupplier.name}
                  onChange={(e) => setNewSupplier({ ...newSupplier, name: e.target.value })}
                  className="form-control"
                  placeholder="e.g. Apex Global Supplies"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Supplier Code</label>
                  <input
                    type="text"
                    required
                    value={newSupplier.supplier_code}
                    onChange={(e) => setNewSupplier({ ...newSupplier, supplier_code: e.target.value })}
                    className="form-control"
                    placeholder="SUP-0004"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Contact Email</label>
                  <input
                    type="email"
                    required
                    value={newSupplier.contact_email}
                    onChange={(e) => setNewSupplier({ ...newSupplier, contact_email: e.target.value })}
                    className="form-control"
                    placeholder="orders@supplier.com"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Contract Lead Time (Days)</label>
                  <input
                    type="number"
                    required
                    value={newSupplier.lead_time_days}
                    onChange={(e) => setNewSupplier({ ...newSupplier, lead_time_days: e.target.value })}
                    className="form-control"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Payment Terms (Net Days)</label>
                  <input
                    type="number"
                    required
                    value={newSupplier.payment_terms_days}
                    onChange={(e) => setNewSupplier({ ...newSupplier, payment_terms_days: e.target.value })}
                    className="form-control"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Register Supplier
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
