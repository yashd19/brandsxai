import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './AdornIQ.css';

const AdornIQ = () => {
  return (
    <div className="adorniq-page">
      {/* NAV */}
      <nav className="adorniq-nav">
        <Link to="/" className="back-link">
          <ArrowLeft size={20} />
          <span>Back to BrandsXAI</span>
        </Link>
        <div className="nav-logo"><span>Adorn</span>IQ</div>
        <ul className="nav-links">
          <li><a href="#products">Products</a></li>
          <li><a href="#how">How It Works</a></li>
          <li><a href="#fields">Industries</a></li>
          <li><Link to="/contact">Contact</Link></li>
        </ul>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-bg"></div>
        <div className="hero-ring"></div>
        <div className="hero-ring"></div>
        <div className="hero-ring"></div>

        <div className="hero-content">
          <div className="hero-eyebrow">The Future of Jewellery Retail</div>
          <h1>Where <em>Elegance</em><br/>Meets Intelligence</h1>
          <p className="hero-sub">
            A complete AI-powered suite that transforms how brides discover, visualise, and purchase jewellery — and how your team sells it.
          </p>
          <a href="#products" className="hero-cta">
            <span>Explore the Suite</span>
            <span>→</span>
          </a>
        </div>

        <div className="hero-scroll">Scroll</div>
      </section>

      <div className="gold-line"></div>
      <div className="divider"><div className="divider-diamond"></div></div>
      <div className="gold-line"></div>

      {/* PRODUCTS */}
      <section className="products" id="products">
        <div className="section-label">The Suite</div>
        <h2 className="section-title">Three <em>AI Products.</em><br/>One Complete Journey.</h2>
        <p className="section-desc">From the moment a bride imagines her look, to the second a salesperson seals the purchase — AdornIQ covers every step.</p>

        <div className="products-grid">
          {/* BRIDAL VISION AI */}
          <div className="product-card">
            <div className="card-number">01</div>
            <div className="card-icon">✦</div>
            <div className="card-tag">Virtual Try-On</div>
            <h3 className="card-title">Bridal Vision <em>AI</em></h3>
            <div className="card-subtitle">See It. Love It. Wear It.</div>
            <p className="card-desc">
              Upload a photo and watch jewellery come to life on you — in your wedding attire, on your wedding day. Powered by vision AI, every piece is rendered with photorealistic precision.
            </p>
            <ul className="card-features">
              <li>AI-powered virtual jewellery try-on</li>
              <li>Wedding day simulation with outfit matching</li>
              <li>One-click purchase from try-on view</li>
              <li>Share looks with family instantly</li>
            </ul>
            <img
              className="card-img"
              src="https://www.astyledwedding.com/wp-content/uploads/2020/09/bridal-jewelry-inspiration-730x1024.jpg"
              alt="Bride wearing bridal jewelry"
              loading="lazy"
              onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600&q=80&auto=format&fit=crop'; }}
            />
          </div>

          {/* INVENIQ */}
          <div className="product-card">
            <div className="card-number">02</div>
            <div className="card-icon">◈</div>
            <div className="card-tag">Smart Inventory Search</div>
            <h3 className="card-title">Inven<em>IQ</em></h3>
            <div className="card-subtitle">Find It. Show It. Sell It.</div>
            <p className="card-desc">
              Sales staff simply describe what they're looking for — in plain language — and InvenIQ surfaces the right pieces from inventory in seconds. No more dead ends, no more missed sales.
            </p>
            <ul className="card-features">
              <li>Natural language inventory search</li>
              <li>Real-time stock visibility across locations</li>
              <li>AI-ranked results by relevance</li>
              <li>Instant availability & pricing display</li>
            </ul>
            <img
              className="card-img"
              src="https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600&q=80&auto=format&fit=crop"
              alt="Jewelry store showcase display"
              loading="lazy"
            />
          </div>

          {/* JEWELMATCH */}
          <div className="product-card">
            <div className="card-number">03</div>
            <div className="card-icon">❋</div>
            <div className="card-tag">Taste-Based Recommendation</div>
            <h3 className="card-title">Jewel<em>Match</em> AI</h3>
            <div className="card-subtitle">Her Style. Her Match. Her Choice.</div>
            <p className="card-desc">
              The customer expresses her colour preferences, design sensibility and style — and JewelMatch curates a personalised selection she'll fall in love with, before she even asks.
            </p>
            <ul className="card-features">
              <li>Preference-driven product discovery</li>
              <li>Colour, design & style matching engine</li>
              <li>Salesperson-guided curation interface</li>
              <li>Learns & refines with every interaction</li>
            </ul>
            <img
              className="card-img"
              src="https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=600&q=80&auto=format&fit=crop"
              alt="Woman choosing jewelry in store"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <div className="gold-line"></div>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="section-label">The Journey</div>
        <h2 className="section-title">How <em>AdornIQ</em> Works</h2>
        <p className="section-desc">A seamless four-step experience that takes a bride from first glance to final purchase.</p>

        <div className="steps">
          <div className="step">
            <div className="step-num">1</div>
            <h4>She Shares Her Style</h4>
            <p>The bride selects her preferred colours, design motifs and jewellery style through a simple, beautiful interface.</p>
          </div>
          <div className="step">
            <div className="step-num">2</div>
            <h4>JewelMatch Curates</h4>
            <p>AI analyses her preferences and surfaces a handpicked selection from live inventory — tailored to her taste.</p>
          </div>
          <div className="step">
            <div className="step-num">3</div>
            <h4>Bridal Vision Visualises</h4>
            <p>She uploads her photo. The jewellery is rendered on her in her wedding look with stunning realism.</p>
          </div>
          <div className="step">
            <div className="step-num">4</div>
            <h4>She Buys with Confidence</h4>
            <p>The salesperson confirms availability via InvenIQ and completes the purchase — effortlessly.</p>
          </div>
        </div>
      </section>

      <div className="gold-line"></div>

      {/* FIELDS */}
      <section className="fields" id="fields">
        <div className="section-label">Industry Applications</div>
        <h2 className="section-title">Built for <em>Three Fields.</em></h2>
        <p className="section-desc">AdornIQ is not just a retail tool — it is a strategic asset across marketing, sales and operations.</p>

        <div className="fields-grid">
          <div className="field-item">
            <span className="field-icon-wrap">📣</span>
            <div className="field-name">Marketing</div>
            <p className="field-desc">Personalised discovery, immersive try-on experiences and shareable looks turn browsers into brand advocates before they ever visit a store.</p>
          </div>
          <div className="field-item">
            <span className="field-icon-wrap">💎</span>
            <div className="field-name">Sales</div>
            <p className="field-desc">Empowers every sales associate with AI-curated suggestions and live stock data, reducing lost sales and dramatically increasing conversion rates.</p>
          </div>
          <div className="field-item">
            <span className="field-icon-wrap">📊</span>
            <div className="field-name">Operations</div>
            <p className="field-desc">Real-time inventory intelligence reduces overstock, surfaces slow-moving pieces, and keeps the right products visible to the right customers at the right time.</p>
          </div>
        </div>
      </section>

      <div className="gold-line"></div>

      {/* FOOTER - BrandsXAI */}
      <footer className="adorniq-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3 className="footer-logo">BrandsXAI</h3>
            <p className="footer-tagline">BrandsXAI is the next step on our mission to make AI better for everyone.</p>
          </div>
          
          <div className="footer-links-grid">
            <div className="footer-col">
              <h4>AdornIQ Suite</h4>
              <a href="#products">Products</a>
              <a href="#how">How It Works</a>
              <a href="#fields">Industries</a>
            </div>
            <div className="footer-col">
              <h4>BrandsXAI</h4>
              <Link to="/">Home</Link>
              <Link to="/about">About Us</Link>
              <Link to="/contact">Contact</Link>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom">
          <span className="footer-powered">Powered by <strong>BrandsXAI</strong></span>
          <span className="footer-copyright">© BrandsXAI Inc. 2026</span>
        </div>
      </footer>
    </div>
  );
};

export default AdornIQ;
