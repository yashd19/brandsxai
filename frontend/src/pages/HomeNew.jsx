import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Home as HomeIcon, Grid, ShoppingCart, Tag, Heart, Settings } from 'lucide-react';
import './HomeNew.css';

const HomeNew = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

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
          <h2 className="case-studies-heading">Supercharge your<br/>business with <span className="highlight-purple">MadOver AI</span></h2>
          
          <div className="case-studies-tabs">
            <button className="tab-button active">OEM</button>
            <button className="tab-button">Carriers & MVNOs</button>
            <button className="tab-button">ISPs & BSPs</button>
            <button className="tab-button">Home Warranty</button>
            <button className="tab-button">Retail</button>
          </div>

          <div className="case-study-card">
            <img 
              src="https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1200&q=80" 
              alt="City skyline at night with network connections" 
              className="case-study-bg-image"
            />
            <div className="case-study-content-card">
              <h2 className="case-study-title">
                Increase your revenue and reduce customer churn
              </h2>
              <p className="case-study-description">
                By offering device protection plans your customers want with features they love
              </p>
              <Link to="/case-study/revenue-churn" className="learn-more-button">
                Learn More →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="site-footer">
        <div className="footer-main">
          <div className="footer-brand">
            <h3 className="footer-logo">MadOver AI</h3>
            <p className="footer-tagline">MadOver AI is the next step on our mission to make AI better for everyone.</p>
            <div className="footer-apps">
              <a href="#" className="app-badge">
                <img src="https://upload.wikimedia.org/wikipedia/commons/3/3c/Download_on_the_App_Store_Badge.svg" alt="Download on App Store" />
              </a>
              <a href="#" className="app-badge">
                <img src="https://upload.wikimedia.org/wikipedia/commons/7/78/Google_Play_Store_badge_EN.svg" alt="Get it on Google Play" />
              </a>
            </div>
          </div>
          
          <div className="footer-links-section">
            <div className="footer-column">
              <h4 className="footer-column-title">Information</h4>
              <a href="#" className="footer-link">Solutions</a>
              <a href="#" className="footer-link">Help center</a>
              <Link to="/contact" className="footer-link">For brands</Link>
            </div>
            
            <div className="footer-column">
              <h4 className="footer-column-title">Social</h4>
              <a href="#" className="footer-link">X (Twitter)</a>
              <a href="#" className="footer-link">Instagram</a>
              <a href="#" className="footer-link">LinkedIn</a>
            </div>
            
            <div className="footer-column">
              <h4 className="footer-column-title">Legal</h4>
              <a href="#" className="footer-link">Terms of Service</a>
              <a href="#" className="footer-link">Privacy Policy</a>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom">
          <span className="footer-powered">Powered by <strong>MadOver AI</strong></span>
          <span className="footer-copyright">© MadOver AI Inc. 2026</span>
        </div>
      </footer>
    </div>
  );
};

export default HomeNew;
