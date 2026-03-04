import React, { useState, useEffect } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';
import './Dashboards.css';

const Dashboards = () => {
  const [stats, setStats] = useState({
    totalContacts: 0,
    totalCalls: 0,
    totalDuration: 0,
    avgDuration: 0,
    successRate: 0,
    stageBreakdown: {},
    campaigns: []
  });
  const [loading, setLoading] = useState(true);
  const [showParticipants, setShowParticipants] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    
    const loadData = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      let contacts = [];
      let campaigns = [];
      let callStats = { totalCalls: 0, totalDuration: 0, avgDuration: 0 };

      try {
        const fetchOptions = { headers: { 'Authorization': `Bearer ${token}` } };
        
        const [contactsRes, campaignsRes, callsRes] = await Promise.all([
          fetch(`${process.env.REACT_APP_BACKEND_URL}/api/contacts`, fetchOptions),
          fetch(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns`, fetchOptions),
          fetch(`${process.env.REACT_APP_BACKEND_URL}/api/sessions/calls`, fetchOptions)
        ]);

        // Process contacts
        if (contactsRes.ok) {
          const data = await contactsRes.json();
          contacts = data.contacts || [];
        }

        // Process campaigns
        if (campaignsRes.ok) {
          const campaignsData = await campaignsRes.json();
          campaigns = campaignsData.campaigns || [];
        }

        // Process call stats
        if (callsRes.ok) {
          const callData = await callsRes.json();
          callStats = callData.stats || callStats;
        }

        // Calculate stage breakdown
        const stageBreakdown = {
          dialing: 0,
          interested: 0,
          not_interested: 0,
          callback: 0,
          store_visit: 0,
          invalid_number: 0
        };
        
        contacts.forEach(c => {
          if (stageBreakdown.hasOwnProperty(c.stage)) {
            stageBreakdown[c.stage]++;
          }
        });

        // Calculate success rate
        const totalAttempted = contacts.length - stageBreakdown.dialing;
        const connected = stageBreakdown.interested + stageBreakdown.callback + stageBreakdown.store_visit + stageBreakdown.not_interested;
        const successRate = totalAttempted > 0 ? Math.round((connected / totalAttempted) * 1000) / 10 : 0;

        setStats({
          totalContacts: contacts.length,
          totalCalls: callStats.totalCalls || 0,
          totalDuration: callStats.totalDuration || 0,
          avgDuration: callStats.avgDuration || 0,
          successRate,
          stageBreakdown,
          campaigns: campaigns.slice(0, 5)
        });
      } catch (err) {
        console.error('Dashboard stats error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Donut Chart SVG Component
  const DonutChart = ({ data, size = 160, strokeWidth = 20 }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const center = size / 2;
    
    const total = data.reduce((sum, item) => sum + item.value, 0);
    let currentAngle = -90; // Start from top
    
    const segments = data.map((item, index) => {
      const percentage = total > 0 ? item.value / total : 0;
      const strokeDasharray = `${percentage * circumference} ${circumference}`;
      const rotation = currentAngle;
      currentAngle += percentage * 360;
      
      return (
        <circle
          key={index}
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={item.color}
          strokeWidth={strokeWidth}
          strokeDasharray={strokeDasharray}
          strokeLinecap="round"
          transform={`rotate(${rotation} ${center} ${center})`}
          style={{ transition: 'stroke-dasharray 0.5s ease' }}
        />
      );
    });

    return (
      <svg width={size} height={size} className="donut-chart">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={strokeWidth}
        />
        {segments}
      </svg>
    );
  };

  // Gauge Chart Component
  const GaugeChart = ({ percentage, size = 180 }) => {
    const strokeWidth = 12;
    const radius = (size - strokeWidth) / 2 - 10;
    const circumference = Math.PI * radius; // Semi-circle
    const center = size / 2;
    const fillPercentage = (percentage / 100) * circumference;
    
    return (
      <div className="gauge-container">
        <svg width={size} height={size / 2 + 30} className="gauge-chart">
          {/* Background arc */}
          <path
            d={`M ${strokeWidth} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${center}`}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Filled arc */}
          <path
            d={`M ${strokeWidth} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${center}`}
            fill="none"
            stroke="#06B6D4"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${fillPercentage} ${circumference}`}
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        </svg>
        <div className="gauge-value">
          <span className="gauge-number">{percentage}</span>
          <span className="gauge-percent">%</span>
        </div>
        <div className="gauge-minigraph">
          <svg viewBox="0 0 100 30" className="minigraph">
            <polyline
              points="0,25 15,20 25,22 35,15 45,18 55,10 65,12 75,8 85,5 100,8"
              fill="none"
              stroke="#06B6D4"
              strokeWidth="2"
            />
            <circle cx="100" cy="8" r="3" fill="#06B6D4" />
          </svg>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  // Prepare chart data
  const outcomeData = [
    { label: 'Interested', value: stats.stageBreakdown.interested || 0, color: '#06B6D4' },
    { label: 'Not Interested', value: stats.stageBreakdown.not_interested || 0, color: '#A855F7' },
    { label: 'Callback', value: stats.stageBreakdown.callback || 0, color: '#F59E0B' },
    { label: 'Store Visit', value: stats.stageBreakdown.store_visit || 0, color: '#10B981' }
  ].filter(d => d.value > 0);

  const statusData = [
    { label: 'Completed', value: (stats.stageBreakdown.interested || 0) + (stats.stageBreakdown.not_interested || 0) + (stats.stageBreakdown.store_visit || 0), color: '#06B6D4' },
    { label: 'Pending', value: (stats.stageBreakdown.dialing || 0) + (stats.stageBreakdown.callback || 0), color: '#A855F7' },
    { label: 'Failed', value: stats.stageBreakdown.invalid_number || 0, color: '#EF4444' }
  ].filter(d => d.value > 0);

  const stageMinutesData = [
    { label: 'Interested Calls', value: (stats.stageBreakdown.interested || 0) * 3, color: '#06B6D4' },
    { label: 'Callback Calls', value: (stats.stageBreakdown.callback || 0) * 2, color: '#A855F7' },
    { label: 'Other Calls', value: (stats.stageBreakdown.not_interested || 0) * 1, color: '#F59E0B' }
  ];

  const totalMins = Math.round(stats.totalDuration / 60) || Math.round(stageMinutesData.reduce((s, d) => s + d.value, 0));

  return (
    <div className="dashboards-page" data-testid="dashboards-page">
      {/* Top Stats Row */}
      <div className="stats-grid-top">
        {/* Call Success Rate */}
        <div className="stat-card gauge-card">
          <div className="stat-header">
            <span>CALL SUCCESS RATE</span>
            <Info size={14} />
          </div>
          <GaugeChart percentage={stats.successRate || 0} />
        </div>

        {/* Call Outcomes */}
        <div className="stat-card donut-card">
          <div className="stat-header">
            <span>CALL OUTCOMES</span>
            <Info size={14} />
          </div>
          <div className="donut-content">
            <DonutChart data={outcomeData.length > 0 ? outcomeData : [{ value: 1, color: '#E5E7EB' }]} />
            <div className="donut-legend">
              {outcomeData.map((item, idx) => (
                <div key={idx} className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: item.color }}></span>
                  <span className="legend-label">{item.label}</span>
                  <span className="legend-value">{Math.round((item.value / (outcomeData.reduce((s, d) => s + d.value, 0) || 1)) * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Call Status */}
        <div className="stat-card donut-card">
          <div className="stat-header">
            <span>CALL STATUS</span>
            <Info size={14} />
          </div>
          <div className="donut-content">
            <DonutChart data={statusData.length > 0 ? statusData : [{ value: 1, color: '#E5E7EB' }]} />
            <div className="donut-legend">
              {statusData.map((item, idx) => (
                <div key={idx} className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: item.color }}></span>
                  <span className="legend-label">{item.label}</span>
                  <span className="legend-value">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Campaigns */}
        <div className="stat-card table-card">
          <div className="stat-header">
            <span>TOP CAMPAIGNS</span>
            <Info size={14} />
          </div>
          <div className="campaign-table">
            <div className="table-header-row">
              <span>#</span>
              <span>NAME</span>
              <span>COUNT</span>
            </div>
            {stats.campaigns.length > 0 ? (
              stats.campaigns.map((campaign, idx) => (
                <div key={idx} className="table-row">
                  <span className="row-num">{idx + 1}</span>
                  <span className="row-name">{campaign.name}</span>
                  <span className="row-count">{campaign.total_opportunities || 0}</span>
                </div>
              ))
            ) : (
              <div className="table-empty">No campaigns yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Participants Section */}
      <div className="section-header" onClick={() => setShowParticipants(!showParticipants)}>
        {showParticipants ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
        <span>Contacts</span>
      </div>

      {showParticipants && (
        <div className="stats-grid-bottom">
          {/* Total Call Minutes */}
          <div className="stat-card large-number-card">
            <div className="stat-header">
              <span>TOTAL CALL MINUTES</span>
              <Info size={14} />
            </div>
            <div className="large-number">
              <span className="number-value">{totalMins}</span>
              <span className="number-unit">mins</span>
            </div>
          </div>

          {/* Call Minutes by Stage */}
          <div className="stat-card donut-card wide">
            <div className="stat-header">
              <span>CONTACTS BY STAGE</span>
              <Info size={14} />
            </div>
            <div className="donut-content wide">
              <DonutChart 
                data={[
                  { value: stats.stageBreakdown.dialing || 0, color: '#3B82F6' },
                  { value: stats.stageBreakdown.interested || 0, color: '#06B6D4' },
                  { value: stats.stageBreakdown.not_interested || 0, color: '#A855F7' },
                  { value: stats.stageBreakdown.callback || 0, color: '#F59E0B' },
                  { value: stats.stageBreakdown.store_visit || 0, color: '#10B981' },
                  { value: stats.stageBreakdown.invalid_number || 0, color: '#6B7280' }
                ].filter(d => d.value > 0).length > 0 ? [
                  { value: stats.stageBreakdown.dialing || 0, color: '#3B82F6' },
                  { value: stats.stageBreakdown.interested || 0, color: '#06B6D4' },
                  { value: stats.stageBreakdown.not_interested || 0, color: '#A855F7' },
                  { value: stats.stageBreakdown.callback || 0, color: '#F59E0B' },
                  { value: stats.stageBreakdown.store_visit || 0, color: '#10B981' },
                  { value: stats.stageBreakdown.invalid_number || 0, color: '#6B7280' }
                ] : [{ value: 1, color: '#E5E7EB' }]}
                size={180}
                strokeWidth={24}
              />
              <div className="donut-legend vertical">
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#3B82F6' }}></span>
                  <span className="legend-label">Dialing</span>
                  <span className="legend-value">{stats.stageBreakdown.dialing || 0}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#06B6D4' }}></span>
                  <span className="legend-label">Interested</span>
                  <span className="legend-value">{stats.stageBreakdown.interested || 0}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#A855F7' }}></span>
                  <span className="legend-label">Not Interested</span>
                  <span className="legend-value">{stats.stageBreakdown.not_interested || 0}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#F59E0B' }}></span>
                  <span className="legend-label">Callback</span>
                  <span className="legend-value">{stats.stageBreakdown.callback || 0}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#10B981' }}></span>
                  <span className="legend-label">Store Visit</span>
                  <span className="legend-value">{stats.stageBreakdown.store_visit || 0}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#6B7280' }}></span>
                  <span className="legend-label">Invalid</span>
                  <span className="legend-value">{stats.stageBreakdown.invalid_number || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="quick-stats-row">
        <div className="quick-stat">
          <span className="quick-label">Total Contacts</span>
          <span className="quick-value">{stats.totalContacts}</span>
        </div>
        <div className="quick-stat">
          <span className="quick-label">In Queue</span>
          <span className="quick-value cyan">{stats.stageBreakdown.dialing || 0}</span>
        </div>
        <div className="quick-stat">
          <span className="quick-label">Converted</span>
          <span className="quick-value green">{(stats.stageBreakdown.interested || 0) + (stats.stageBreakdown.store_visit || 0)}</span>
        </div>
        <div className="quick-stat">
          <span className="quick-label">Avg Duration</span>
          <span className="quick-value">{stats.avgDuration || 0}s</span>
        </div>
      </div>
    </div>
  );
};

export default Dashboards;
