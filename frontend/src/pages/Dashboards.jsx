import React, { useState, useEffect } from 'react';
import { Users, Phone, Clock, TrendingUp, CheckCircle, XCircle, PhoneCall, Calendar, BarChart3, PieChart, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import './Dashboards.css';

const Dashboards = () => {
  const [stats, setStats] = useState({
    totalContacts: 0,
    totalCalls: 0,
    totalDuration: 0,
    avgDuration: 0,
    conversionRate: 0,
    todayCalls: 0,
    weekCalls: 0,
    stageBreakdown: {}
  });
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // Fetch contacts for stage breakdown
      const contactsRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/contacts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      let contacts = [];
      if (contactsRes.ok) {
        const data = await contactsRes.json();
        contacts = data.contacts || [];
      }

      // Fetch calls for call stats
      const callsRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/sessions/calls`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      let callStats = { totalCalls: 0, totalDuration: 0, avgDuration: 0 };
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

      // Calculate conversion rate
      const totalDialed = contacts.length;
      const interested = stageBreakdown.interested + stageBreakdown.store_visit;
      const conversionRate = totalDialed > 0 ? Math.round((interested / totalDialed) * 100) : 0;

      setStats({
        totalContacts: contacts.length,
        totalCalls: callStats.totalCalls || 0,
        totalDuration: callStats.totalDuration || 0,
        avgDuration: callStats.avgDuration || 0,
        conversionRate,
        todayCalls: 0, // Would need date filtering
        weekCalls: callStats.totalCalls || 0,
        stageBreakdown
      });

    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0 mins';
    const mins = Math.floor(seconds / 60);
    return `${mins} mins`;
  };

  const getStageColor = (stage) => {
    const colors = {
      dialing: '#3B82F6',
      interested: '#10B981',
      not_interested: '#EF4444',
      callback: '#F59E0B',
      store_visit: '#8B5CF6',
      invalid_number: '#6B7280'
    };
    return colors[stage] || '#6B7280';
  };

  const getStageName = (stage) => {
    const names = {
      dialing: 'Dialing',
      interested: 'Interested',
      not_interested: 'Not Interested',
      callback: 'Call Back',
      store_visit: 'Store Visit',
      invalid_number: 'Invalid Number'
    };
    return names[stage] || stage;
  };

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  const maxStageCount = Math.max(...Object.values(stats.stageBreakdown), 1);

  return (
    <div className="dashboards-page" data-testid="dashboards-page">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Voice AI Campaign Performance Overview</p>
      </div>

      {/* KPI Cards Row 1 */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon blue">
            <Users size={24} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Total Contacts</span>
            <span className="kpi-value">{stats.totalContacts}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon green">
            <Phone size={24} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Total Calls Made</span>
            <span className="kpi-value">{stats.totalCalls}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon purple">
            <Clock size={24} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Total Call Duration</span>
            <span className="kpi-value">{formatDuration(stats.totalDuration)}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon orange">
            <TrendingUp size={24} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Conversion Rate</span>
            <span className="kpi-value">{stats.conversionRate}%</span>
            <span className="kpi-trend positive">
              <ArrowUpRight size={14} />
              Interested + Store Visit
            </span>
          </div>
        </div>
      </div>

      {/* KPI Cards Row 2 */}
      <div className="kpi-grid secondary">
        <div className="kpi-card small">
          <div className="kpi-icon-small cyan">
            <PhoneCall size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Avg Call Duration</span>
            <span className="kpi-value-small">{stats.avgDuration} secs</span>
          </div>
        </div>

        <div className="kpi-card small">
          <div className="kpi-icon-small green">
            <CheckCircle size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Interested</span>
            <span className="kpi-value-small">{stats.stageBreakdown.interested || 0}</span>
          </div>
        </div>

        <div className="kpi-card small">
          <div className="kpi-icon-small red">
            <XCircle size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Not Interested</span>
            <span className="kpi-value-small">{stats.stageBreakdown.not_interested || 0}</span>
          </div>
        </div>

        <div className="kpi-card small">
          <div className="kpi-icon-small yellow">
            <Calendar size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Call Backs Pending</span>
            <span className="kpi-value-small">{stats.stageBreakdown.callback || 0}</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        {/* Stage Breakdown */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><BarChart3 size={18} /> Contacts by Stage</h3>
          </div>
          <div className="chart-body">
            <div className="stage-bars">
              {Object.entries(stats.stageBreakdown).map(([stage, count]) => (
                <div key={stage} className="stage-bar-row">
                  <div className="stage-bar-label">
                    <span className="stage-dot" style={{ backgroundColor: getStageColor(stage) }}></span>
                    <span>{getStageName(stage)}</span>
                  </div>
                  <div className="stage-bar-wrapper">
                    <div 
                      className="stage-bar-fill" 
                      style={{ 
                        width: `${(count / maxStageCount) * 100}%`,
                        backgroundColor: getStageColor(stage)
                      }}
                    ></div>
                    <span className="stage-bar-count">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Funnel Overview */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><PieChart size={18} /> Conversion Funnel</h3>
          </div>
          <div className="chart-body">
            <div className="funnel-container">
              <div className="funnel-step">
                <div className="funnel-bar" style={{ width: '100%', backgroundColor: '#3B82F6' }}>
                  <span>Total Contacts</span>
                  <span>{stats.totalContacts}</span>
                </div>
              </div>
              <div className="funnel-step">
                <div className="funnel-bar" style={{ 
                  width: stats.totalContacts ? `${((stats.stageBreakdown.interested + stats.stageBreakdown.callback + stats.stageBreakdown.store_visit) / stats.totalContacts) * 100}%` : '0%', 
                  backgroundColor: '#10B981' 
                }}>
                  <span>Engaged</span>
                  <span>{(stats.stageBreakdown.interested || 0) + (stats.stageBreakdown.callback || 0) + (stats.stageBreakdown.store_visit || 0)}</span>
                </div>
              </div>
              <div className="funnel-step">
                <div className="funnel-bar" style={{ 
                  width: stats.totalContacts ? `${((stats.stageBreakdown.interested + stats.stageBreakdown.store_visit) / stats.totalContacts) * 100}%` : '0%', 
                  backgroundColor: '#8B5CF6' 
                }}>
                  <span>Converted</span>
                  <span>{(stats.stageBreakdown.interested || 0) + (stats.stageBreakdown.store_visit || 0)}</span>
                </div>
              </div>
            </div>
            <div className="funnel-legend">
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#3B82F6' }}></span>
                <span>Total Contacts</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#10B981' }}></span>
                <span>Engaged (Interested + Callback + Store Visit)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#8B5CF6' }}></span>
                <span>Converted (Interested + Store Visit)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="quick-stat-item">
          <span className="quick-stat-label">In Dialing Queue</span>
          <span className="quick-stat-value">{stats.stageBreakdown.dialing || 0}</span>
        </div>
        <div className="quick-stat-divider"></div>
        <div className="quick-stat-item">
          <span className="quick-stat-label">Invalid Numbers</span>
          <span className="quick-stat-value">{stats.stageBreakdown.invalid_number || 0}</span>
        </div>
        <div className="quick-stat-divider"></div>
        <div className="quick-stat-item">
          <span className="quick-stat-label">Store Visits Scheduled</span>
          <span className="quick-stat-value">{stats.stageBreakdown.store_visit || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default Dashboards;
