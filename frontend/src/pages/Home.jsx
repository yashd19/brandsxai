import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Mic, Brain, Zap, ChevronRight } from 'lucide-react';
import './Home.css';

const Home = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // AI Use Case Cards - animated floating cards
  const aiCards = [
    { id: 1, title: 'Voice AI', icon: '🎤', description: 'Intelligent voice interactions', color: '#E4EDF8', position: { top: '15%', left: '12%' } },
    { id: 2, title: 'Automation', icon: '⚡', description: 'AI-powered workflows', color: '#F9E8FA', position: { top: '25%', right: '15%' } },
    { id: 3, title: 'Inventory AI', icon: '📦', description: 'Smart inventory management', color: '#FEEFDC', position: { top: '60%', left: '10%' } },
    { id: 4, title: 'Analytics', icon: '📊', description: 'Data-driven insights', color: '#FCC9C7', position: { top: '45%', right: '12%' } },
    { id: 5, title: 'Chat AI', icon: '💬', description: 'Conversational interfaces', color: '#b8d1ba', position: { top: '70%', right: '20%' } },
    { id: 6, title: 'Vision AI', icon: '👁️', description: 'Image recognition', color: '#E9E1E1', position: { top: '35%', left: '20%' } },
  ];

  return (
    <div className="home-container">
      {/* Left Navigation */}
      <nav className="left-nav">
        <div className="nav-logo">
          <div className="logo-icon">
            <Sparkles size={24} />
          </div>
        </div>
        <div className="nav-items">
          <button className="nav-item active" title="Home">
            <div className="nav-icon-wrapper">
              <span className="nav-emoji">🏠</span>
            </div>
          </button>
          <button className="nav-item" title="Solutions">
            <div className="nav-icon-wrapper">
              <Brain size={20} />
            </div>
          </button>
          <button className="nav-item" title="Case Studies">
            <div className="nav-icon-wrapper">
              <span className="nav-emoji">📈</span>
            </div>
          </button>
          <Link to="/about" className="nav-item" title="About Us">
            <div className="nav-icon-wrapper">
              <span className="nav-emoji">ℹ️</span>
            </div>
          </Link>
        </div>
        <div className="nav-bottom">
          <button className="nav-item" title="Settings">
            <div className="nav-icon-wrapper">
              <span className="nav-emoji">⚙️</span>
            </div>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="floating-cards-container">
            {aiCards.map((card, index) => (
              <div
                key={card.id}
                className="floating-card"
                style={{
                  ...card.position,
                  backgroundColor: card.color,
                  animationDelay: `${index * 0.2}s`,
                  transform: `translate(${mousePosition.x * 0.01}px, ${mousePosition.y * 0.01}px)`
                }}
              >
                <div className="card-icon">{card.icon}</div>
                <h4 className="card-title">{card.title}</h4>
                <p className="card-description">{card.description}</p>
                <div className="card-rating">⭐⭐⭐⭐⭐</div>
              </div>
            ))}
          </div>

          <div className="hero-content">
            <div className="hero-badge">
              <Zap size={14} />
              <span>AI-Powered Innovation</span>
            </div>
            <h1 className="hero-title">Brands X AI</h1>
            <p className="hero-subtitle">
              Empowering brands with cutting-edge AI solutions for voice, automation, and intelligent systems
            </p>
            <div className="hero-search">
              <input
                type="text"
                placeholder="What AI solution are you looking for?"
                className="hero-input"
              />
              <button className="hero-search-btn">
                <ChevronRight size={20} />
              </button>
            </div>
          </div>

          <div className="hero-scroll-indicator">
            <div className="scroll-dots">
              <span className="dot active"></span>
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        </section>

        {/* Case Studies Section */}
        <section className="case-studies-section">
          <div className="section-container">
            <div className="section-header">
              <h2 className="section-title">Success Stories</h2>
              <p className="section-subtitle">See how we're transforming brands with AI</p>
            </div>

            <div className="case-studies-grid">
              <div className="case-study-card">
                <div className="case-study-image" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                  <Mic size={48} color="white" />
                </div>
                <div className="case-study-content">
                  <h3>Voice Commerce Revolution</h3>
                  <p>Increased customer engagement by 300% with AI-powered voice shopping</p>
                  <div className="case-study-stats">
                    <span className="stat">300% ↑</span>
                    <span className="stat-label">Engagement</span>
                  </div>
                </div>
              </div>

              <div className="case-study-card">
                <div className="case-study-image" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                  <Brain size={48} color="white" />
                </div>
                <div className="case-study-content">
                  <h3>Smart Inventory Management</h3>
                  <p>Reduced operational costs by 45% with AI-driven inventory optimization</p>
                  <div className="case-study-stats">
                    <span className="stat">45% ↓</span>
                    <span className="stat-label">Cost Reduction</span>
                  </div>
                </div>
              </div>

              <div className="case-study-card">
                <div className="case-study-image" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                  <Zap size={48} color="white" />
                </div>
                <div className="case-study-content">
                  <h3>Automated Customer Support</h3>
                  <p>Achieved 24/7 support with 95% customer satisfaction through AI automation</p>
                  <div className="case-study-stats">
                    <span className="stat">95%</span>
                    <span className="stat-label">Satisfaction</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-container">
            <div className="footer-content">
              <div className="footer-left">
                <div className="footer-logo">
                  <Sparkles size={28} />
                  <span>Brands X AI</span>
                </div>
                <p className="footer-tagline">Enabling brands through intelligent AI solutions</p>
                <div className="footer-social">
                  <a href="#" className="social-link">Twitter</a>
                  <a href="#" className="social-link">LinkedIn</a>
                  <a href="#" className="social-link">GitHub</a>
                </div>
              </div>

              <div className="footer-right">
                <h3 className="footer-form-title">Get Started with AI</h3>
                <p className="footer-form-subtitle">Let's transform your brand together</p>
                <form className="contact-form" onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  const data = {
                    name: formData.get('name'),
                    email: formData.get('email'),
                    company: formData.get('company'),
                    message: formData.get('message')
                  };
                  console.log('Form submitted:', data);
                  // TODO: Will integrate with backend
                  alert('Thank you! We will contact you soon.');
                  e.target.reset();
                }}>
                  <input type="text" name="name" placeholder="Your Name" required className="form-input" />
                  <input type="email" name="email" placeholder="Email Address" required className="form-input" />
                  <input type="text" name="company" placeholder="Company Name" required className="form-input" />
                  <textarea name="message" placeholder="Tell us about your AI needs..." required className="form-textarea"></textarea>
                  <button type="submit" className="form-submit">
                    Send Message
                    <ChevronRight size={16} />
                  </button>
                </form>
              </div>
            </div>

            <div className="footer-bottom">
              <p>&copy; 2026 Brands X AI. All rights reserved.</p>
              <div className="footer-links">
                <Link to="/about">About Us</Link>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
              </div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Home;
