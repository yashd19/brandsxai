import React, { useState, useEffect } from 'react';
import { Phone, PhoneOutgoing, Clock, AlertTriangle, Filter, Search, Info, QrCode, ExternalLink } from 'lucide-react';
import './Session.css';

const Session = () => {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [sortField, setSortField] = useState('started_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Stats
  const [stats, setStats] = useState({
    totalCalls: 0,
    totalDuration: 0,
    avgDuration: 0,
    activeCalls: 0,
    callsWithIssues: 0
  });

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchCalls();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchCalls, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchCalls = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/sessions/calls`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCalls(data.calls || []);
        setStats(data.stats || {
          totalCalls: data.calls?.length || 0,
          totalDuration: data.calls?.reduce((acc, c) => acc + (c.duration || 0), 0) || 0,
          avgDuration: 0,
          activeCalls: data.calls?.filter(c => c.status === 'active').length || 0,
          callsWithIssues: data.calls?.filter(c => c.has_issue).length || 0
        });
      }
    } catch (err) {
      console.error('Error fetching calls:', err);
      // Use mock data for demo
      generateMockData();
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = () => {
    const mockCalls = [
      {
        id: 'SCL_tcncF53maTxW',
        from: '+911171366938',
        to: '+919896529723',
        direction: 'Outbound',
        started_at: '2026-02-28T05:24:59',
        ended_at: '2026-02-28T05:25:51',
        duration: 52,
        session: 'outbound_call_e78dc9b1e7df',
        status: 'completed'
      },
      {
        id: 'SCL_JKorxRn9UUhj',
        from: '+911171366938',
        to: '+919896529723',
        direction: 'Outbound',
        started_at: '2026-02-28T05:24:06',
        ended_at: '2026-02-28T05:27:54',
        duration: 228,
        session: 'outbound_call_7261d2b57467',
        status: 'completed'
      },
      {
        id: 'SCL_YwBZQi68E3w7',
        from: '+911171366938',
        to: '+919896529723',
        direction: 'Outbound',
        started_at: '2026-02-28T05:19:40',
        ended_at: '2026-02-28T05:20:33',
        duration: 53,
        session: 'outbound_call_2d10829e510a',
        status: 'completed'
      },
      {
        id: 'SCL_2LVFEzc6TZAt',
        from: '+911171366938',
        to: '+918928646605',
        direction: 'Outbound',
        started_at: '2026-02-28T05:17:19',
        ended_at: '2026-02-28T05:18:38',
        duration: 79,
        session: 'outbound_call_6367f91631ff',
        status: 'completed'
      },
      {
        id: 'SCL_u3EnRMMZKeWK',
        from: '+911171366938',
        to: '+919702375326',
        direction: 'Outbound',
        started_at: '2026-02-28T05:12:45',
        ended_at: '2026-02-28T05:13:53',
        duration: 68,
        session: 'outbound_call_aca46da113c0',
        status: 'completed'
      },
      {
        id: 'SCL_EdWCtVntGSCh',
        from: '+911171366938',
        to: '+917977606844',
        direction: 'Outbound',
        started_at: '2026-02-28T05:10:20',
        ended_at: '2026-02-28T05:11:39',
        duration: 79,
        session: 'outbound_call_9288cbe63544',
        status: 'completed'
      },
      {
        id: 'SCL_rJ3YFnirV7v7',
        from: '+911171366938',
        to: '+918380835616',
        direction: 'Outbound',
        started_at: '2026-02-28T05:05:47',
        ended_at: '2026-02-28T05:08:15',
        duration: 148,
        session: 'outbound_call_8abe0f37da15',
        status: 'completed'
      },
      {
        id: 'SCL_Fq6PfFufpMr7',
        from: '+911171366938',
        to: '+919896529723',
        direction: 'Outbound',
        started_at: '2026-02-28T05:02:58',
        ended_at: '2026-02-28T05:03:30',
        duration: 32,
        session: 'outbound_call_1932c930c706',
        status: 'completed'
      }
    ];

    setCalls(mockCalls);
    const totalDuration = mockCalls.reduce((acc, c) => acc + (c.duration || 0), 0);
    setStats({
      totalCalls: mockCalls.length,
      totalDuration,
      avgDuration: Math.round(totalDuration / mockCalls.length),
      activeCalls: 9, // Mock active calls
      callsWithIssues: 0
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds} secs`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (secs === 0) return `${mins} mins`;
    return `${mins} mins`;
  };

  const formatTotalDuration = (seconds) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    return `${mins} mins`;
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }) + ', ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const sortedCalls = [...calls].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    if (sortField === 'started_at' || sortField === 'ended_at') {
      aVal = new Date(aVal).getTime();
      bVal = new Date(bVal).getTime();
    }
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    }
    return aVal < bVal ? 1 : -1;
  });

  const filteredCalls = sortedCalls.filter(call => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      call.id.toLowerCase().includes(query) ||
      call.from.includes(query) ||
      call.to.includes(query) ||
      call.session.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return <div className="session-loading">Loading session data...</div>;
  }

  return (
    <div className="session-page" data-testid="session-page">
      {/* Stats Cards */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-header">
            <span>TOTAL CALLS</span>
            <Info size={14} />
          </div>
          <div className="stat-value">-</div>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span>TOTAL CALL DURATION</span>
            <Info size={14} />
          </div>
          <div className="stat-value">{formatTotalDuration(stats.totalDuration)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span>AVERAGE CALL DURATION</span>
            <Info size={14} />
          </div>
          <div className="stat-value">{stats.avgDuration} secs</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        <div className="chart-card">
          <div className="chart-header">
            <span>ACTIVE CALLS</span>
            <Info size={14} />
          </div>
          <div className="chart-body">
            <div className="chart-value cyan">{stats.activeCalls}</div>
            <div className="mini-chart">
              <svg viewBox="0 0 400 100" className="line-chart">
                <defs>
                  <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity="0.2" />
                    <stop offset="50%" stopColor="#2563eb" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                <path
                  d="M0,80 L50,80 L80,60 L120,50 L160,45 L200,42 L240,42 L280,42 L320,42 L360,45 L400,60"
                  fill="none"
                  stroke="url(#lineGradient)"
                  strokeWidth="2"
                />
                <circle cx="400" cy="60" r="4" fill="#2563eb" />
              </svg>
            </div>
          </div>
        </div>
        <div className="chart-card">
          <div className="chart-header">
            <span>CALLS WITH ISSUES</span>
            <Info size={14} />
          </div>
          <div className="chart-body">
            <div className="chart-value red">{stats.callsWithIssues}</div>
            <div className="mini-chart">
              <svg viewBox="0 0 400 100" className="line-chart">
                <path
                  d="M0,50 L100,50 L200,50 L300,50 L400,50"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  opacity="0.3"
                />
                <circle cx="400" cy="50" r="4" fill="#2563eb" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Calls Table */}
      <div className="calls-section">
        <div className="calls-header">
          <h2>Calls</h2>
          <div className="calls-controls">
            <button className="filter-btn" onClick={() => setShowFilters(!showFilters)}>
              <Filter size={16} />
              Filters
            </button>
            <div className="search-box">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search calls..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="calls-table-wrapper">
          <table className="calls-table" data-testid="calls-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>FROM</th>
                <th>TO</th>
                <th>DIRECTION</th>
                <th className="sortable" onClick={() => handleSort('started_at')}>
                  STARTED AT {sortField === 'started_at' && (sortOrder === 'desc' ? '↓' : '↑')}
                </th>
                <th className="sortable" onClick={() => handleSort('ended_at')}>
                  ENDED AT {sortField === 'ended_at' && (sortOrder === 'desc' ? '↓' : '↑')}
                </th>
                <th>DURATION</th>
                <th>SESSION</th>
              </tr>
            </thead>
            <tbody>
              {filteredCalls.map(call => (
                <tr key={call.id} data-testid={`call-row-${call.id}`}>
                  <td className="id-cell">{call.id}</td>
                  <td>{call.from}</td>
                  <td>{call.to}</td>
                  <td>
                    <span className="direction-badge">
                      <PhoneOutgoing size={14} />
                      {call.direction}
                    </span>
                  </td>
                  <td>{formatDateTime(call.started_at)}</td>
                  <td>{formatDateTime(call.ended_at)}</td>
                  <td>{formatDuration(call.duration)}</td>
                  <td>
                    <div className="session-cell">
                      <QrCode size={14} />
                      <span>{call.session}</span>
                      <button className="copy-btn" title="Open session">
                        <ExternalLink size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredCalls.length === 0 && (
            <div className="empty-table">
              <Phone size={32} />
              <p>No calls found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Session;
