import React, { useState, useEffect } from 'react';
import { Search, Upload, Plus, Filter, Mail, Phone, Building2, Calendar, Clock, ChevronDown, Check, MoreHorizontal, Settings } from 'lucide-react';
import './Contacts.css';

const Contacts = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedContacts, setSelectedContacts] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [showAddContact, setShowAddContact] = useState(false);
  const [campaigns, setCampaigns] = useState({});
  
  const [newContact, setNewContact] = useState({
    name: '', phone: '', email: '', business_name: '', campaign_id: ''
  });

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchAllContacts();
  }, []);

  const fetchAllContacts = async () => {
    try {
      // Use optimized API to get all contacts at once
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/contacts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setContacts(data.contacts || []);
        
        // Build campaigns map for the add contact dropdown
        const campaignMap = {};
        (data.contacts || []).forEach(c => {
          if (c.campaign_id && c.campaign_name) {
            campaignMap[c.campaign_id] = c.campaign_name;
          }
        });
        setCampaigns(campaignMap);
      }
      
      // Also fetch campaigns list for Add Contact dropdown
      const campaignsRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (campaignsRes.ok) {
        const campaignsData = await campaignsRes.json();
        const campaignMap = {};
        (campaignsData.campaigns || []).forEach(c => {
          campaignMap[c.id] = c.name;
        });
        setCampaigns(campaignMap);
      }
      
    } catch (err) {
      console.error('Error fetching contacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedContacts([]);
    } else {
      setSelectedContacts(filteredContacts.map(c => c.id));
    }
    setSelectAll(!selectAll);
  };

  const handleSelectContact = (id) => {
    if (selectedContacts.includes(id)) {
      setSelectedContacts(selectedContacts.filter(cid => cid !== id));
    } else {
      setSelectedContacts([...selectedContacts, id]);
    }
  };

  const handleAddContact = async (e) => {
    e.preventDefault();
    if (!newContact.campaign_id) {
      alert('Please select a campaign');
      return;
    }
    
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${newContact.campaign_id}/opportunities`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newContact.name,
          phone: newContact.phone,
          email: newContact.email,
          business_name: newContact.business_name
        })
      });
      
      if (res.ok) {
        setShowAddContact(false);
        setNewContact({ name: '', phone: '', email: '', business_name: '', campaign_id: '' });
        fetchAllContacts();
      }
    } catch (err) {
      console.error('Error adding contact:', err);
    }
  };

  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(/[\s_]+/).filter(p => p.length > 0);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const getAvatarColor = (name) => {
    const colors = [
      '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', 
      '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
    ];
    if (!name) return colors[0];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }) + ' ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const getTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    const diffWeeks = Math.floor(diffDays / 7);

    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return `${diffWeeks} week${diffWeeks > 1 ? 's' : ''} ago`;
  };

  const filteredContacts = contacts.filter(contact => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      contact.name?.toLowerCase().includes(query) ||
      contact.phone?.includes(query) ||
      contact.email?.toLowerCase().includes(query) ||
      contact.business_name?.toLowerCase().includes(query) ||
      contact.campaign_name?.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return <div className="contacts-loading">Loading contacts...</div>;
  }

  return (
    <div className="contacts-page" data-testid="contacts-page">
      {/* Header */}
      <div className="contacts-header">
        <div className="header-left">
          <h1>Contacts</h1>
          <span className="contact-count">{contacts.length} Contacts</span>
        </div>
        <div className="header-actions">
          <button className="import-btn">
            <Upload size={16} />
            Import
          </button>
          <button className="add-contact-btn" onClick={() => setShowAddContact(true)} data-testid="add-contact-btn">
            <Plus size={16} />
            Add Contact
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="contacts-toolbar">
        <div className="toolbar-left">
          {selectedContacts.length > 0 && (
            <div className="selection-info">
              <span>{selectedContacts.length} Contacts Selected</span>
              <button className="select-all-btn" onClick={handleSelectAll}>
                Select All {contacts.length}
              </button>
            </div>
          )}
        </div>
        <div className="toolbar-right">
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search Contacts"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="search-contacts"
            />
          </div>
          <button className="manage-fields-btn">
            <Settings size={16} />
            Manage Fields
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="contacts-table-wrapper">
        <table className="contacts-table" data-testid="contacts-table">
          <thead>
            <tr>
              <th className="checkbox-col">
                <label className="checkbox-wrapper">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                  />
                  <span className="checkmark"></span>
                </label>
              </th>
              <th>Contact Name</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Business Name</th>
              <th>Created (IST)</th>
              <th>Last Activity (IST)</th>
              <th>Campaign</th>
            </tr>
          </thead>
          <tbody>
            {filteredContacts.map(contact => (
              <tr key={contact.id} className={selectedContacts.includes(contact.id) ? 'selected' : ''}>
                <td className="checkbox-col">
                  <label className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      checked={selectedContacts.includes(contact.id)}
                      onChange={() => handleSelectContact(contact.id)}
                    />
                    <span className="checkmark"></span>
                  </label>
                </td>
                <td>
                  <div className="contact-name-cell">
                    <div className="contact-avatar" style={{ backgroundColor: getAvatarColor(contact.name) }}>
                      {getInitials(contact.name)}
                    </div>
                    <span>{contact.name}</span>
                  </div>
                </td>
                <td>
                  {contact.phone ? (
                    <div className="phone-cell">
                      <Phone size={14} />
                      {contact.phone}
                    </div>
                  ) : '-'}
                </td>
                <td>
                  {contact.email ? (
                    <div className="email-cell">
                      <Mail size={14} />
                      {contact.email}
                    </div>
                  ) : '-'}
                </td>
                <td>{contact.business_name || '-'}</td>
                <td>{formatDateTime(contact.created_at)}</td>
                <td>
                  {contact.updated_at && contact.updated_at !== contact.created_at ? (
                    <div className="activity-cell">
                      <Clock size={14} />
                      {getTimeAgo(contact.updated_at)}
                    </div>
                  ) : '-'}
                </td>
                <td>
                  <span className="campaign-tag">{contact.campaign_name}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredContacts.length === 0 && (
          <div className="empty-contacts">
            <Phone size={48} />
            <h3>No contacts found</h3>
            <p>Add contacts to your campaigns to see them here</p>
          </div>
        )}
      </div>

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="modal-overlay" onClick={() => setShowAddContact(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Contact</h2>
              <button className="close-btn" onClick={() => setShowAddContact(false)}>×</button>
            </div>
            <form onSubmit={handleAddContact}>
              <div className="form-group">
                <label>Campaign *</label>
                <select
                  value={newContact.campaign_id}
                  onChange={e => setNewContact({...newContact, campaign_id: e.target.value})}
                  required
                >
                  <option value="">Select a campaign</option>
                  {Object.entries(campaigns).map(([id, name]) => (
                    <option key={id} value={id}>{name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Contact Name *</label>
                <input
                  type="text"
                  value={newContact.name}
                  onChange={e => setNewContact({...newContact, name: e.target.value})}
                  placeholder="Full name"
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={newContact.phone}
                    onChange={e => setNewContact({...newContact, phone: e.target.value})}
                    placeholder="+91 XXXXXXXXXX"
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={newContact.email}
                    onChange={e => setNewContact({...newContact, email: e.target.value})}
                    placeholder="email@example.com"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Business Name</label>
                <input
                  type="text"
                  value={newContact.business_name}
                  onChange={e => setNewContact({...newContact, business_name: e.target.value})}
                  placeholder="Company name"
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="cancel-btn" onClick={() => setShowAddContact(false)}>Cancel</button>
                <button type="submit" className="submit-btn">Add Contact</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Contacts;
