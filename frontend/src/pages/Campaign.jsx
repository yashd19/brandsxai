import React, { useState, useEffect } from 'react';
import { Plus, X, ArrowLeft, Phone, Mail, Building2, DollarSign, User, MessageSquare, Calendar, Trash2, Search, Filter, ArrowUpDown, LayoutGrid, List, Settings } from 'lucide-react';
import './Campaign.css';

const STAGES = [
  { id: 'dialing', name: 'Dialing', color: '#3B82F6' },
  { id: 'interested', name: 'Interested', color: '#10B981' },
  { id: 'not_interested', name: 'Not Interested', color: '#EF4444' },
  { id: 'callback', name: 'Call back', color: '#F59E0B' },
  { id: 'store_visit', name: 'Store Visit', color: '#8B5CF6' },
  { id: 'invalid_number', name: 'Invalid Number', color: '#6B7280' }
];

const Campaign = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [stages, setStages] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreateCampaign, setShowCreateCampaign] = useState(false);
  const [showCreateOpportunity, setShowCreateOpportunity] = useState(false);
  const [draggedOpp, setDraggedOpp] = useState(null);
  const [viewMode, setViewMode] = useState('board');
  const [searchQuery, setSearchQuery] = useState('');

  const [newCampaign, setNewCampaign] = useState({
    name: '', description: '', start_date: '', end_date: '', target_audience: '', call_script: ''
  });

  const [newOpportunity, setNewOpportunity] = useState({
    name: '', phone: '', email: '', business_name: '', opportunity_value: 0, notes: ''
  });

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (err) {
      console.error('Error fetching campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaignDetails = async (campaignId) => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${campaignId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedCampaign(data.campaign);
        setStages(data.stages || {});
      }
    } catch (err) {
      console.error('Error fetching campaign:', err);
    }
  };

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newCampaign)
      });
      if (res.ok) {
        setShowCreateCampaign(false);
        setNewCampaign({ name: '', description: '', start_date: '', end_date: '', target_audience: '', call_script: '' });
        fetchCampaigns();
      }
    } catch (err) {
      console.error('Error creating campaign:', err);
    }
  };

  const handleCreateOpportunity = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${selectedCampaign.id}/opportunities`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newOpportunity)
      });
      if (res.ok) {
        setShowCreateOpportunity(false);
        setNewOpportunity({ name: '', phone: '', email: '', business_name: '', opportunity_value: 0, notes: '' });
        fetchCampaignDetails(selectedCampaign.id);
      }
    } catch (err) {
      console.error('Error creating opportunity:', err);
    }
  };

  const handleDragStart = (e, opp, stage) => {
    setDraggedOpp({ ...opp, fromStage: stage });
    e.target.classList.add('dragging');
  };

  const handleDragEnd = (e) => {
    e.target.classList.remove('dragging');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (toStage) => {
    if (!draggedOpp || draggedOpp.fromStage === toStage) {
      setDraggedOpp(null);
      return;
    }

    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/opportunities/${draggedOpp.id}/stage`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: toStage })
      });
      if (res.ok) {
        fetchCampaignDetails(selectedCampaign.id);
      }
    } catch (err) {
      console.error('Error updating stage:', err);
    }
    setDraggedOpp(null);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value || 0);
  };

  const getInitials = (name) => {
    if (!name) return 'A';
    const parts = name.split(/[_\s]+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  if (loading) {
    return <div className="campaign-loading">Loading campaigns...</div>;
  }

  // Campaign Pipeline View
  if (selectedCampaign) {
    return (
      <div className="campaign-pipeline" data-testid="campaign-pipeline">
        <div className="pipeline-header">
          <button className="back-btn" onClick={() => setSelectedCampaign(null)} data-testid="back-to-campaigns">
            <ArrowLeft size={20} />
            Back to Campaigns
          </button>
          <div className="pipeline-title">
            <h2>{selectedCampaign.name}</h2>
            <span className="campaign-status">{selectedCampaign.status}</span>
          </div>
          <button className="add-opp-btn" onClick={() => setShowCreateOpportunity(true)} data-testid="add-opportunity-btn">
            <Plus size={18} />
            Add Opportunity
          </button>
        </div>

        {/* Controls Bar */}
        <div className="pipeline-controls">
          <div className="controls-left">
            <div className="view-toggle">
              <button 
                className={viewMode === 'board' ? 'active' : ''} 
                onClick={() => setViewMode('board')}
              >
                <LayoutGrid size={16} />
                All
              </button>
              <button 
                className={viewMode === 'list' ? 'active' : ''} 
                onClick={() => setViewMode('list')}
              >
                <List size={16} />
                List
              </button>
            </div>
            <button className="filter-btn">
              <Filter size={16} />
              Advanced Filters
            </button>
            <button className="sort-btn">
              <ArrowUpDown size={16} />
              Sort (1)
            </button>
          </div>
          <div className="controls-right">
            <div className="search-box">
              <Search size={16} />
              <input 
                type="text" 
                placeholder="Search Opportunities" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="manage-fields-btn">
              <Settings size={16} />
              Manage Fields
            </button>
          </div>
        </div>

        <div className="pipeline-board">
          {STAGES.map(stage => (
            <div
              key={stage.id}
              className="pipeline-column"
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(stage.id)}
              data-testid={`column-${stage.id}`}
            >
              <div className="column-header" style={{ borderTopColor: stage.color }}>
                <h3>{stage.name}</h3>
                <div className="column-stats">
                  <span className="opp-count">{stages[stage.id]?.count || 0} Opportunities</span>
                  <span className="opp-value">{formatCurrency(stages[stage.id]?.total_value)}</span>
                </div>
              </div>
              <div className="column-cards">
                {(stages[stage.id]?.opportunities || [])
                  .filter(opp => !searchQuery || opp.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map(opp => (
                  <div
                    key={opp.id}
                    className="opportunity-card"
                    draggable
                    onDragStart={(e) => handleDragStart(e, opp, stage.id)}
                    onDragEnd={handleDragEnd}
                    data-testid={`opportunity-card-${opp.id}`}
                  >
                    <div className="card-header">
                      <h4>{opp.name}</h4>
                      <div className={`card-avatar ${stage.id === 'callback' ? 'callback' : ''}`}>
                        {stage.id === 'callback' ? 'CB' : getInitials(opp.name)}
                      </div>
                    </div>
                    {opp.business_name && (
                      <div className="card-info">
                        <Building2 size={14} />
                        <span>Business Name: {opp.business_name}</span>
                      </div>
                    )}
                    <div className="card-info">
                      <DollarSign size={14} />
                      <span>Opportunity Value: {formatCurrency(opp.opportunity_value)}</span>
                    </div>
                    <div className="card-actions">
                      <button className="action-btn" title="Call">
                        <Phone size={16} />
                      </button>
                      <button className="action-btn" title="Contact">
                        <User size={16} />
                      </button>
                      <button className="action-btn active" title="Message">
                        <MessageSquare size={16} />
                      </button>
                      <button className="action-btn active" title="Schedule">
                        <Calendar size={16} />
                      </button>
                      <button className="action-btn active" title="Email">
                        <Mail size={16} />
                      </button>
                      <button className="action-btn" title="Delete">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Create Opportunity Modal */}
        {showCreateOpportunity && (
          <div className="modal-overlay" onClick={() => setShowCreateOpportunity(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Add New Opportunity</h2>
                <button className="close-btn" onClick={() => setShowCreateOpportunity(false)}>
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleCreateOpportunity}>
                <div className="form-group">
                  <label>Contact Name *</label>
                  <input
                    type="text"
                    value={newOpportunity.name}
                    onChange={e => setNewOpportunity({...newOpportunity, name: e.target.value})}
                    placeholder="e.g., John Smith or AICaII_91XXXXXXXXXX"
                    required
                    data-testid="opportunity-name-input"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Phone</label>
                    <input
                      type="tel"
                      value={newOpportunity.phone}
                      onChange={e => setNewOpportunity({...newOpportunity, phone: e.target.value})}
                      placeholder="+91 XXXXXXXXXX"
                      data-testid="opportunity-phone-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={newOpportunity.email}
                      onChange={e => setNewOpportunity({...newOpportunity, email: e.target.value})}
                      placeholder="email@example.com"
                      data-testid="opportunity-email-input"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Business Name</label>
                  <input
                    type="text"
                    value={newOpportunity.business_name}
                    onChange={e => setNewOpportunity({...newOpportunity, business_name: e.target.value})}
                    placeholder="Company or NA"
                    data-testid="opportunity-business-input"
                  />
                </div>
                <div className="form-group">
                  <label>Opportunity Value ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newOpportunity.opportunity_value}
                    onChange={e => setNewOpportunity({...newOpportunity, opportunity_value: parseFloat(e.target.value) || 0})}
                    data-testid="opportunity-value-input"
                  />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={newOpportunity.notes}
                    onChange={e => setNewOpportunity({...newOpportunity, notes: e.target.value})}
                    rows={3}
                    placeholder="Additional notes..."
                    data-testid="opportunity-notes-input"
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="cancel-btn" onClick={() => setShowCreateOpportunity(false)}>Cancel</button>
                  <button type="submit" className="submit-btn" data-testid="submit-opportunity-btn">Add Opportunity</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Campaign List View
  return (
    <div className="campaign-list" data-testid="campaign-list">
      <div className="list-header">
        <h2>Voice AI Campaigns</h2>
        <button className="create-campaign-btn" onClick={() => setShowCreateCampaign(true)} data-testid="create-campaign-btn">
          <Plus size={18} />
          New Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="empty-state" data-testid="empty-campaigns">
          <div className="empty-icon">
            <Phone size={48} strokeWidth={1.5} />
          </div>
          <h3>No campaigns yet</h3>
          <p>Create your first voice calling campaign to get started</p>
          <button className="create-first-btn" onClick={() => setShowCreateCampaign(true)}>
            <Plus size={18} />
            Create Campaign
          </button>
        </div>
      ) : (
        <div className="campaigns-grid">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="campaign-card" onClick={() => fetchCampaignDetails(campaign.id)} data-testid={`campaign-card-${campaign.id}`}>
              <div className="campaign-card-header">
                <h3>{campaign.name}</h3>
                <span className={`status-badge ${campaign.status}`}>{campaign.status}</span>
              </div>
              <p className="campaign-desc">{campaign.description || 'No description'}</p>
              <div className="campaign-stats">
                <div className="stat">
                  <span className="stat-value">{campaign.total_opportunities || 0}</span>
                  <span className="stat-label">Opportunities</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{formatCurrency(campaign.total_value)}</span>
                  <span className="stat-label">Total Value</span>
                </div>
              </div>
              <div className="campaign-meta">
                Created {new Date(campaign.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Campaign Modal */}
      {showCreateCampaign && (
        <div className="modal-overlay" onClick={() => setShowCreateCampaign(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Campaign</h2>
              <button className="close-btn" onClick={() => setShowCreateCampaign(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateCampaign}>
              <div className="form-group">
                <label>Campaign Name *</label>
                <input
                  type="text"
                  value={newCampaign.name}
                  onChange={e => setNewCampaign({...newCampaign, name: e.target.value})}
                  placeholder="e.g., Q1 Sales Outreach"
                  required
                  data-testid="campaign-name-input"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newCampaign.description}
                  onChange={e => setNewCampaign({...newCampaign, description: e.target.value})}
                  placeholder="Campaign objectives and goals..."
                  rows={3}
                  data-testid="campaign-desc-input"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={newCampaign.start_date}
                    onChange={e => setNewCampaign({...newCampaign, start_date: e.target.value})}
                    data-testid="campaign-start-input"
                  />
                </div>
                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    value={newCampaign.end_date}
                    onChange={e => setNewCampaign({...newCampaign, end_date: e.target.value})}
                    data-testid="campaign-end-input"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Target Audience</label>
                <input
                  type="text"
                  value={newCampaign.target_audience}
                  onChange={e => setNewCampaign({...newCampaign, target_audience: e.target.value})}
                  placeholder="e.g., Small business owners in retail"
                  data-testid="campaign-audience-input"
                />
              </div>
              <div className="form-group">
                <label>Call Script</label>
                <textarea
                  value={newCampaign.call_script}
                  onChange={e => setNewCampaign({...newCampaign, call_script: e.target.value})}
                  placeholder="Enter the voice AI call script..."
                  rows={5}
                  data-testid="campaign-script-input"
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="cancel-btn" onClick={() => setShowCreateCampaign(false)}>Cancel</button>
                <button type="submit" className="submit-btn" data-testid="submit-campaign-btn">Create Campaign</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Campaign;
