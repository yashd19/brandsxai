import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './FoundAI.css';

const FoundAI = () => {
  return (
    <div className="found-container">
      {/* NAV */}
      <nav className="found-nav">
        <Link to="/" className="found-back">
          <ArrowLeft size={20} />
          <span>Back to BrandsXAI</span>
        </Link>
        <div className="found-logo">Found<em>AI</em></div>
        <div className="found-nav-links">
          <a href="#why">Why GEO</a>
          <a href="#services">Services</a>
          <a href="#process">Process</a>
          <a href="#contact" className="nav-cta">Get Audit</a>
        </div>
      </nav>

      {/* HERO */}
      <section className="found-hero">
        <div className="hero-bg"></div>
        <div className="hero-glow"></div>

        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="status-dot"></span>
            Now Accepting Clients — Q2 2026
          </div>
          
          <h1>Be <span className="line-accent">Found</span> in the <span className="line-outline">AI Era.</span></h1>

          <p className="hero-tagline">
            When someone asks ChatGPT, Claude or Gemini about your industry — <strong>your brand should be the answer.</strong> We make that happen.
          </p>

          <div className="hero-stats">
            <div className="stat-item">
              <span className="stat-num">4+</span>
              <span className="stat-label">AI Platforms</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">8wk</span>
              <span className="stat-label">To Visibility</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">0</span>
              <span className="stat-label">Competitors Doing This</span>
            </div>
          </div>

          <div className="hero-ctas">
            <a href="#services" className="btn-primary"><span>See Our Services</span><span>→</span></a>
            <a href="#why" className="btn-outline"><span>Why GEO Matters</span></a>
          </div>
        </div>

        {/* Terminal Animation */}
        <div className="hero-terminal">
          <div className="terminal-bar">
            <span className="terminal-dot red"></span>
            <span className="terminal-dot yellow"></span>
            <span className="terminal-dot green"></span>
            <span className="terminal-title">geo_audit.sh</span>
          </div>
          <div className="terminal-body">
            <div className="terminal-line">
              <span className="prompt">$</span> Running GEO audit for <span className="highlight">yourbrand.com</span>...
            </div>
            <div className="terminal-line">
              <span className="prompt">→</span> Checking ChatGPT visibility... <span className="status error">NOT FOUND</span>
            </div>
            <div className="terminal-line">
              <span className="prompt">→</span> Checking Gemini visibility... <span className="status error">NOT FOUND</span>
            </div>
            <div className="terminal-line">
              <span className="prompt">→</span> Checking Claude visibility... <span className="status error">NOT FOUND</span>
            </div>
            <div className="terminal-line">
              <span className="prompt">→</span> Checking AI Overviews... <span className="status error">NOT FOUND</span>
            </div>
            <div className="terminal-line muted">
              <span className="prompt">!</span> Your competitors are invisible too. This is the window.
            </div>
            <div className="terminal-line success">
              <span className="prompt">✓</span> GEO opportunity score: <span className="highlight">HIGH</span>
            </div>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>
      <div className="divider"><div className="divider-mark"></div></div>
      <div className="lime-line"></div>

      {/* WHY GEO */}
      <section className="why-section" id="why">
        <div className="section-label">The Shift</div>
        <h2 className="section-title">Search has <em>changed.</em><br />Has your strategy?</h2>
        <p className="section-desc">40% of Gen Z now searches on AI platforms instead of Google. And when they do — they don't get links. They get one answer. Yours needs to be it.</p>

        <div className="why-grid">
          <div className="why-card">
            <div className="why-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <h3>Search habits are shifting</h3>
            <p>Users are abandoning Google and asking ChatGPT, Claude, and Gemini directly. Your old SEO playbook doesn't work here.</p>
          </div>

          <div className="why-card">
            <div className="why-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <h3>AI picks one answer</h3>
            <p>Unlike 10 blue links, AI gives one response. If you're not cited — you don't exist. We get you cited.</p>
          </div>

          <div className="why-card">
            <div className="why-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            </div>
            <h3>Early movers win</h3>
            <p>This is SEO in 2004. The playbook is new. The competition is low. The upside is massive — if you move now.</p>
          </div>

          <div className="why-card">
            <div className="why-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>
            </div>
            <h3>Zero competitors doing this</h3>
            <p>Most businesses don't know GEO exists. While they sleep on it, you can become the default answer in your category.</p>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>

      {/* SERVICES */}
      <section className="services-section" id="services">
        <div className="section-label">What We Do</div>
        <h2 className="section-title">Three services. <em>One outcome.</em></h2>
        <p className="section-desc">Every engagement is designed to get you one thing: appearing in AI answers when your category is mentioned.</p>

        <div className="services-grid">
          <div className="service-card">
            <div className="service-badge">Clarity</div>
            <h3>GEO Audit</h3>
            <p>We run your brand through ChatGPT, Gemini, Claude, and AI Overviews — and tell you exactly where you stand, what's missing, and what to fix.</p>
            <ul className="service-features">
              <li>AI visibility score across 4 platforms</li>
              <li>Competitor visibility analysis</li>
              <li>Gap analysis + roadmap</li>
              <li>Delivered in 5 business days</li>
            </ul>
            <div className="service-price">Starting at ₹25,000</div>
          </div>

          <div className="service-card featured">
            <div className="service-badge">Visibility</div>
            <h3>GEO Foundation</h3>
            <p>A complete GEO setup. We rewrite your content, implement schema, create AI-friendly Q&A, and build citations to get you into answers.</p>
            <ul className="service-features">
              <li>Content optimization for AI</li>
              <li>Schema markup implementation</li>
              <li>Q&A structured content</li>
              <li>Authority signal building</li>
              <li>Initial visibility within 8 weeks</li>
            </ul>
            <div className="service-price">Starting at ₹1,50,000</div>
          </div>

          <div className="service-card">
            <div className="service-badge">Dominance</div>
            <h3>GEO Retainer</h3>
            <p>Ongoing GEO maintenance. We monitor your AI visibility, adjust to model updates, and compound your presence over time.</p>
            <ul className="service-features">
              <li>Monthly visibility reports</li>
              <li>Continuous content updates</li>
              <li>AI model change adaptation</li>
              <li>Competitor monitoring</li>
            </ul>
            <div className="service-price">Starting at ₹50,000/mo</div>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>

      {/* PROCESS */}
      <section className="process-section" id="process">
        <div className="section-label">How It Works</div>
        <h2 className="section-title">From <em>invisible</em> to cited.<br />In 8 weeks.</h2>
        <p className="section-desc">A structured, repeatable process that takes you from unknown to authoritative in AI answers.</p>

        <div className="process-timeline">
          <div className="process-step">
            <div className="step-num">01</div>
            <div className="step-content">
              <div className="step-week">Week 1-2</div>
              <h4>Audit & Discovery</h4>
              <p>We analyze your current visibility across ChatGPT, Gemini, Claude, and AI Overviews. We map your competitors and identify the gaps.</p>
            </div>
          </div>

          <div className="process-step">
            <div className="step-num">02</div>
            <div className="step-content">
              <div className="step-week">Week 2-3</div>
              <h4>Language & Structure</h4>
              <p>We identify the exact language patterns AI models prefer. We restructure your content to match how AI retrieves and cites information.</p>
            </div>
          </div>

          <div className="process-step">
            <div className="step-num">03</div>
            <div className="step-content">
              <div className="step-week">Week 3-6</div>
              <h4>Content & Citations</h4>
              <p>We create and deploy AI-optimized content. We build citations, implement schema, and create structured Q&A that AI loves to cite.</p>
            </div>
          </div>

          <div className="process-step">
            <div className="step-num">04</div>
            <div className="step-content">
              <div className="step-week">Week 6-8+</div>
              <h4>Monitor & Compound</h4>
              <p>We track your appearance in AI answers, adapt to model updates, and continue building your authority. The visibility compounds.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>

      {/* GEO VS SEO */}
      <section className="compare-section" id="compare">
        <div className="section-label">The Difference</div>
        <h2 className="section-title">GEO vs <em>SEO</em></h2>
        <p className="section-desc">SEO gets you ranked. GEO gets you cited. One is the past. One is the future.</p>

        <div className="compare-table">
          <div className="compare-row header">
            <div className="compare-cell">Aspect</div>
            <div className="compare-cell">SEO</div>
            <div className="compare-cell highlight">GEO</div>
          </div>
          <div className="compare-row">
            <div className="compare-cell label">Goal</div>
            <div className="compare-cell">Rank on page 1</div>
            <div className="compare-cell highlight">Be the AI's answer</div>
          </div>
          <div className="compare-row">
            <div className="compare-cell label">Where it shows</div>
            <div className="compare-cell">Google search results</div>
            <div className="compare-cell highlight">ChatGPT, Gemini, Claude, AI Overviews</div>
          </div>
          <div className="compare-row">
            <div className="compare-cell label">Format</div>
            <div className="compare-cell">10 blue links</div>
            <div className="compare-cell highlight">One cited answer</div>
          </div>
          <div className="compare-row">
            <div className="compare-cell label">Competition</div>
            <div className="compare-cell">Extremely high</div>
            <div className="compare-cell highlight">Almost none (for now)</div>
          </div>
          <div className="compare-row">
            <div className="compare-cell label">Future trajectory</div>
            <div className="compare-cell">Declining relevance</div>
            <div className="compare-cell highlight">Exponential growth</div>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>

      {/* WHO WE SERVE */}
      <section className="serve-section" id="serve">
        <div className="section-label">Who We Serve</div>
        <h2 className="section-title">Built for brands ready<br />to be <em>found.</em></h2>
        <p className="section-desc">From e-commerce to professional services — if people search for what you do, you need GEO.</p>

        <div className="serve-grid">
          <div className="serve-card">
            <h4>D2C & E-Commerce</h4>
            <p>Get your products recommended when users ask AI for buying advice.</p>
          </div>
          <div className="serve-card">
            <h4>B2B SaaS</h4>
            <p>Become the cited solution when businesses search for software.</p>
          </div>
          <div className="serve-card">
            <h4>Professional Services</h4>
            <p>Lawyers, consultants, agencies — appear when AI recommends experts.</p>
          </div>
          <div className="serve-card">
            <h4>Local Businesses</h4>
            <p>Dominate local AI queries in your city and category.</p>
          </div>
          <div className="serve-card">
            <h4>MSME & Trade</h4>
            <p>Wholesalers, manufacturers — get found by B2B buyers using AI.</p>
          </div>
          <div className="serve-card">
            <h4>Marketing Agencies</h4>
            <p>Add GEO to your service stack. White-label available.</p>
          </div>
        </div>
      </section>

      <div className="lime-line"></div>

      {/* CTA */}
      <section className="found-cta" id="contact">
        <h2>Ready to be Found?</h2>
        <p>Get your free GEO audit and see exactly where you stand in AI answers.</p>
        <Link to="/contact" className="btn-primary"><span>Get Your Audit</span><span>→</span></Link>
      </section>

      <div className="lime-line"></div>
      <div className="divider"><div className="divider-mark"></div></div>
      <div className="lime-line"></div>

      {/* FOOTER */}
      <footer className="found-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3 className="footer-logo">BrandsXAI</h3>
            <p className="footer-tagline">BrandsXAI is the next step on our mission to make AI better for everyone.</p>
          </div>
          
          <div className="footer-links-grid">
            <div className="footer-col">
              <h4>FoundAI</h4>
              <a href="#why">Why GEO</a>
              <a href="#services">Services</a>
              <a href="#process">Process</a>
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

export default FoundAI;
