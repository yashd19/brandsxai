import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Users, Building2, Shield, Plus, Edit2, Trash2, LogOut, Check } from 'lucide-react';
import './AdminPortal.css';

const AdminPortal = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [brands, setBrands] = useState([]);
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateBrand, setShowCreateBrand] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  
  const [newUser, setNewUser] = useState({ username: '', password: '', email: '', brand_id: '', feature_ids: [] });
  const [newBrand, setNewBrand] = useState('');
  
  const token = localStorage.getItem('admin_token');

  useEffect(() => {
    if (!token) {
      navigate('/admin/login');
      return;
    }
    fetchData();
  }, [token, navigate]);

  const fetchData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
      
      const [usersRes, brandsRes, featuresRes] = await Promise.all([
        fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users`, { headers }),
        fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/brands`, { headers }),
        fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/features`, { headers })
      ]);
      
      if (usersRes.ok) setUsers((await usersRes.json()).users || []);
      if (brandsRes.ok) setBrands((await brandsRes.json()).brands || []);
      if (featuresRes.ok) setFeatures((await featuresRes.json()).features || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newUser,
          brand_id: parseInt(newUser.brand_id),
          feature_ids: newUser.feature_ids.map(id => parseInt(id))
        })
      });
      
      if (res.ok) {
        setShowCreateUser(false);
        setNewUser({ username: '', password: '', email: '', brand_id: '', feature_ids: [] });
        fetchData();
      } else {
        const data = await res.json();
        alert(data.detail || 'Error creating user');
      }
    } catch (error) {
      alert('Error creating user');
    }
  };

  const handleUpdateFeatures = async (userId, featureIds) => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users/${userId}/features`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature_ids: featureIds })
      });
      
      if (res.ok) {
        setEditingUser(null);
        fetchData();
      }
    } catch (error) {
      alert('Error updating features');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;
    
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchData();
    } catch (error) {
      alert('Error deleting user');
    }
  };

  const handleCreateBrand = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/brands`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newBrand })
      });
      
      if (res.ok) {
        setShowCreateBrand(false);
        setNewBrand('');
        fetchData();
      } else {
        const data = await res.json();
        alert(data.detail || 'Error creating brand');
      }
    } catch (error) {
      alert('Error creating brand');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate('/admin/login');
  };

  const toggleFeature = (featureId) => {
    const id = parseInt(featureId);
    setNewUser(prev => ({
      ...prev,
      feature_ids: prev.feature_ids.includes(id)
        ? prev.feature_ids.filter(f => f !== id)
        : [...prev.feature_ids, id]
    }));
  };

  if (loading) {
    return <div className="admin-loading">Loading...</div>;
  }

  return (
    <div className="admin-portal">
      <header className="admin-header">
        <div className="admin-logo">
          <Shield size={24} />
          <span>MadOver AI Admin</span>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          <LogOut size={18} />
          Logout
        </button>
      </header>

      <div className="admin-content">
        <nav className="admin-tabs">
          <button 
            className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <Users size={18} />
            Users
          </button>
          <button 
            className={`admin-tab ${activeTab === 'brands' ? 'active' : ''}`}
            onClick={() => setActiveTab('brands')}
          >
            <Building2 size={18} />
            Brands
          </button>
        </nav>

        <div className="admin-panel">
          {activeTab === 'users' && (
            <div className="users-section">
              <div className="section-header">
                <h2>User Management</h2>
                <button className="create-btn" onClick={() => setShowCreateUser(true)}>
                  <Plus size={18} />
                  Create User
                </button>
              </div>

              <div className="users-table">
                <div className="table-header">
                  <span>Username</span>
                  <span>Email</span>
                  <span>Brand</span>
                  <span>Features</span>
                  <span>Status</span>
                  <span>Actions</span>
                </div>
                {users.map(user => (
                  <div key={user.id} className="table-row">
                    <span>{user.username}</span>
                    <span>{user.email || '-'}</span>
                    <span className="brand-badge">{user.brand?.name || '-'}</span>
                    <span className="features-cell">
                      {editingUser === user.id ? (
                        <div className="feature-edit">
                          {features.map(f => (
                            <label key={f.id} className="feature-checkbox">
                              <input
                                type="checkbox"
                                checked={user.features?.some(uf => uf.id === f.id)}
                                onChange={(e) => {
                                  const newFeatures = e.target.checked
                                    ? [...(user.features || []).map(uf => uf.id), f.id]
                                    : (user.features || []).filter(uf => uf.id !== f.id).map(uf => uf.id);
                                  handleUpdateFeatures(user.id, newFeatures);
                                }}
                              />
                              {f.name}
                            </label>
                          ))}
                        </div>
                      ) : (
                        user.features?.map(f => (
                          <span key={f.id} className="feature-tag">{f.name}</span>
                        )) || '-'
                      )}
                    </span>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span className="actions-cell">
                      <button 
                        className="action-btn edit"
                        onClick={() => setEditingUser(editingUser === user.id ? null : user.id)}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button 
                        className="action-btn delete"
                        onClick={() => handleDeleteUser(user.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </span>
                  </div>
                ))}
                {users.length === 0 && (
                  <div className="empty-state">No users created yet</div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'brands' && (
            <div className="brands-section">
              <div className="section-header">
                <h2>Brand Management</h2>
                <button className="create-btn" onClick={() => setShowCreateBrand(true)}>
                  <Plus size={18} />
                  Create Brand
                </button>
              </div>

              <div className="brands-grid">
                {brands.map(brand => (
                  <div key={brand.id} className="brand-card">
                    <Building2 size={32} />
                    <h3>{brand.name}</h3>
                    <p>Created: {new Date(brand.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
                {brands.length === 0 && (
                  <div className="empty-state">No brands created yet</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="modal-overlay" onClick={() => setShowCreateUser(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create New User</h2>
            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={e => setNewUser({...newUser, username: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={e => setNewUser({...newUser, password: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email (optional)</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={e => setNewUser({...newUser, email: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Brand</label>
                <select
                  value={newUser.brand_id}
                  onChange={e => setNewUser({...newUser, brand_id: e.target.value})}
                  required
                >
                  <option value="">Select Brand</option>
                  {brands.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Feature Access</label>
                <div className="feature-options">
                  {features.map(f => (
                    <label key={f.id} className="feature-option">
                      <input
                        type="checkbox"
                        checked={newUser.feature_ids.includes(f.id)}
                        onChange={() => toggleFeature(f.id)}
                      />
                      <span className="checkmark"><Check size={14} /></span>
                      {f.name}
                    </label>
                  ))}
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="cancel-btn" onClick={() => setShowCreateUser(false)}>
                  Cancel
                </button>
                <button type="submit" className="submit-btn">Create User</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Brand Modal */}
      {showCreateBrand && (
        <div className="modal-overlay" onClick={() => setShowCreateBrand(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create New Brand</h2>
            <form onSubmit={handleCreateBrand}>
              <div className="form-group">
                <label>Brand Name</label>
                <input
                  type="text"
                  value={newBrand}
                  onChange={e => setNewBrand(e.target.value)}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="cancel-btn" onClick={() => setShowCreateBrand(false)}>
                  Cancel
                </button>
                <button type="submit" className="submit-btn">Create Brand</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPortal;
