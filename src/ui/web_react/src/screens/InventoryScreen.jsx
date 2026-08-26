import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, History, RefreshCw } from 'lucide-react';
import { API_BASE, describeApiError } from '../lib/api';
import { Table, Card } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.6 Inventory Catalog (/inventory)
 * Decomposed product CRUD and stock adjustments from App.jsx
 */
export default function InventoryScreen() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showProductModal, setShowProductModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Forms
  const [newProduct, setNewProduct] = useState({
    name: '', category: 'grocery', unit_price: '', cost_price: '',
    unit_of_measure: 'pieces', reorder_point: 10, reorder_quantity: 50, supplier_id: ''
  });
  const [stockAdjustment, setStockAdjustment] = useState({
    movement_type: 'receipt', quantity: '', reference_number: '', notes: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [prodRes, suppRes] = await Promise.all([
        axios.get(`${API_BASE}/products`),
        axios.get(`${API_BASE}/suppliers`),
      ]);
      setProducts(prodRes.data);
      setSuppliers(suppRes.data);
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
        supplier_id: newProduct.supplier_id ? parseInt(newProduct.supplier_id) : null
      });
      setShowProductModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to create product: ' + describeApiError(err));
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
        notes: stockAdjustment.notes
      });
      setShowStockModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to update stock: ' + describeApiError(err));
    }
  };

  const columns = [
    {
      key: 'sku',
      label: 'SKU',
      width: '120px',
      render: (val) => <strong>{val}</strong>,
    },
    {
      key: 'name',
      label: 'PRODUCT NAME',
      render: (val, row) => (
        <div>
          <span style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</span>
          <span className="badge badge-primary" style={{ marginLeft: '0.5rem' }}>{row.category}</span>
        </div>
      ),
    },
    {
      key: 'unit_price',
      label: 'SELLING',
      width: '110px',
      align: 'right',
      render: (val) => `₹${val?.toFixed(2)}`,
    },
    {
      key: 'cost_price',
      label: 'COST',
      width: '110px',
      align: 'right',
      render: (val) => `₹${val?.toFixed(2)}`,
    },
    {
      key: 'on_hand',
      label: 'ON HAND',
      width: '120px',
      align: 'right',
      render: (_, row) => `${row.stock_level?.quantity_on_hand ?? 0} ${row.unit_of_measure}`,
    },
    {
      key: 'available',
      label: 'AVAILABLE',
      width: '120px',
      align: 'right',
      render: (_, row) => {
        const avail = row.stock_level?.quantity_available ?? 0;
        const isOut = avail <= 0;
        const isLow = avail <= row.reorder_point;
        return (
          <span style={{ fontWeight: 700, color: isOut ? 'var(--critical)' : isLow ? 'var(--warn)' : 'var(--good)' }}>
            {avail} {row.unit_of_measure}
          </span>
        );
      },
    },
    {
      key: 'reorder_point',
      label: 'ROP',
      width: '90px',
      align: 'right',
      render: (val) => val,
    },
    {
      key: 'actions',
      label: 'ACTIONS',
      width: '210px',
      render: (_, row) => (
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            className="btn btn-outline"
            style={{ padding: '0.25rem 0.55rem', fontSize: '11px' }}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedProduct(row);
              setShowStockModal(true);
            }}
          >
            Update Stock
          </button>
          <button
            className="btn btn-outline"
            style={{ padding: '0.25rem 0.55rem', fontSize: '11px' }}
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/inventory/${row.sku}`);
            }}
          >
            <History size={12} /> Audit
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="inventory-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Inventory Catalog</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Products, stock positions, and movement adjustments.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline" onClick={fetchData}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowProductModal(true)}>
            <Plus size={15} /> Register Product
          </button>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={products}
          loading={loading}
          onRowClick={(row) => navigate(`/inventory/${row.sku}`)}
        />
      </Card>

      {/* Modal 1: Register Product */}
      {showProductModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">Register New Product</div>
              <button className="close-btn" onClick={() => setShowProductModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreateProduct}>
              <div className="form-group">
                <label>Product Name</label>
                <input
                  type="text"
                  className="form-control"
                  required
                  value={newProduct.name}
                  onChange={e => setNewProduct({...newProduct, name: e.target.value})}
                  placeholder="e.g. Basmati Rice 5kg"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Category</label>
                  <select
                    className="form-control"
                    value={newProduct.category}
                    onChange={e => setNewProduct({...newProduct, category: e.target.value})}
                  >
                    <option value="grocery">Grocery (GRO)</option>
                    <option value="electronics">Electronics (ELC)</option>
                    <option value="clothing">Clothing (CLO)</option>
                    <option value="household">Household (HHD)</option>
                    <option value="personal_care">Personal Care (PRC)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Unit of Measure</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newProduct.unit_of_measure}
                    onChange={e => setNewProduct({...newProduct, unit_of_measure: e.target.value})}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Unit Selling Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    required
                    value={newProduct.unit_price}
                    onChange={e => setNewProduct({...newProduct, unit_price: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    required
                    value={newProduct.cost_price}
                    onChange={e => setNewProduct({...newProduct, cost_price: e.target.value})}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Reorder Point</label>
                  <input
                    type="number"
                    className="form-control"
                    value={newProduct.reorder_point}
                    onChange={e => setNewProduct({...newProduct, reorder_point: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Reorder Quantity</label>
                  <input
                    type="number"
                    className="form-control"
                    value={newProduct.reorder_quantity}
                    onChange={e => setNewProduct({...newProduct, reorder_quantity: e.target.value})}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Preferred Supplier</label>
                <select
                  className="form-control"
                  value={newProduct.supplier_id}
                  onChange={e => setNewProduct({...newProduct, supplier_id: e.target.value})}
                >
                  <option value="">-- None --</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.supplier_code} - {s.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowProductModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Product</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Stock Update */}
      {showStockModal && selectedProduct && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">Record Stock Movement: {selectedProduct.sku}</div>
              <button className="close-btn" onClick={() => setShowStockModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleUpdateStock}>
              <div className="form-group">
                <label>Movement Type</label>
                <select
                  className="form-control"
                  value={stockAdjustment.movement_type}
                  onChange={e => setStockAdjustment({...stockAdjustment, movement_type: e.target.value})}
                >
                  <option value="receipt">Receipt (Stock In)</option>
                  <option value="sale">Sale (Stock Out - negative)</option>
                  <option value="adjustment">Adjustment (Correction)</option>
                  <option value="transfer">Transfer</option>
                  <option value="returnm">Return</option>
                </select>
              </div>
              <div className="form-group">
                <label>Quantity (positive for IN, negative for OUT)</label>
                <input
                  type="number"
                  className="form-control"
                  required
                  value={stockAdjustment.quantity}
                  onChange={e => setStockAdjustment({...stockAdjustment, quantity: e.target.value})}
                  placeholder="e.g. 50 or -10"
                />
              </div>
              <div className="form-group">
                <label>Reference Number</label>
                <input
                  type="text"
                  className="form-control"
                  value={stockAdjustment.reference_number}
                  onChange={e => setStockAdjustment({...stockAdjustment, reference_number: e.target.value})}
                  placeholder="e.g. PO-2026-0001 or SALE-042"
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <input
                  type="text"
                  className="form-control"
                  value={stockAdjustment.notes}
                  onChange={e => setStockAdjustment({...stockAdjustment, notes: e.target.value})}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowStockModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Update Stock</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
