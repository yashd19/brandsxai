import React, { useState, useEffect } from 'react';
import { Plus, X, ArrowLeft, Phone, Mail, Building2, User, MessageSquare, Calendar, Trash2, Search, Filter, ArrowUpDown, LayoutGrid, List, Settings, Clock, Download, Play, FileText, ChevronDown, Upload, Zap } from 'lucide-react';
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
  const [showOpportunityDetail, setShowOpportunityDetail] = useState(null);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [draggedOpp, setDraggedOpp] = useState(null);
  const [viewMode, setViewMode] = useState('board');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ stage: 'all', hasRecording: 'all' });
  const [allOpportunities, setAllOpportunities] = useState([]);
  const [csvData, setCsvData] = useState([]);
  const [importStatus, setImportStatus] = useState(null);

  const [newCampaign, setNewCampaign] = useState({
    name: '', description: '', start_date: '', end_date: '', target_audience: '', call_script: ''
  });

  const [newOpportunity, setNewOpportunity] = useState({
    name: '', phone: '', email: '', business_name: '', notes: ''
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
        
        const allOpps = [];
        Object.entries(data.stages || {}).forEach(([stageName, stageData]) => {
          (stageData.opportunities || []).forEach(opp => {
            allOpps.push({ ...opp, stageName });
          });
        });
        setAllOpportunities(allOpps);
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
        setNewOpportunity({ name: '', phone: '', email: '', business_name: '', notes: '' });
        fetchCampaignDetails(selectedCampaign.id);
      }
    } catch (err) {
      console.error('Error creating opportunity:', err);
    }
  };

  const handleCSVUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
      
      const data = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const row = {};
        headers.forEach((header, idx) => {
          row[header] = values[idx] || '';
        });
        if (row.name || row.phone) {
          data.push({
            name: row.name || `Lead_${Date.now()}_${i}`,
            phone: row.phone || '',
            email: row.email || '',
            business_name: row.business_name || row.business || row.company || '',
            notes: row.notes || ''
          });
        }
      }
      setCsvData(data);
      setImportStatus(null);
    };
    reader.readAsText(file);
  };

  const handleBulkImport = async () => {
    if (csvData.length === 0) return;
    
    setImportStatus({ importing: true, success: 0, failed: 0 });
    let success = 0;
    let failed = 0;

    for (const lead of csvData) {
      try {
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${selectedCampaign.id}/opportunities`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(lead)
        });
        if (res.ok) success++;
        else failed++;
      } catch {
        failed++;
      }
    }

    setImportStatus({ importing: false, success, failed });
    if (success > 0) {
      fetchCampaignDetails(selectedCampaign.id);
    }
  };

  const handleTriggerAICalls = async () => {
    // Placeholder for AI calling integration
    alert('AI Calling feature will be integrated soon. This will trigger automated calls for all leads in the Dialing stage.');
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

  const handleOpportunityClick = (e, opp) => {
    e.stopPropagation();
    setShowOpportunityDetail(opp);
  };

  const getInitials = (name) => {
    if (!name) return 'A';
    const parts = name.split(/[_\s]+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStageColor = (stageId) => {
    const stage = STAGES.find(s => s.id === stageId);
    return stage?.color || '#6B7280';
  };

  const getStageName = (stageId) => {
    const stage = STAGES.find(s => s.id === stageId);
    return stage?.name || stageId;
  };

  const filterOpportunities = (opportunities) => {
    return opportunities.filter(opp => {
      if (searchQuery && !opp.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (filters.stage !== 'all' && opp.stage !== filters.stage) {
        return false;
      }
      if (filters.hasRecording === 'yes' && !opp.recording_url) {
        return false;
      }
      if (filters.hasRecording === 'no' && opp.recording_url) {
        return false;
      }
      return true;
    });
  };

  const getFilteredStages = () => {
    const filtered = {};
    STAGES.forEach(stage => {
      const opps = (stages[stage.id]?.opportunities || []).filter(opp => {
        if (searchQuery && !opp.name.toLowerCase().includes(searchQuery.toLowerCase())) {
          return false;
        }
        return true;
      });
      filtered[stage.id] = {
        ...stages[stage.id],
        opportunities: opps,
        count: opps.length
      };
    });
    return filtered;
  };

  if (loading) {
    return <div className="campaign-loading">Loading campaigns...</div>;
  }

  // Campaign Pipeline View
  if (selectedCampaign) {
    const filteredStages = getFilteredStages();
    const filteredAllOpps = filterOpportunities(allOpportunities);
    const dialingCount = stages.dialing?.count || 0;

    return (
      <div className="campaign-pipeline" data-testid="campaign-pipeline">
        <div className="pipeline-header">
          <div className="header-left-section">
            <button className="back-btn" onClick={() => setSelectedCampaign(null)} data-testid="back-to-campaigns">
              <ArrowLeft size={20} />
              Back to Campaigns
            </button>
            <div className="pipeline-title">
              <h2>{selectedCampaign.name}</h2>
              <span className="campaign-status">{selectedCampaign.status}</span>
            </div>
          </div>
          <div className="header-actions">
            <button className="import-btn" onClick={() => setShowBulkImport(true)} data-testid="bulk-import-btn">
              <Upload size={18} />
              Import CSV
            </button>
            <button className="add-opp-btn" onClick={() => setShowCreateOpportunity(true)} data-testid="add-opportunity-btn">
              <Plus size={18} />
              Add Opportunity
            </button>
          </div>
        </div>

        {/* Controls Bar */}
        <div className="pipeline-controls">
          <div className="controls-left">
            <div className="view-toggle">
              <button 
                className={viewMode === 'board' ? 'active' : ''} 
                onClick={() => setViewMode('board')}
                data-testid="view-board-btn"
              >
                <LayoutGrid size={16} />
                All
              </button>
              <button 
                className={viewMode === 'list' ? 'active' : ''} 
                onClick={() => setViewMode('list')}
                data-testid="view-list-btn"
              >
                <List size={16} />
                List
              </button>
            </div>
            {/* Filters only in list view */}
            {viewMode === 'list' && (
              <>
                <div className="filter-dropdown-container">
                  <button 
                    className={`filter-btn ${showFilters ? 'active' : ''}`}
                    onClick={() => setShowFilters(!showFilters)}
                    data-testid="advanced-filters-btn"
                  >
                    <Filter size={16} />
                    Advanced Filters
                    <ChevronDown size={14} />
                  </button>
                  {showFilters && (
                    <div className="filter-dropdown" data-testid="filter-dropdown">
                      <div className="filter-section">
                        <label>Stage</label>
                        <select 
                          value={filters.stage} 
                          onChange={(e) => setFilters({...filters, stage: e.target.value})}
                        >
                          <option value="all">All Stages</option>
                          {STAGES.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                          ))}
                        </select>
                      </div>
                      <div className="filter-section">
                        <label>Has Recording</label>
                        <select 
                          value={filters.hasRecording} 
                          onChange={(e) => setFilters({...filters, hasRecording: e.target.value})}
                        >
                          <option value="all">All</option>
                          <option value="yes">With Recording</option>
                          <option value="no">Without Recording</option>
                        </select>
                      </div>
                      <button 
                        className="clear-filters-btn"
                        onClick={() => setFilters({ stage: 'all', hasRecording: 'all' })}
                      >
                        Clear Filters
                      </button>
                    </div>
                  )}
                </div>
                <button className="sort-btn">
                  <ArrowUpDown size={16} />
                  Sort
                </button>
              </>
            )}
          </div>
          <div className="controls-right">
            <div className="search-box">
              <Search size={16} />
              <input 
                type="text" 
                placeholder="Search Opportunities" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="search-opportunities"
              />
            </div>
          </div>
        </div>

        {/* Board View */}
        {viewMode === 'board' && (
          <>
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
                      <span className="opp-count">{filteredStages[stage.id]?.count || 0} Opportunities</span>
                    </div>
                  </div>
                  <div className="column-cards">
                    {(filteredStages[stage.id]?.opportunities || []).map(opp => (
                      <div
                        key={opp.id}
                        className="opportunity-card"
                        draggable
                        onDragStart={(e) => handleDragStart(e, opp, stage.id)}
                        onDragEnd={handleDragEnd}
                        onClick={(e) => handleOpportunityClick(e, opp)}
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
                        {opp.recording_url && (
                          <div className="card-info recording-badge">
                            <Play size={14} />
                            <span>Has Recording</span>
                          </div>
                        )}
                        <div className="card-actions">
                          <button className="action-btn" title="Call"><Phone size={16} /></button>
                          <button className="action-btn" title="Contact"><User size={16} /></button>
                          <button className="action-btn active" title="Message"><MessageSquare size={16} /></button>
                          <button className="action-btn active" title="Schedule"><Calendar size={16} /></button>
                          <button className="action-btn active" title="Email"><Mail size={16} /></button>
                          <button className="action-btn" title="Delete"><Trash2 size={16} /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* AI Trigger Button */}
            {dialingCount > 0 && (
              <div className="ai-trigger-section">
                <button className="ai-trigger-btn" onClick={handleTriggerAICalls} data-testid="trigger-ai-btn">
                  <Zap size={20} />
                  Trigger AI Calls ({dialingCount} leads in Dialing)
                </button>
                <p className="ai-trigger-hint">Click to initiate automated AI voice calls for all leads in the Dialing stage</p>
              </div>
            )}
          </>
        )}

        {/* List View */}
        {viewMode === 'list' && (
          <div className="pipeline-list" data-testid="list-view">
            <table className="opportunities-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Business</th>
                  <th>Phone</th>
                  <th>Stage</th>
                  <th>Recording</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAllOpps.map(opp => (
                  <tr key={opp.id} onClick={(e) => handleOpportunityClick(e, opp)} className="clickable-row">
                    <td>
                      <div className="list-name-cell">
                        <div className="list-avatar">{getInitials(opp.name)}</div>
                        <span>{opp.name}</span>
                      </div>
                    </td>
                    <td>{opp.business_name || '-'}</td>
                    <td>{opp.phone || '-'}</td>
                    <td>
                      <span className="stage-badge" style={{ backgroundColor: getStageColor(opp.stage) }}>
                        {getStageName(opp.stage)}
                      </span>
                    </td>
                    <td>
                      {opp.recording_url ? (
                        <span className="has-recording"><Play size={14} /> Yes</span>
                      ) : (
                        <span className="no-recording">No</span>
                      )}
                    </td>
                    <td>{formatDate(opp.updated_at)}</td>
                    <td>
                      <div className="list-actions">
                        <button className="action-btn" title="Call"><Phone size={14} /></button>
                        <button className="action-btn" title="Email"><Mail size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredAllOpps.length === 0 && (
              <div className="empty-list">No opportunities match your filters</div>
            )}
          </div>
        )}

        {/* Opportunity Detail Modal */}
        {showOpportunityDetail && (
          <div className="modal-overlay" onClick={() => setShowOpportunityDetail(null)}>
            <div className="modal detail-modal" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <div className="detail-header-info">
                  <div className="detail-avatar" style={{ backgroundColor: getStageColor(showOpportunityDetail.stage) }}>
                    {getInitials(showOpportunityDetail.name)}
                  </div>
                  <div>
                    <h2>{showOpportunityDetail.name}</h2>
                    <span className="stage-badge" style={{ backgroundColor: getStageColor(showOpportunityDetail.stage) }}>
                      {getStageName(showOpportunityDetail.stage)}
                    </span>
                  </div>
                </div>
                <button className="close-btn" onClick={() => setShowOpportunityDetail(null)}>
                  <X size={20} />
                </button>
              </div>
              
              <div className="detail-content">
                <div className="detail-section">
                  <h3><User size={16} /> Contact Information</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Phone</label>
                      <span>{showOpportunityDetail.phone || 'Not provided'}</span>
                    </div>
                    <div className="detail-item">
                      <label>Email</label>
                      <span>{showOpportunityDetail.email || 'Not provided'}</span>
                    </div>
                    <div className="detail-item">
                      <label>Business Name</label>
                      <span>{showOpportunityDetail.business_name || 'Not provided'}</span>
                    </div>
                    <div className="detail-item">
                      <label>Created</label>
                      <span>{formatDate(showOpportunityDetail.created_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3><Phone size={16} /> Call Recording</h3>
                  {showOpportunityDetail.recording_url ? (
                    <div className="recording-section">
                      <div className="recording-player">
                        <audio controls src={showOpportunityDetail.recording_url} className="audio-player">
                          Your browser does not support the audio element.
                        </audio>
                      </div>
                      <div className="recording-meta">
                        <div className="detail-item">
                          <label>Duration</label>
                          <span>{formatDuration(showOpportunityDetail.call_duration)}</span>
                        </div>
                        <div className="detail-item">
                          <label>Last Called</label>
                          <span>{formatDate(showOpportunityDetail.last_called_at)}</span>
                        </div>
                        <div className="detail-item">
                          <label>Call Outcome</label>
                          <span>{showOpportunityDetail.call_outcome || 'Not specified'}</span>
                        </div>
                      </div>
                      <a 
                        href={showOpportunityDetail.recording_url} 
                        download 
                        className="download-btn"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Download size={16} />
                        Download Recording
                      </a>
                    </div>
                  ) : (
                    <div className="no-recording-placeholder">
                      <Phone size={32} />
                      <p>No call recording available</p>
                      <span>Recording will appear here after a call is made</span>
                    </div>
                  )}
                </div>

                <div className="detail-section">
                  <h3><FileText size={16} /> AI Call Summary</h3>
                  {showOpportunityDetail.call_summary ? (
                    <div className="call-summary-box">
                      <p>{showOpportunityDetail.call_summary}</p>
                    </div>
                  ) : (
                    <div className="no-summary-placeholder">
                      <FileText size={32} />
                      <p>No call summary available</p>
                      <span>AI-generated summary will appear here after call analysis</span>
                    </div>
                  )}
                </div>

                <div className="detail-section">
                  <h3><MessageSquare size={16} /> Notes</h3>
                  <div className="notes-box">
                    {showOpportunityDetail.notes || 'No notes added'}
                  </div>
                </div>

                <div className="detail-section">
                  <h3><Clock size={16} /> Activity Timeline</h3>
                  <div className="timeline">
                    <div className="timeline-item">
                      <div className="timeline-dot"></div>
                      <div className="timeline-content">
                        <span className="timeline-time">{formatDate(showOpportunityDetail.updated_at)}</span>
                        <p>Status changed to <strong>{getStageName(showOpportunityDetail.stage)}</strong></p>
                      </div>
                    </div>
                    <div className="timeline-item">
                      <div className="timeline-dot"></div>
                      <div className="timeline-content">
                        <span className="timeline-time">{formatDate(showOpportunityDetail.created_at)}</span>
                        <p>Opportunity created</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Import Modal */}
        {showBulkImport && (
          <div className="modal-overlay" onClick={() => setShowBulkImport(false)}>
            <div className="modal import-modal" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Import Leads from CSV</h2>
                <button className="close-btn" onClick={() => setShowBulkImport(false)}>
                  <X size={20} />
                </button>
              </div>
              <div className="import-content">
                <div className="import-instructions">
                  <h4>CSV Format Requirements:</h4>
                  <p>Your CSV should have columns: <code>name, phone, email, business_name, notes</code></p>
                  <p>Only <code>name</code> or <code>phone</code> is required. Other fields are optional.</p>
                </div>
                
                <div className="file-upload-area">
                  <input 
                    type="file" 
                    accept=".csv" 
                    onChange={handleCSVUpload}
                    id="csv-upload"
                    data-testid="csv-file-input"
                  />
                  <label htmlFor="csv-upload" className="upload-label">
                    <Upload size={32} />
                    <span>Click to upload CSV or drag & drop</span>
                  </label>
                </div>

                {csvData.length > 0 && (
                  <div className="csv-preview">
                    <h4>Preview ({csvData.length} leads)</h4>
                    <div className="preview-table-wrapper">
                      <table className="preview-table">
                        <thead>
                          <tr>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Business</th>
                          </tr>
                        </thead>
                        <tbody>
                          {csvData.slice(0, 5).map((row, idx) => (
                            <tr key={idx}>
                              <td>{row.name}</td>
                              <td>{row.phone || '-'}</td>
                              <td>{row.email || '-'}</td>
                              <td>{row.business_name || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {csvData.length > 5 && <p className="more-rows">...and {csvData.length - 5} more rows</p>}
                    </div>
                  </div>
                )}

                {importStatus && (
                  <div className={`import-status ${importStatus.importing ? 'importing' : importStatus.failed > 0 ? 'partial' : 'success'}`}>
                    {importStatus.importing ? (
                      <p>Importing leads...</p>
                    ) : (
                      <p>
                        Import complete: {importStatus.success} successful, {importStatus.failed} failed
                      </p>
                    )}
                  </div>
                )}

                <div className="modal-actions">
                  <button type="button" className="cancel-btn" onClick={() => setShowBulkImport(false)}>Cancel</button>
                  <button 
                    type="button" 
                    className="submit-btn" 
                    onClick={handleBulkImport}
                    disabled={csvData.length === 0 || importStatus?.importing}
                    data-testid="import-leads-btn"
                  >
                    <Upload size={16} />
                    Import {csvData.length} Leads
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

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
                    placeholder="e.g., John Smith"
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
                <h3 className="campaign-title">{campaign.name}</h3>
                <span className={`status-badge ${campaign.status}`}>{campaign.status}</span>
              </div>
              <p className="campaign-desc">{campaign.description || 'No description'}</p>
              <div className="campaign-stats">
                <div className="stat">
                  <span className="stat-value">{campaign.total_opportunities || 0}</span>
                  <span className="stat-label">Opportunities</span>
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
