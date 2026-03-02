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

  // LEFT SIDE Products (pushed to left edge)
  const leftProducts = [
    {
      id: 1,
      name: 'Dream Night Serum with B...',
      image: 'https://images.unsplash.com/photo-1770732766528-d0e9fd0df233?w=400&q=80',
      rating: 5,
      reviews: '227',
      position: { top: '15%', left: '5%' },
      zIndex: 5
    },
    {
      id: 2,
      name: 'Premium Leather Bag',
      image: 'https://images.unsplash.com/photo-1540749046540-b7d8f98c7e4c?w=500&q=80',
      rating: 5,
      reviews: '156',
      position: { top: '8%', left: '20%' },
      zIndex: 3
    },
    {
      id: 3,
      name: 'Organic Dark Chocolate B...',
      image: 'https://images.unsplash.com/photo-1760307244852-190a6c5d2a5f?w=400&q=80',
      rating: 5,
      reviews: '52',
      position: { bottom: '18%', left: '5%' },
      zIndex: 4
    },
    {
      id: 4,
      name: 'Coffee Mug Premium',
      image: 'https://images.unsplash.com/photo-1548287914-44c700af2ed5?w=400&q=80',
      rating: 4,
      reviews: '91',
      position: { bottom: '10%', left: '22%' },
      zIndex: 3
    }
  ];

  // RIGHT SIDE Products (pushed to right edge)
  const rightProducts = [
    {
      id: 5,
      name: 'White Sneakers Collection',
      image: 'https://images.unsplash.com/photo-1625860191460-10a66c7384fb?w=400&q=80',
      rating: 5,
      reviews: '89',
      position: { top: '12%', right: '20%' },
      zIndex: 4
    },
    {
      id: 6,
      name: 'Luxury Sunglasses',
      image: 'https://images.unsplash.com/photo-1760446032400-506ec8963e6a?w=400&q=80',
      rating: 5,
      reviews: '234',
      position: { top: '20%', right: '5%' },
      zIndex: 5
    },
    {
      id: 7,
      name: 'Cookware Set',
      image: 'https://images.unsplash.com/photo-1584990347163-2b86b71390d6?w=400&q=80',
      rating: 5,
      reviews: '38.5k',
      position: { top: '5%', right: '2%' },
      zIndex: 3
    },
    {
      id: 8,
      name: 'Designer Bag',
      image: 'https://images.unsplash.com/photo-1772026251816-a6d382c67b3b?w=400&q=80',
      rating: 5,
      reviews: '178',
      position: { bottom: '15%', right: '22%' },
      zIndex: 4
    },
    {
      id: 9,
      name: 'Terry Stripe Slippers (Bone...',
      image: 'https://images.unsplash.com/photo-1656335362192-2bc9051b1824?w=400&q=80',
      rating: 4,
      reviews: '2',
      position: { bottom: '12%', right: '5%' },
      zIndex: 5
    }
  ];

  const renderStars = (rating) => {
    return '⭐'.repeat(rating);
  };

  return (
    <div className="home-new-container">
      {/* Top App Banner */}
      <div className="top-banner">
        <div className="banner-content">
          <div className="banner-icon">📱</div>
          <span>Download Mad Over AI app. Available on iOS & Android</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>

      {/* Left Navigation Sidebar */}
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

      {/* Main Hero Section */}
      <main className="hero-main">
        <div className="hero-wrapper">
          {/* LEFT SIDE - Product Cards */}
          <div className="products-left">
            {leftProducts.map((product, index) => (
              <div
                key={product.id}
                className="product-card"
                style={{
                  ...product.position,
                  zIndex: product.zIndex,
                  transform: `translate(${mousePosition.x * 0.005}px, ${mousePosition.y * 0.005}px)`,
                  animationDelay: `${index * 0.2}s`
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

          {/* RIGHT SIDE - Product Cards */}
          <div className="products-right">
            {rightProducts.map((product, index) => (
              <div
                key={product.id}
                className="product-card"
                style={{
                  ...product.position,
                  zIndex: product.zIndex,
                  transform: `translate(${mousePosition.x * -0.005}px, ${mousePosition.y * 0.005}px)`,
                  animationDelay: `${index * 0.2}s`
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
            <h1 className="hero-main-title">Mad Over AI</h1>
            
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
