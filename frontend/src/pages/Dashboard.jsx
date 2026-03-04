import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Phone, FileCheck, Users, LayoutDashboard, Clock, LogOut, ChevronRight, Megaphone } from 'lucide-react';
import Campaign from './Campaign';
import Session from './Session';
import Contacts from './Contacts';
import Dashboards from './Dashboards';
import './Dashboard.css';

const iconMap = {
  Phone: Phone,
  FileCheck: FileCheck,
  Users: Users,
  LayoutDashboard: LayoutDashboard,
  Clock: Clock,
  Megaphone: Megaphone
};

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [brand, setBrand] = useState(null);
  const [features, setFeatures] = useState([]);
  const [activeFeature, setActiveFeature] = useState(null);
  const [activePage, setActivePage] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user_data');
    
    if (!token || !userData) {
      navigate('/login');
      return;
    }

    const data = JSON.parse(userData);
    setUser(data.user);
    setBrand(data.brand);
    setFeatures(data.features || []);
    
    // Set default active feature
    if (data.features && data.features.length > 0) {
      setActiveFeature(data.features[0]);
      if (data.features[0].pages && data.features[0].pages.length > 0) {
        setActivePage(data.features[0].pages[0]);
      }
    }
  }, [navigate]);

  const handleFeatureClick = (feature) => {
    setActiveFeature(feature);
    if (feature.pages && feature.pages.length > 0) {
      setActivePage(feature.pages[0]);
    } else {
      setActivePage(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_data');
    navigate('/login');
  };

  const getIcon = (iconName, size = 20) => {
    const IconComponent = iconMap[iconName] || Phone;
    return <IconComponent size={size} />;
  };

  if (!user) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      {/* Left Sidebar - Features */}
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">M</div>
        </div>
        
        <nav className="sidebar-nav">
          {features.map(feature => (
            <button
              key={feature.id}
              className={`sidebar-feature ${activeFeature?.id === feature.id ? 'active' : ''}`}
              onClick={() => handleFeatureClick(feature)}
              title={feature.name}
            >
              {getIcon(feature.icon, 22)}
              <span className="feature-tooltip">{feature.name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-button" onClick={handleLogout} title="Logout">
            <LogOut size={20} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Top Navigation - Pages */}
        <header className="dashboard-header">
          <div className="header-left">
            <h1>{activeFeature?.name || 'Dashboard'}</h1>
            <span className="brand-indicator">{brand?.name}</span>
          </div>
          
          {activeFeature?.pages && activeFeature.pages.length > 0 && (
            <nav className="page-tabs">
              {activeFeature.pages.sort((a, b) => a.display_order - b.display_order).map(page => (
                <button
                  key={page.id}
                  className={`page-tab ${activePage?.id === page.id ? 'active' : ''}`}
                  onClick={() => setActivePage(page)}
                >
                  {getIcon(page.icon, 16)}
                  {page.name}
                </button>
              ))}
            </nav>
          )}

          <div className="header-right">
            <span className="user-name">{user.username}</span>
          </div>
        </header>

        {/* Page Content */}
        <div className="dashboard-content">
          {activePage?.name === 'Dashboards' ? (
            <Dashboards />
          ) : activePage?.name === 'Campaign' ? (
            <Campaign />
          ) : activePage?.name === 'Session' ? (
            <Session />
          ) : activePage?.name === 'Contacts' ? (
            <Contacts />
          ) : activePage ? (
            <div className="page-placeholder">
              <div className="placeholder-icon">
                {getIcon(activePage.icon, 64)}
              </div>
              <h2>{activePage.name}</h2>
              <p>This is the {activePage.name} page for {activeFeature?.name}.</p>
              <p className="placeholder-hint">Content coming soon...</p>
            </div>
          ) : activeFeature ? (
            <div className="page-placeholder">
              <div className="placeholder-icon">
                {getIcon(activeFeature.icon, 64)}
              </div>
              <h2>{activeFeature.name}</h2>
              <p>No pages configured for this feature yet.</p>
            </div>
          ) : (
            <div className="page-placeholder">
              <h2>Welcome, {user.username}!</h2>
              <p>Select a feature from the sidebar to get started.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
