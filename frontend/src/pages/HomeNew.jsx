import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Home as HomeIcon, Grid, ShoppingCart, Tag, Heart, Settings } from 'lucide-react';
import './HomeNew.css';

const HomeNew = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: ''
  });
  const [formStatus, setFormStatus] = useState({ loading: false, success: false, error: '' });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormStatus({ loading: true, success: false, error: '' });

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/leads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to submit form');
      }

      setFormStatus({ loading: false, success: true, error: '' });
      setFormData({ name: '', email: '', company: '', message: '' });
      
      // Reset success message after 5 seconds
      setTimeout(() => {
        setFormStatus(prev => ({ ...prev, success: false }));
      }, 5000);
    } catch (error) {
      setFormStatus({ loading: false, success: false, error: error.message });
    }
  };

  // Product cards SURROUNDING MadOver AI from all sides
  const productCards = [
    // TOP LEFT AREA
    {
      id: 1,
      name: 'Dream Night Serum with B...',
      image: 'https://images.unsplash.com/photo-1770732766528-d0e9fd0df233?w=400&q=80',
      rating: 5,
      reviews: '227',
      position: { top: '10%', left: '6%' },
      zIndex: 5
    },
    {
      id: 2,
      name: 'Premium Leather Bag',
      image: 'https://images.unsplash.com/photo-1772026251816-a6d382c67b3b?w=400&q=80',
      rating: 5,
      reviews: '156',
      position: { top: '6%', left: '24%' },
      zIndex: 3
    },
    
    // TOP RIGHT AREA
    {
      id: 3,
      name: 'White Sneakers Collection',
      image: 'https://images.unsplash.com/photo-1625860191460-10a66c7384fb?w=400&q=80',
      rating: 5,
      reviews: '89',
      position: { top: '10%', right: '6%' },
      zIndex: 5
    },
    {
      id: 4,
      name: 'Luxury Sunglasses',
      image: 'https://images.unsplash.com/photo-1760446032400-506ec8963e6a?w=400&q=80',
      rating: 5,
      reviews: '234',
      position: { top: '6%', right: '24%' },
      zIndex: 6
    },
    
    // MIDDLE LEFT - AT LOGO HEIGHT
    {
      id: 5,
      name: 'Cookware Set',
      image: 'https://images.unsplash.com/photo-1584990347163-2b86b71390d6?w=400&q=80',
      rating: 5,
      reviews: '38.5k',
      position: { top: '38%', left: '3%' }, // Left side at logo height
      zIndex: 4
    },
    
    // MIDDLE RIGHT - AT LOGO HEIGHT
    {
      id: 6,
      name: 'Coffee Mug Premium',
      image: 'https://images.unsplash.com/photo-1548287914-44c700af2ed5?w=400&q=80',
      rating: 4,
      reviews: '91',
      position: { top: '38%', right: '3%' }, // Right side at logo height
      zIndex: 4
    },
    
    // BOTTOM LEFT AREA
    {
      id: 8,
      name: 'Organic Dark Chocolate B...',
      image: 'https://images.unsplash.com/photo-1760307244852-190a6c5d2a5f?w=400&q=80',
      rating: 5,
      reviews: '52',
      position: { bottom: '12%', left: '6%' },
      zIndex: 7
    },
    {
      id: 9,
      name: 'Gourmet Collection',
      image: 'https://images.unsplash.com/photo-1685384338018-1774719d5b69?w=400&q=80',
      rating: 5,
      reviews: '178',
      position: { bottom: '8%', left: '24%' },
      zIndex: 5
    },
    
    // BOTTOM RIGHT AREA
    {
      id: 10,
      name: 'Terry Stripe Slippers (Bone...',
      image: 'https://images.unsplash.com/photo-1656335362192-2bc9051b1824?w=400&q=80',
      rating: 4,
      reviews: '2',
      position: { bottom: '12%', right: '6%' },
      zIndex: 6
    },
    {
      id: 11,
      name: 'Designer Bag',
      image: 'https://images.unsplash.com/photo-1540749046540-b7d8f98c7e4c?w=400&q=80',
      rating: 5,
      reviews: '324',
      position: { bottom: '8%', right: '24%' },
      zIndex: 4
    }
  ];

  const renderStars = (rating) => {
    return '⭐'.repeat(rating);
  };

  return (
    <div className="home-new-container">
      {/* Left Navigation Sidebar - OUTSIDE THE CARD */}
      <nav className="left-sidebar">
        <div className="sidebar-logo">
          <div className="logo-circle">O</div>
        </div>
        <div className="sidebar-items">
          <button className="sidebar-item active" title="Home">
            <HomeIcon size={20} />
          </button>
          <button className="sidebar-item" title="Categories">
            <Grid size={20} />
          </button>
          <button className="sidebar-item" title="Cart">
            <ShoppingCart size={20} />
          </button>
          <button className="sidebar-item" title="Tags">
            <Tag size={20} />
          </button>
          <button className="sidebar-item" title="Favorites">
            <Heart size={20} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <button className="sidebar-item" title="Settings">
            <div className="letter-icon">L</div>
          </button>
        </div>
      </nav>

      {/* 3D ELEVATED CARD CONTAINER */}
      <div className="main-card-container">
        {/* Top App Banner - INSIDE CARD */}
        <div className="top-banner">
          <div className="banner-content">
            <div className="banner-icon">📱</div>
            <span>Download Mad Over AI app. Available on iOS & Android</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>

        {/* Main Hero Section */}
        <main className="hero-main">
        <div className="hero-wrapper">
          {/* Floating Product Cards */}
          <div className="products-container">
            {productCards.map((product, index) => (
              <div
                key={product.id}
                className={`product-card ${product.size || ''}`}
                style={{
                  ...product.position,
                  zIndex: product.zIndex,
                  transform: `translate(${mousePosition.x * 0.008 * (index % 2 === 0 ? 1 : -1)}px, ${mousePosition.y * 0.008 * (index % 3 === 0 ? 1 : -1)}px)`,
                  animationDelay: `${index * 0.15}s`
                }}
              >
                <div className="product-image-wrapper">
                  <img src={product.image} alt={product.name} className="product-image" />
                </div>
                <div className="product-info">
                  <h3 className="product-name">{product.name}</h3>
                  <div className="product-rating">
                    <span className="stars">{renderStars(product.rating)}</span>
                    <span className="reviews">({product.reviews})</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Center Content */}
          <div className="hero-center">
            <h1 className="hero-main-title">MadOver AI</h1>
            
            <div className="hero-search-wrapper">
              <input
                type="text"
                className="hero-search-input"
                placeholder="What are you shopping for today?"
              />
              <button className="hero-search-button">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M7.5 3.33334L13.3333 10L7.5 16.6667" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Pagination Dots */}
          <div className="pagination-dots">
            <span className="dot active"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      </main>
      </div>
      {/* END 3D CARD CONTAINER */}

      {/* Metrics Section */}
      <section className="metrics-section">
        <div className="metrics-background">AI</div>
        <div className="metrics-container">
          <div className="metrics-left">
            <h2 className="metrics-heading">
              Millions trust Servity to<br />
              deliver great value
            </h2>
          </div>
          <div className="metrics-right">
            <div className="metric-item">
              <div className="metric-number">75+</div>
              <div className="metric-label">Brand Customers</div>
            </div>
            <div className="metric-item">
              <div className="metric-number">200k+</div>
              <div className="metric-label">Resellers</div>
            </div>
            <div className="metric-item">
              <div className="metric-number">18k+</div>
              <div className="metric-label">Service Locations</div>
            </div>
            <div className="metric-item">
              <div className="metric-number">40+</div>
              <div className="metric-label">Countries</div>
            </div>
          </div>
        </div>
      </section>

      {/* Case Studies Section */}
      <section className="case-studies-section">
        <div className="case-studies-container">
          <h2 className="case-studies-heading">Supercharge your<br/>business with Servify</h2>
          
          <div className="case-studies-tabs">
            <button className="tab-button active">OEM</button>
            <button className="tab-button">Carriers & MVNOs</button>
            <button className="tab-button">ISPs & BSPs</button>
            <button className="tab-button">Home Warranty</button>
            <button className="tab-button">Retail</button>
          </div>

          <div className="case-study-card">
            <div className="case-study-image" style={{
              background: 'linear-gradient(135deg, #A8D8EA 0%, #87CEEB 100%)',
              position: 'relative'
            }}>
              <div className="tech-icons">
                <div className="icon-circle" style={{top: '20%', left: '15%'}}>📱</div>
                <div className="icon-circle" style={{top: '15%', left: '35%'}}>💻</div>
                <div className="icon-circle" style={{top: '30%', left: '10%'}}>🎧</div>
                <div className="icon-circle" style={{bottom: '25%', left: '20%'}}>⌚</div>
                <div className="connecting-lines"></div>
              </div>
            </div>
            <div className="case-study-content-card">
              <h2 className="case-study-title">
                Increase your revenue and reduce customer churn
              </h2>
              <p className="case-study-description">
                By introducing whole home consumer electronics protection plans
              </p>
              <Link to="/case-study/revenue-churn" className="learn-more-button">
                Learn More →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom Footer */}
      <footer className="hero-footer">
        <div className="footer-left">
          <div className="footer-logo-icon">shop</div>
          <span className="footer-logo-text">Shop</span>
        </div>
        <div className="footer-right">
          <span className="curated-text">curated by</span>
          <span className="mobbin-logo">Mobbin</span>
        </div>
      </footer>
    </div>
  );
};

export default HomeNew;
