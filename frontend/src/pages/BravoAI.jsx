import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './BravoAI.css';

const BravoAI = () => {
  return (
    <div className="bravo-page">
      {/* NAV */}
      <nav className="bravo-nav">
        <Link to="/" className="back-link">
          <ArrowLeft size={20} />
          <span>Back to BrandsXAI</span>
        </Link>
        <div className="nav-logo">
          <span className="nav-logo-accent">BRAVO</span>&nbsp;AI
        </div>
        <ul className="nav-links">
          <li><a href="#what">What We Do</a></li>
          <li><a href="#how">How It Works</a></li>
          <li><a href="#qualify">Lead Qualifier</a></li>
          <li><a href="#who">Who It's For</a></li>
          <li><Link to="/contact" className="nav-cta">Launch Campaign</Link></li>
        </ul>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-slash"></div>
        <div className="hero-bg-text">BRAVO</div>
        <div className="hero-vlines">
          <div className="vline"></div><div className="vline"></div>
          <div className="vline"></div><div className="vline"></div>
          <div className="vline"></div><div className="vline"></div>
          <div className="vline"></div><div className="vline"></div>
        </div>

        <div className="hero-content">
          <div className="hero-pre">BRAnding with VOice AI</div>
          <h1>
            <span className="word-bravo">BRAVO</span><br/>
            <span className="word-outline">VOICE</span>&nbsp;<span className="word-ai">AI</span>
          </h1>
          <div className="hero-sub-row">
            <p className="hero-tagline">
              Your brand calls. Your prospects listen.<br/>
              <strong>BRAVO AI runs outbound campaigns, qualifies leads at scale, and hands your sales team only the ones ready to close.</strong>
            </p>
            <div className="hero-ctas">
              <a href="#what" className="btn-accent">
                <span>See It In Action</span>
                <span>→</span>
              </a>
              <a href="#how" className="btn-ghost">
                <span>How It Works</span>
              </a>
            </div>
          </div>
        </div>

        <div className="hero-stats-bar">
          <div className="stat-block">
            <span className="stat-n">500+</span>
            <span className="stat-l">Calls Per Day</span>
          </div>
          <div className="stat-block">
            <span className="stat-n">3×</span>
            <span className="stat-l">More Qualified Leads</span>
          </div>
          <div className="stat-block">
            <span className="stat-n">24/7</span>
            <span className="stat-l">Always On</span>
          </div>
          <div className="stat-block">
            <span className="stat-n">0</span>
            <span className="stat-l">Leads Missed</span>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* WHAT IT DOES */}
      <section className="what" id="what">
        <div className="sec-eyebrow">What Bravo AI Does</div>
        <h2 className="sec-title">THREE WEAPONS.<br/><em>ONE MISSION.</em></h2>
        <p className="sec-desc">BRAVO AI handles your entire outbound pipeline — from first contact to qualified handoff — so your team only ever deals with prospects ready to buy.</p>

        <div className="what-grid">
          <div className="what-card">
            <div className="what-num">01</div>
            <div className="what-icon">
              <svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.61a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            </div>
            <span className="what-tag">Outbound</span>
            <h3>Campaign Calling</h3>
            <p>BRAVO AI dials hundreds of prospects daily — introducing your brand, delivering your message with perfect consistency, and sparking real conversations at scale.</p>
            <div className="what-outcome">Outcome: Brand Awareness at Scale</div>
          </div>

          <div className="what-card">
            <div className="what-num">02</div>
            <div className="what-icon">
              <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <span className="what-tag">Intelligence</span>
            <h3>Lead Qualification</h3>
            <p>Every call is a qualification interview. BRAVO AI listens, asks the right questions, and scores each prospect — so you always know who's hot, who's warm, and who needs nurturing.</p>
            <div className="what-outcome">Outcome: Scored, Segmented Pipeline</div>
          </div>

          <div className="what-card">
            <div className="what-num">03</div>
            <div className="what-icon">
              <svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            </div>
            <span className="what-tag">Handoff</span>
            <h3>Sales Handoff</h3>
            <p>When a lead is ready, BRAVO AI hands them to your sales team with a full brief — what was said, their interest level, their objections, and the best approach to close.</p>
            <div className="what-outcome">Outcome: Sales-Ready Leads Only</div>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="sec-eyebrow">The Process</div>
        <h2 className="sec-title">FROM COLD LIST<br/>TO <em>CLOSED DEAL.</em></h2>
        <p className="sec-desc">A five-step pipeline that runs automatically — day and night — turning your prospect list into revenue.</p>

        <div className="flow-track">
          <div className="flow-item">
            <div className="flow-dot">01</div>
            <div className="flow-body">
              <h4>Campaign is Launched</h4>
              <p>You upload your prospect list and brief. BRAVO AI learns your brand voice, your campaign message, and your qualification criteria in minutes.</p>
              <span className="flow-badge">Setup in Minutes</span>
            </div>
          </div>
          <div className="flow-item">
            <div className="flow-dot">02</div>
            <div className="flow-body">
              <h4>Bravo AI Calls at Scale</h4>
              <p>The agent dials every prospect — introducing your brand naturally, delivering the campaign message, and opening a real two-way conversation. 500+ calls a day, consistently.</p>
              <span className="flow-badge">Voice AI Outbound</span>
            </div>
          </div>
          <div className="flow-item">
            <div className="flow-dot">03</div>
            <div className="flow-body">
              <h4>Qualifies Every Conversation</h4>
              <p>During each call, BRAVO AI asks intelligent questions, listens to responses, and scores the lead in real time — interest level, budget signals, timeline, decision authority.</p>
              <span className="flow-badge">AI Qualification Engine</span>
            </div>
          </div>
          <div className="flow-item">
            <div className="flow-dot">04</div>
            <div className="flow-body">
              <h4>Routes to the Right Bucket</h4>
              <p>Every lead is placed in one of three buckets — Hot (ready now), Warm (follow up), or Nurture (longer term). Each bucket triggers a different automated action instantly.</p>
              <span className="flow-badge">Smart Routing</span>
            </div>
          </div>
          <div className="flow-item">
            <div className="flow-dot">05</div>
            <div className="flow-body">
              <h4>Hands Off to Your Sales Team</h4>
              <p>Hot leads are sent to your team with a complete brief — what they said, what they want, what their objection is, and how to close. Your team walks in to win, not to pitch cold.</p>
              <span className="flow-badge">Warm Handoff</span>
            </div>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* LEAD QUALIFICATION */}
      <section className="qualify" id="qualify">
        <div className="sec-eyebrow">The Qualifier</div>
        <h2 className="sec-title">EVERY LEAD.<br/><em>SCORED. ROUTED. READY.</em></h2>
        <p className="sec-desc">BRAVO AI doesn't just call — it thinks. Every conversation ends with a clear verdict on where the lead stands and exactly what happens next.</p>

        <div className="qualify-grid">
          <div className="q-bucket hot">
            <div className="q-signal"><div className="q-dot"></div> Hot Lead</div>
            <h3>Ready to Buy</h3>
            <div className="q-sub">Immediate Handoff</div>
            <p>Prospect has shown clear interest, fits the profile, and is ready to speak with your team now. BRAVO AI notifies sales immediately with the full conversation brief.</p>
            <div className="q-action">Routed to Sales Instantly</div>
          </div>
          <div className="q-bucket warm">
            <div className="q-signal"><div className="q-dot"></div> Warm Lead</div>
            <h3>Needs a Nudge</h3>
            <div className="q-sub">Automated Follow-Up</div>
            <p>Prospect is interested but not ready yet — needs more time, information, or a second touchpoint. BRAVO AI schedules a follow-up call automatically and nurtures till ready.</p>
            <div className="q-action">Follow-Up Auto-Scheduled</div>
          </div>
          <div className="q-bucket nurture">
            <div className="q-signal"><div className="q-dot"></div> Nurture Lead</div>
            <h3>Long-Term Play</h3>
            <div className="q-sub">Drip Campaign</div>
            <p>Prospect is curious but not in buying mode yet. BRAVO AI adds them to a long-term nurture sequence — staying on their radar until the timing is right.</p>
            <div className="q-action">Added to Drip Sequence</div>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* CALL SIMULATION */}
      <section className="callsim" id="call">
        <div className="sec-eyebrow">Live Agent</div>
        <h2 className="sec-title">HEAR BRAVO AI<br/><em>IN ACTION.</em></h2>
        <p className="sec-desc">Natural. Confident. On-brand. BRAVO AI sounds like your best sales rep — every single time.</p>

        <div className="call-wrap">
          <div className="call-window">
            <div className="call-topbar">
              <div className="call-live">
                <div className="call-live-dot"></div>
                Live Call
              </div>
              <span className="call-label">Bravo AI — Outbound Campaign Simulation</span>
            </div>
            <div className="call-body">
              <div className="call-line">
                <span className="call-who">Bravo AI</span>
                <div className="call-text agent">Hi, am I speaking with Priya? I'm calling on behalf of [Your Brand]. We help D2C businesses like yours scale customer outreach using AI — I wanted to take 60 seconds to see if it's relevant to you?</div>
              </div>
              <div className="call-line">
                <span className="call-who prospect">Priya</span>
                <div className="call-text">Yeah sure, go ahead.</div>
              </div>
              <div className="call-line">
                <span className="call-who">Bravo AI</span>
                <div className="call-text agent">Great. Most of our clients were spending 4–5 hours a day on manual follow-ups. We cut that to 30 minutes — while tripling the number of prospects they reach. Are you currently running any outbound campaigns?</div>
              </div>
              <div className="call-line">
                <span className="call-who prospect">Priya</span>
                <div className="call-text">We do some email and a bit of cold calling but nothing structured.</div>
              </div>
              <div className="call-line">
                <span className="call-who">Bravo AI</span>
                <div className="call-text agent">That's exactly where we add the most value. Would it make sense to set up a quick 15-minute call with our team this week to walk you through how it works?</div>
              </div>
              <div className="call-result">Hot Lead — Qualified & Routed to Sales with Full Brief</div>
            </div>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* WHO IT'S FOR */}
      <section className="who" id="who">
        <div className="sec-eyebrow">Who It's For</div>
        <h2 className="sec-title">BUILT FOR BRANDS<br/><em>THAT MEAN BUSINESS.</em></h2>
        <p className="sec-desc">If you have a product, a target market, and a sales team — BRAVO AI is your unfair advantage.</p>

        <div className="who-grid">
          <div className="who-card">
            <div className="who-icon-wrap">
              <svg viewBox="0 0 24 24"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            </div>
            <h4>D2C Brands</h4>
            <p>Scale your outreach beyond email. Reach thousands of potential customers with a voice that carries your brand's personality.</p>
          </div>
          <div className="who-card">
            <div className="who-icon-wrap">
              <svg viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            </div>
            <h4>B2B Companies</h4>
            <p>Replace cold email with warm voice outreach. Qualify decision-makers before your sales reps ever pick up the phone.</p>
          </div>
          <div className="who-card">
            <div className="who-icon-wrap">
              <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </div>
            <h4>Real Estate & Finance</h4>
            <p>High-value deals need warm leads. BRAVO AI qualifies interest and intent before your consultants invest their time.</p>
          </div>
          <div className="who-card">
            <div className="who-icon-wrap">
              <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <h4>Agencies & SaaS</h4>
            <p>Run client acquisition campaigns at scale. BRAVO AI fills your demo calendar with qualified prospects who already know your pitch.</p>
          </div>
        </div>
      </section>

      <div className="slash-divider"></div>

      {/* FOOTER - BrandsXAI */}
      <footer className="bravo-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3 className="footer-logo">BrandsXAI</h3>
            <p className="footer-tagline">BrandsXAI is the next step on our mission to make AI better for everyone.</p>
          </div>
          
          <div className="footer-links-grid">
            <div className="footer-col">
              <h4>Bravo AI</h4>
              <a href="#what">What We Do</a>
              <a href="#how">How It Works</a>
              <a href="#qualify">Lead Qualifier</a>
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

export default BravoAI;
