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
            <div className="card-icon-wrap">
              <div className="card-icon-ring">
                <span className="card-icon-symbol">✦</span>
              </div>
              <div className="card-number">01</div>
            </div>
            <div className="card-tag">VIRTUAL TRY-ON</div>
            <h3 className="card-title">Bridal<br/>Vision<br/><em>AI</em></h3>
            <div className="card-subtitle">SEE IT.<br/>LOVE IT.<br/>WEAR IT.</div>
            <p className="card-desc">
              Upload a photo and watch jewellery come to life on you — in your wedding attire, on your wedding day. Powered by vision AI, every piece is rendered with photorealistic precision.
            </p>
          </div>

          {/* INVENIQ */}
          <div className="product-card">
            <div className="card-icon-wrap">
              <div className="card-icon-ring">
                <span className="card-icon-symbol">◇</span>
              </div>
              <div className="card-number">02</div>
            </div>
            <div className="card-tag">SMART INVENTORY SEARCH</div>
            <h3 className="card-title">Inven<em>IQ</em></h3>
            <div className="card-subtitle">FIND IT.<br/>SHOW IT.<br/>SELL IT.</div>
            <p className="card-desc">
              Sales staff simply describe what they're looking for — in plain language — and InvenIQ surfaces the right pieces from inventory in seconds. No more dead ends, no more missed sales.
            </p>
          </div>

          {/* JEWELMATCH */}
          <div className="product-card">
            <div className="card-icon-wrap">
              <div className="card-icon-ring">
                <span className="card-icon-symbol">✳</span>
              </div>
              <div className="card-number">03</div>
            </div>
            <div className="card-tag">TASTE-BASED RECOMMENDATION</div>
            <h3 className="card-title">JewelMatch<br/><em>AI</em></h3>
            <div className="card-subtitle">HER STYLE.<br/>HER MATCH.<br/>HER CHOICE.</div>
            <p className="card-desc">
              The customer expresses her colour preferences, design sensibility and style — and JewelMatch curates a personalised selection she'll fall in love with, before she even asks.
            </p>
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
