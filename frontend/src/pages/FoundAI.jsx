import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './FoundAI.css';

const FoundAI = () => {
  return (
    <div className="found-page">
      {/* NAV */}
      <nav className="found-nav">
        <Link to="/" className="back-link">
          <ArrowLeft size={20} />
          <span>Back to BrandsXAI</span>
        </Link>
        <div className="nav-logo">
          <div className="nav-logo-dot"></div>
          Found AI
        </div>
        <ul className="nav-links">
          <li><a href="#why">Why GEO</a></li>
          <li><a href="#services">Services</a></li>
          <li><a href="#process">Process</a></li>
          <li><Link to="/contact" className="nav-cta">Get Audit</Link></li>
        </ul>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-left fade-up">
          <div className="hero-status">
            <div className="status-dot"></div>
            Now Accepting Clients — Q2 2026
          </div>

          <h1>
            Be <span className="line-accent">Found</span><br/>
            in the<br/>
            <span className="line-outline">AI Era.</span>
          </h1>

          <p className="hero-tagline">
            When someone asks ChatGPT, Claude or Gemini about your industry —<br/>
            <strong>your brand should be the answer.</strong><br/>
            We make that happen.
          </p>

          <div className="hero-ctas">
            <a href="#services" className="btn-lime">
              <span>See Our Services</span>
              <span>→</span>
            </a>
            <a href="#why" className="btn-ghost">
              <span>Why GEO Matters</span>
            </a>
          </div>

          <div className="hero-metrics">
            <div className="metric">
              <span className="metric-num">4+</span>
              <span className="metric-label">AI Platforms</span>
            </div>
            <div className="metric">
              <span className="metric-num">8wk</span>
              <span className="metric-label">To Visibility</span>
            </div>
            <div className="metric">
              <span className="metric-num">0</span>
              <span className="metric-label">Competitors Doing This</span>
            </div>
          </div>
        </div>

        <div className="hero-right fade-up delay-2">
          <div className="terminal">
            <div className="terminal-bar">
              <div className="t-dot r"></div>
              <div className="t-dot y"></div>
              <div className="t-dot g"></div>
              <span className="terminal-title">found-ai — geo_audit.sh</span>
            </div>
            <div className="terminal-body">
              <div className="t-line"><span className="t-prompt">$ </span><span className="t-cmd">run geo-audit --client="Your Brand"</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output">Scanning ChatGPT responses...</span></div>
              <div className="t-line"><span className="t-output bad">✗ Not found in 48 relevant answers</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output">Scanning Google AI Overviews...</span></div>
              <div className="t-line"><span className="t-output bad">✗ Not found in 31 relevant answers</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output">Scanning Perplexity...</span></div>
              <div className="t-line"><span className="t-output bad">✗ Not found in 22 relevant answers</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output warn">⚠ Competitor "Brand X" appears in 67% of answers</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output">Running GEO Foundation...</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-output">8 weeks later:</span></div>
              <div className="t-line"><span className="t-output good">✓ Found in 34 ChatGPT answers</span></div>
              <div className="t-line"><span className="t-output good">✓ Found in 28 Gemini answers</span></div>
              <div className="t-line"><span className="t-output good">✓ Found in 19 Perplexity answers</span></div>
              <div className="t-gap"></div>
              <div className="t-line"><span className="t-prompt">$ </span><span className="t-cursor"></span></div>
            </div>
          </div>
        </div>

        <div className="hero-scroll">Scroll</div>
      </section>

      <div className="sep"></div>

      {/* WHY GEO */}
      <section className="why" id="why">
        <div className="sec-eyebrow">The Shift</div>
        <h2 className="sec-title">Search has <em>changed.</em><br/>Has your strategy?</h2>
        <p className="sec-desc">People no longer just Google. They ask AI. And AI doesn't show a list of links — it picks one answer. That answer needs to be you.</p>

        <div className="why-grid">
          <div className="why-cell">
            <div className="why-icon">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            </div>
            <h3>The Way People Search is Changing</h3>
            <p>Over 40% of Gen Z now starts research on AI tools rather than search engines. By 2027, AI-generated answers will influence the majority of purchase decisions online.</p>
          </div>
          <div className="why-cell">
            <div className="why-icon">
              <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <h3>AI Picks One Answer — Not Ten</h3>
            <p>Google shows 10 blue links. AI gives one confident answer. If your brand isn't in that answer, you are completely invisible to that potential customer. There is no page 2.</p>
          </div>
          <div className="why-cell">
            <div className="why-icon">
              <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            </div>
            <h3>Early Movers Own the Category</h3>
            <p>AI models learn from the web. The brands that establish themselves now — with clear language, authoritative content, and strong citation signals — will own their category in AI answers for years.</p>
          </div>
          <div className="why-cell">
            <div className="why-icon">
              <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <h3>Your Competitors Haven't Started Yet</h3>
            <p>GEO is where SEO was in 2004. Most businesses have no strategy. Most agencies don't even offer it. The window to get ahead is open right now — but it will not stay open for long.</p>
          </div>
        </div>
      </section>

      <div className="sep"></div>

      {/* SERVICES */}
      <section className="services" id="services">
        <div className="sec-eyebrow">What We Do</div>
        <h2 className="sec-title">Three services.<br/><em>One outcome.</em></h2>
        <p className="sec-desc">Every engagement is designed to get your brand appearing in AI answers — and staying there.</p>

        <div className="services-list">
          <div className="svc-row">
            <div className="svc-num">01</div>
            <div className="svc-name">GEO Audit</div>
            <div className="svc-desc">We ask 50–100 questions relevant to your business across ChatGPT, Claude, Gemini and Perplexity. You get a full report showing where you're invisible, who's appearing instead of you, and exactly what needs to change.</div>
            <div className="svc-outcome">Clarity</div>
          </div>
          <div className="svc-row">
            <div className="svc-num">02</div>
            <div className="svc-name">GEO Foundation</div>
            <div className="svc-desc">The full setup. We rewrite your key pages for AI clarity, add schema markup, build a library of Q&A content, and secure citations on sources AI models trust. This is what gets you appearing in answers.</div>
            <div className="svc-outcome">Visibility</div>
          </div>
          <div className="svc-row">
            <div className="svc-num">03</div>
            <div className="svc-name">GEO Retainer</div>
            <div className="svc-desc">Monthly monitoring, content updates, and citation expansion. We track every AI platform weekly, measure your visibility score, and keep optimising as the AI landscape evolves.</div>
            <div className="svc-outcome">Dominance</div>
          </div>
        </div>
      </section>

      <div className="sep"></div>

      {/* PROCESS */}
      <section className="process" id="process">
        <div className="sec-eyebrow">How It Works</div>
        <h2 className="sec-title">From <em>invisible</em><br/>to cited. In 8 weeks.</h2>
        <p className="sec-desc">A structured, repeatable process that works across any industry, any market, any language.</p>

        <div className="process-grid">
          <div className="process-step">
            <div className="p-num">01</div>
            <div className="p-tag">Week 1–2</div>
            <h4>Audit & Discovery</h4>
            <p>We run a deep audit across all major AI platforms. We map your current visibility, identify the gaps, and benchmark against competitors appearing in your space.</p>
          </div>
          <div className="process-step">
            <div className="p-num">02</div>
            <div className="p-tag">Week 2–3</div>
            <h4>Language & Structure</h4>
            <p>We rewrite your website's key pages in clear, definitional language. We add schema markup and structured data that tells AI crawlers exactly what you do and who you serve.</p>
          </div>
          <div className="process-step">
            <div className="p-num">03</div>
            <div className="p-tag">Week 3–6</div>
            <h4>Content & Citations</h4>
            <p>We create a library of 30–50 Q&A pieces matching real AI queries. We secure mentions on trusted sources — directories, publications, LinkedIn, niche communities — that AI models cite.</p>
          </div>
          <div className="process-step">
            <div className="p-num">04</div>
            <div className="p-tag">Week 6–8+</div>
            <h4>Monitor & Compound</h4>
            <p>We track your AI visibility score weekly. We report on which queries you're now appearing in. We continue building citations and content to compound your presence over time.</p>
          </div>
        </div>
      </section>

      <div className="sep"></div>

      {/* GEO VS SEO */}
      <section className="compare" id="compare">
        <div className="sec-eyebrow">The Difference</div>
        <h2 className="sec-title">GEO vs <em>SEO</em></h2>
        <p className="sec-desc">Both matter. But GEO is where the next decade of discovery is being built. Here's how they compare.</p>

        <table className="compare-table">
          <thead>
            <tr>
              <th></th>
              <th className="lime">GEO — Generative Engine Optimisation</th>
              <th className="dim">SEO — Search Engine Optimisation</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Goal</td>
              <td className="geo-val">Be cited in AI-generated answers</td>
              <td className="seo-val">Rank on Google search results page</td>
            </tr>
            <tr>
              <td>Where it shows</td>
              <td className="geo-val">ChatGPT, Claude, Gemini, Perplexity, AI Overviews</td>
              <td className="seo-val">Google, Bing search results</td>
            </tr>
            <tr>
              <td>Format</td>
              <td className="geo-val">Definitional content, Q&A, schema, citations</td>
              <td className="seo-val">Keywords, backlinks, page authority</td>
            </tr>
            <tr>
              <td>Competition level</td>
              <td className="geo-val">Very low — most brands haven't started</td>
              <td className="seo-val">Extremely high — every brand competing</td>
            </tr>
            <tr>
              <td>Result format</td>
              <td className="geo-val">One definitive answer — your brand</td>
              <td className="seo-val">A list of 10 links — your brand is one of many</td>
            </tr>
            <tr>
              <td>Future trajectory</td>
              <td className="geo-val">Growing rapidly with AI adoption</td>
              <td className="seo-val">Gradually declining as AI answers replace clicks</td>
            </tr>
            <tr>
              <td>Time to results</td>
              <td className="geo-val">6–10 weeks to initial visibility</td>
              <td className="seo-val">3–12 months to meaningful rankings</td>
            </tr>
          </tbody>
        </table>
      </section>

      <div className="sep"></div>

      {/* WHO WE SERVE */}
      <section className="clients" id="clients">
        <div className="sec-eyebrow">Who We Serve</div>
        <h2 className="sec-title">Built for brands<br/>ready to be <em>found.</em></h2>
        <p className="sec-desc">Any business that wants to appear when someone asks an AI about their industry. Here are the clients we work with best.</p>

        <div className="clients-grid">
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            </div>
            <h4>D2C & E-Commerce Brands</h4>
            <p>Jewellery, fashion, food, beauty — brands that want to appear when someone asks "best [product] brand in [city/country]."</p>
            <div className="client-example">e.g. Jewellery, Skincare, Apparel</div>
          </div>
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            </div>
            <h4>B2B SaaS Products</h4>
            <p>Software tools that want to appear when someone asks "best tool for X" — getting cited as the recommended solution in their category.</p>
            <div className="client-example">e.g. Settle AI, AdornIQ, HR Tools</div>
          </div>
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><path d="M20 7h-9"/><path d="M14 17H5"/><circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/></svg>
            </div>
            <h4>Professional Services</h4>
            <p>Consultants, CA firms, law firms, coaches — professionals who want AI to recommend them when someone asks for expertise in their field.</p>
            <div className="client-example">e.g. Finance, Legal, Consulting</div>
          </div>
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </div>
            <h4>Local Businesses</h4>
            <p>Clinics, restaurants, agencies — businesses that want to appear when someone asks "best [service] in [city]" inside an AI tool.</p>
            <div className="client-example">e.g. Clinics, Restaurants, Agencies</div>
          </div>
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            </div>
            <h4>MSME & Trade Businesses</h4>
            <p>Wholesalers, manufacturers, distributors in South Asian markets who want to be found by buyers searching on AI platforms.</p>
            <div className="client-example">e.g. Jewellery Wholesale, Textiles</div>
          </div>
          <div className="client-card">
            <div className="client-icon">
              <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <h4>Marketing Agencies</h4>
            <p>Agencies that want to white-label GEO and offer it as a service to their existing clients — adding a new, high-margin revenue stream.</p>
            <div className="client-example">e.g. Digital Agencies, PR Firms</div>
          </div>
        </div>
      </section>

      {/* FOOTER - BrandsXAI */}
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
