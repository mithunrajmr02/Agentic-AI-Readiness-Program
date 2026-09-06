import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, History, RefreshCw, Search, Package, CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * STEWARD Inventory Catalog Screen (/inventory)
 * Horizon Catalog Layout: Category tabs, search, stock health indicators, and stock adjustment dialogs.
 */
export default function InventoryScreen() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [showProductModal, setShowProductModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Forms
  const [newProduct, setNewProduct] = useState({
    name: '',
    category: 'grocery',
    unit_price: '',
    cost_price: '',
    unit_of_measure: 'pieces',
    reorder_point: 10,
    reorder_quantity: 50,
    supplier_id: '',
  });

  const [stockAdjustment, setStockAdjustment] = useState({
    movement_type: 'receipt',
    quantity: '',
    reference_number: '',
    notes: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [prodRes, suppRes] = await Promise.all([
        axios.get(`${API_BASE}/products`),
        axios.get(`${API_BASE}/suppliers`),
      ]);
      setProducts(prodRes.data || []);
      setSuppliers(suppRes.data || []);
    } catch (err) {
      console.error('Error fetching inventory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/products`, {
        ...newProduct,
        unit_price: parseFloat(newProduct.unit_price),
        cost_price: parseFloat(newProduct.cost_price),
        reorder_point: parseInt(newProduct.reorder_point),
        reorder_quantity: parseInt(newProduct.reorder_quantity),
        supplier_id: newProduct.supplier_id ? parseInt(newProduct.supplier_id) : null,
      });
      setShowProductModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to register product: ' + describeApiError(err));
    }
  };

  const handleUpdateStock = async (e) => {
    e.preventDefault();
    if (!selectedProduct) return;
    try {
      await axios.patch(`${API_BASE}/products/${selectedProduct.id}/stock`, {
        movement_type: stockAdjustment.movement_type,
        quantity: parseInt(stockAdjustment.quantity),
        reference_number: stockAdjustment.reference_number,
        notes: stockAdjustment.notes,
      });
      setShowStockModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to record stock movement: ' + describeApiError(err));
    }
  };

  // Filter products by category and search
  const filteredProducts = products.filter((p) => {
    const matchesCat = categoryFilter === 'all' || p.category?.toLowerCase() === categoryFilter.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const categories = ['all', ...Array.from(new Set(products.map((p) => p.category).filter(Boolean)))];

  const columns = [
    {
      key: 'sku',
      label: 'SKU',
      width: '130px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'name',
      label: 'PRODUCT & CATEGORY',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.2rem' }}>
            <span className="badge badge-accent" style={{ fontSize: '10px' }}>{row.category}</span>
            <span style={{ fontSize: '11px', color: 'var(--ink-3)' }}>Reorder Pack: {row.reorder_quantity}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'unit_price',
      label: 'PRICE / COST',
      width: '140px',
      align: 'right',
      render: (val, row) => (
        <div style={{ textAlign: 'right' }}>
          <div className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>₹{val?.toFixed(2)}</div>
          <div className="t-mono" style={{ fontSize: '11px', color: 'var(--ink-3)' }}>Cost: ₹{row.cost_price?.toFixed(2)}</div>
        </div>
      ),
    },
    {
      key: 'on_hand',
      label: 'ON HAND',
      width: '120px',
      align: 'right',
      render: (_, row) => (
        <span className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>
          {row.stock_level?.quantity_on_hand ?? 0} {row.unit_of_measure}
        </span>
      ),
    },
    {
      key: 'available',
      label: 'AVAILABLE COVER',
      width: '160px',
      align: 'right',
      render: (_, row) => {
        const avail = row.stock_level?.quantity_available ?? 0;
        const isOut = avail <= 0;
        const isLow = avail <= row.reorder_point;

        return (
          <div style={{ textAlign: 'right' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <span
                className="t-mono"
                style={{
                  fontWeight: 700,
                  color: isOut ? 'var(--critical)' : isLow ? 'var(--warn)' : 'var(--good)',
                }}
              >
                {avail} {row.unit_of_measure}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--ink-3)' }}>
              ROP: {row.reorder_point} {row.unit_of_measure}
            </div>
          </div>
        );
      },
    },
    {
      key: 'actions',
      label: '',
      width: '180px',
      render: (_, row) => (
        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedProduct(row);
              setShowStockModal(true);
            }}
          >
            Adjust Stock
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/inventory/${row.sku}`);
            }}
            title="Inspect movement ledger"
          >
            <History size={13} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="inventory-screen" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Screen Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="t-hero" style={{ margin: 0 }}>Inventory Catalog & Positions</h1>
          <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
            Live SKU stock positions, autonomous reorder parameters, and movement ledgers.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--ink-3)' }} />
            <input
              type="text"
              placeholder="Search SKU or name…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ paddingLeft: '32px', fontSize: 'var(--t-meta-size)' }}
            />
          </div>

          <button type="button" className="btn btn-outline btn-sm" onClick={fetchData} title="Refresh catalog">
            <RefreshCw size={14} /> Refresh
          </button>

          <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowProductModal(true)}>
            <Plus size={15} /> Register Product
          </button>
        </div>
      </div>

      {/* Category Segmented Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setCategoryFilter(cat)}
            style={{
              background: categoryFilter === cat ? 'var(--surface-0)' : 'transparent',
              border: categoryFilter === cat ? '1px solid var(--border)' : '1px solid transparent',
              borderRadius: 'var(--radius-sm)',
              padding: '0.35rem 0.85rem',
              fontSize: 'var(--t-meta-size)',
              fontWeight: categoryFilter === cat ? 700 : 500,
              color: categoryFilter === cat ? 'var(--accent)' : 'var(--ink-2)',
              cursor: 'pointer',
              textTransform: 'capitalize',
              boxShadow: categoryFilter === cat ? 'var(--shadow-sm)' : 'none',
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Catalog Table Card */}
      <Card>
        <Table
          columns={columns}
          rows={filteredProducts}
          loading={loading}
          onRowClick={(row) => navigate(`/inventory/${row.sku}`)}
        />
      </Card>

      {/* Modal 1: Register Product */}
      {showProductModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="card-header">
              <span className="card-title">Register Product in Catalog</span>
              <button
                type="button"
                onClick={() => setShowProductModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ink-3)' }}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateProduct} style={{ padding: '1.5rem' }}>
              <div className="form-group">
                <label className="form-label">Product Name</label>
                <input
                  type="text"
                  required
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                  className="form-control"
                  placeholder="e.g. Wireless Ergonomic Mouse"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    value={newProduct.category}
                    onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
                    className="form-control"
                  >
                    <option value="electronics">Electronics</option>
                    <option value="grocery">Grocery</option>
                    <option value="clothing">Clothing</option>
                    <option value="household">Household</option>
                    <option value="personal_care">Personal Care</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Primary Supplier</label>
                  <select
                    value={newProduct.supplier_id}
                    onChange={(e) => setNewProduct({ ...newProduct, supplier_id: e.target.value })}
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
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Selling Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newProduct.unit_price}
                    onChange={(e) => setNewProduct({ ...newProduct, unit_price: e.target.value })}
                    className="form-control"
                    placeholder="0.00"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newProduct.cost_price}
                    onChange={(e) => setNewProduct({ ...newProduct, cost_price: e.target.value })}
                    className="form-control"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Reorder Point (ROP)</label>
                  <input
                    type="number"
                    required
                    value={newProduct.reorder_point}
                    onChange={(e) => setNewProduct({ ...newProduct, reorder_point: e.target.value })}
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Reorder Quantity (ROQ)</label>
                  <input
                    type="number"
                    required
                    value={newProduct.reorder_quantity}
                    onChange={(e) => setNewProduct({ ...newProduct, reorder_quantity: e.target.value })}
                    className="form-control"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowProductModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Register Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Stock Adjustment */}
      {showStockModal && selectedProduct && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="card-header">
              <span className="card-title">Record Physical Stock Movement</span>
              <button
                type="button"
                onClick={() => setShowStockModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ink-3)' }}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleUpdateStock} style={{ padding: '1.5rem' }}>
              <div style={{ background: 'var(--surface-1)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem' }}>
                <div style={{ fontWeight: 700, color: 'var(--ink-1)' }}>{selectedProduct.name}</div>
                <div className="t-mono" style={{ fontSize: '11px', color: 'var(--ink-3)' }}>
                  SKU: {selectedProduct.sku} · Current Available: {selectedProduct.stock_level?.quantity_available ?? 0} {selectedProduct.unit_of_measure}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Movement Type</label>
                <select
                  value={stockAdjustment.movement_type}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, movement_type: e.target.value })}
                  className="form-control"
                >
                  <option value="receipt">Goods Receipt (+)</option>
                  <option value="sale">Customer Sale (−)</option>
                  <option value="adjustment">Cycle Count Audit (±)</option>
                  <option value="return">Customer Return (+)</option>
                  <option value="damage">Damaged / Write-off (−)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input
                  type="number"
                  required
                  value={stockAdjustment.quantity}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, quantity: e.target.value })}
                  className="form-control"
                  placeholder="e.g. 20"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Reference Number (Optional)</label>
                <input
                  type="text"
                  value={stockAdjustment.reference_number}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, reference_number: e.target.value })}
                  className="form-control"
                  placeholder="e.g. INV-2026-0825"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Audit Notes</label>
                <textarea
                  value={stockAdjustment.notes}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, notes: e.target.value })}
                  className="form-control"
                  rows={2}
                  placeholder="Physical verification notes…"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowStockModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Commit Movement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
