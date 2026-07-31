import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Package, AlertTriangle, ShoppingCart, Truck, LayoutDashboard, 
  Plus, RefreshCw, CheckCircle, ArrowDownRight, ArrowUpRight, Search
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [lowAlerts, setLowAlerts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showProductModal, setShowProductModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [showPOModal, setShowPOModal] = useState(false);
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Form states
  const [newProduct, setNewProduct] = useState({
    name: '', category: 'grocery', unit_price: '', cost_price: '',
    unit_of_measure: 'pieces', reorder_point: 10, reorder_quantity: 50, supplier_id: ''
  });
  const [newSupplier, setNewSupplier] = useState({
    name: '', supplier_code: '', contact_email: '', payment_terms_days: 30, lead_time_days: 7
  });
  const [stockAdjustment, setStockAdjustment] = useState({
    movement_type: 'receipt', quantity: '', reference_number: '', notes: ''
  });
  const [newPO, setNewPO] = useState({
    supplier_id: '', order_date: new Date().toISOString().split('T')[0],
    expected_delivery: '', items: [{ product_id: '', quantity_ordered: 50, unit_cost: 100 }]
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, prodRes, alertRes, poRes, suppRes] = await Promise.all([
        axios.get(`${API_BASE}/dashboard`),
        axios.get(`${API_BASE}/products`),
        axios.get(`${API_BASE}/stock/low-alerts`),
        axios.get(`${API_BASE}/orders`),
        axios.get(`${API_BASE}/suppliers`)
      ]);
      setDashboard(dashRes.data);
      setProducts(prodRes.data);
      setLowAlerts(alertRes.data);
      setOrders(poRes.data);
      setSuppliers(suppRes.data);
    } catch (err) {
      console.error('Error fetching inventory data:', err);
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
      alert('Failed to create product: ' + (err.response?.data?.detail || err.message));
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
      alert('Failed to update stock: ' + (err.response?.data?.detail || err.message));
    }
  };

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
      alert('Failed to create PO: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/suppliers`, {
        ...newSupplier,
        payment_terms_days: parseInt(newSupplier.payment_terms_days),
        lead_time_days: parseInt(newSupplier.lead_time_days)
      });
      setShowSupplierModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to create supplier: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleReceivePO = async (orderId) => {
    try {
      await axios.patch(`${API_BASE}/orders/${orderId}/receive`);
      fetchData();
    } catch (err) {
      alert('Failed to receive PO: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">P7</div>
          <div>
            <div className="brand-title">Retail Inventory</div>
            <div className="brand-subtitle">POC-07 Platform</div>
          </div>
        </div>

        <ul className="nav-list">
          <li 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={20} />
            Dashboard
          </li>
          <li 
            className={`nav-item ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            <Package size={20} />
            Products & Stock
          </li>
          <li 
            className={`nav-item ${activeTab === 'alerts' ? 'active' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            <AlertTriangle size={20} />
            Low Stock Alerts ({lowAlerts.length})
          </li>
          <li 
            className={`nav-item ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            <ShoppingCart size={20} />
            Purchase Orders
          </li>
          <li 
            className={`nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}
            onClick={() => setActiveTab('suppliers')}
          >
            <Truck size={20} />
            Suppliers
          </li>
        </ul>
      </aside>

      {/* Main Area */}
      <main className="main-content">
        {/* Top Header */}
        <header className="header-bar">
          <div className="header-title">
            <h1>
              {activeTab === 'dashboard' && 'Inventory Dashboard'}
              {activeTab === 'products' && 'Product Catalog & Stock Management'}
              {activeTab === 'alerts' && 'Low Stock & Out of Stock Alerts'}
              {activeTab === 'orders' && 'Purchase Orders & Supplier Orders'}
              {activeTab === 'suppliers' && 'Supplier Catalog & Directory'}
            </h1>
            <p>Retail Operations & Procurement System — Phase 1</p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button className="btn btn-outline" onClick={fetchData}>
              <RefreshCw size={16} /> Refresh
            </button>
            <div className="user-badge">
              <div className="user-avatar">PS</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Priya Sharma</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Store Manager</div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Overview Cards */}
        {dashboard && (
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-header">
                <span>Total Products</span>
                <Package size={20} color="#3b82f6" />
              </div>
              <div className="stat-value">{dashboard.total_products}</div>
            </div>

            <div className="stat-card orange">
              <div className="stat-header">
                <span>Low Stock Items</span>
                <AlertTriangle size={20} color="#f59e0b" />
              </div>
              <div className="stat-value">{dashboard.low_stock_count}</div>
            </div>

            <div className="stat-card red">
              <div className="stat-header">
                <span>Out of Stock</span>
                <AlertTriangle size={20} color="#ef4444" />
              </div>
              <div className="stat-value">{dashboard.out_of_stock_count}</div>
            </div>

            <div className="stat-card green">
              <div className="stat-header">
                <span>Total Stock Value</span>
                <span>₹</span>
              </div>
              <div className="stat-value">₹{dashboard.total_stock_value.toLocaleString('en-IN')}</div>
            </div>
          </div>
        )}

        {/* TAB 1: DASHBOARD / PRODUCTS */}
        {(activeTab === 'dashboard' || activeTab === 'products') && (
          <section className="card-section">
            <div className="section-header">
              <div className="section-title">Product Catalog & Inventory Levels</div>
              <button className="btn btn-primary" onClick={() => setShowProductModal(true)}>
                <Plus size={16} /> Register New Product
              </button>
            </div>

            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Unit Price</th>
                    <th>Cost Price</th>
                    <th>On Hand</th>
                    <th>Available</th>
                    <th>Reorder Pt</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => {
                    const avail = p.stock_level?.quantity_available ?? 0;
                    const isOut = avail === 0;
                    const isLow = avail <= p.reorder_point;
                    return (
                      <tr key={p.id}>
                        <td><strong>{p.sku}</strong></td>
                        <td>{p.name}</td>
                        <td><span className="badge badge-primary">{p.category}</span></td>
                        <td>₹{p.unit_price.toFixed(2)}</td>
                        <td>₹{p.cost_price.toFixed(2)}</td>
                        <td>{p.stock_level?.quantity_on_hand ?? 0} {p.unit_of_measure}</td>
                        <td><strong>{avail}</strong> {p.unit_of_measure}</td>
                        <td>{p.reorder_point}</td>
                        <td>
                          {isOut ? (
                            <span className="badge badge-danger">Out of Stock</span>
                          ) : isLow ? (
                            <span className="badge badge-warning">Low Stock</span>
                          ) : (
                            <span className="badge badge-success">In Stock</span>
                          )}
                        </td>
                        <td>
                          <button 
                            className="btn btn-outline" 
                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                            onClick={() => {
                              setSelectedProduct(p);
                              setShowStockModal(true);
                            }}
                          >
                            Update Stock
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* TAB 2: ALERTS */}
        {activeTab === 'alerts' && (
          <section className="card-section">
            <div className="section-header">
              <div className="section-title">Critical Inventory Alerts</div>
            </div>
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Available Stock</th>
                    <th>Reorder Point</th>
                    <th>Reorder Quantity</th>
                    <th>Alert Status</th>
                  </tr>
                </thead>
                <tbody>
                  {lowAlerts.map(p => (
                    <tr key={p.id}>
                      <td><strong>{p.sku}</strong></td>
                      <td>{p.name}</td>
                      <td><span className="badge badge-primary">{p.category}</span></td>
                      <td><strong>{p.stock_level?.quantity_available ?? 0}</strong> {p.unit_of_measure}</td>
                      <td>{p.reorder_point}</td>
                      <td>{p.reorder_quantity}</td>
                      <td>
                        {p.stock_level?.quantity_available === 0 ? (
                          <span className="badge badge-danger">CRITICAL: OUT OF STOCK</span>
                        ) : (
                          <span className="badge badge-warning">WARNING: LOW STOCK</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {lowAlerts.length === 0 && (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
                        All stock levels are currently healthy!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* TAB 3: PURCHASE ORDERS */}
        {activeTab === 'orders' && (
          <section className="card-section">
            <div className="section-header">
              <div className="section-title">Supplier Purchase Orders</div>
              <button className="btn btn-primary" onClick={() => setShowPOModal(true)}>
                <Plus size={16} /> Raise Purchase Order
              </button>
            </div>
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>PO Number</th>
                    <th>Supplier ID</th>
                    <th>Order Date</th>
                    <th>Expected Delivery</th>
                    <th>Total Amount</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map(po => (
                    <tr key={po.id}>
                      <td><strong>{po.po_number}</strong></td>
                      <td>SUP-000{po.supplier_id}</td>
                      <td>{po.order_date}</td>
                      <td>{po.expected_delivery || 'N/A'}</td>
                      <td>₹{po.total_amount.toLocaleString('en-IN')}</td>
                      <td>
                        <span className={`badge ${
                          po.status === 'received' ? 'badge-success' :
                          po.status === 'draft' ? 'badge-primary' : 'badge-warning'
                        }`}>
                          {po.status}
                        </span>
                      </td>
                      <td>
                        {po.status !== 'received' && (
                          <button 
                            className="btn btn-success" 
                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                            onClick={() => handleReceivePO(po.id)}
                          >
                            <CheckCircle size={14} /> Receive PO
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* TAB 4: SUPPLIERS */}
        {activeTab === 'suppliers' && (
          <section className="card-section">
            <div className="section-header">
              <div className="section-title">Approved Suppliers Directory</div>
              <button className="btn btn-primary" onClick={() => setShowSupplierModal(true)}>
                <Plus size={16} /> Register New Supplier
              </button>
            </div>
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Supplier Name</th>
                    <th>Contact Email</th>
                    <th>Payment Terms</th>
                    <th>Lead Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers.map(s => (
                    <tr key={s.id}>
                      <td><strong>{s.supplier_code}</strong></td>
                      <td>{s.name}</td>
                      <td>{s.contact_email}</td>
                      <td>Net {s.payment_terms_days} days</td>
                      <td>{s.lead_time_days} days</td>
                      <td><span className="badge badge-success">Active</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

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
                  <option value="sale">Sale (Stock Out - use negative quantity)</option>
                  <option value="adjustment">Adjustment (Correction)</option>
                  <option value="transfer">Transfer</option>
                  <option value="return">Return</option>
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

      {/* Modal 3: Raise PO */}
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

      {/* Modal 4: Register Supplier */}
      {showSupplierModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <div className="modal-title">Register New Supplier</div>
              <button className="close-btn" onClick={() => setShowSupplierModal(false)}>&times;</button>
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
                <button type="button" className="btn btn-outline" onClick={() => setShowSupplierModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Supplier</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
