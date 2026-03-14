import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './SettleAI.css';

const SettleAI = () => {
  return (
    <div className="settle-container">
      {/* NAV */}
      <nav className="settle-nav">
        <Link to="/" className="settle-back">
          <ArrowLeft size={20} />
          <span>Back to BrandsXAI</span>
        </Link>
        <div className="settle-logo">Settle <em>AI</em></div>
        <div className="settle-nav-links">
          <a href="#how">How It Works</a>
          <a href="#qualify">The Agent</a>
          <a href="#impact">Impact</a>
          <a href="#contact" className="nav-cta">Get Started</a>
        </div>
      </nav>

      {/* HERO */}
      <section className="settle-hero">
        <div className="hero-bg"></div>
        <div className="hero-wave"></div>
        <div className="hero-wave"></div>
        <div className="hero-wave"></div>
        <div className="hero-dot"></div>
        <div className="hero-dot"></div>
        <div className="hero-dot"></div>

        <div className="hero-content">
          <div className="hero-eyebrow">AI-Powered Collections Agent</div>
          <h1>Recover Your<br /><em>Udhaar.</em> Peacefully.</h1>

          <p className="hero-tagline">
            A peaceful AI agent that calls, qualifies, and hands warm recovery leads to your team — so money comes back without breaking relationships.
          </p>

          <div className="hero-stats">
            <div className="stat-item">
              <span className="stat-num">3x</span>
              <span className="stat-label">Faster Recovery</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">100+</span>
              <span className="stat-label">Calls per Day</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">0</span>
              <span className="stat-label">Awkward Moments</span>
            </div>
          </div>

          <div className="hero-ctas">
            <a href="#how" className="btn-primary"><span>See How It Works</span><span>→</span></a>
            <a href="#qualify" className="btn-outline"><span>Meet the Agent</span></a>
          </div>
        </div>

        <div className="hero-scroll">Scroll</div>
      </section>

      <div className="blue-line"></div>
      <div className="divider"><div className="divider-mark"></div></div>
      <div className="blue-line"></div>

      {/* PROBLEM */}
      <section className="problem" id="problem">
        <div className="section-label">The Problem</div>
        <h2 className="section-title">The <em>Udhaar</em> Trap<br />Every Wholesaler Knows</h2>
        <p className="section-desc">Goods go out. Money comes in slowly — or not at all. And chasing it yourself risks the very relationships that built your business.</p>

        <div className="problem-grid">
          <ul className="problem-list">
            <li>
              <span className="icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="2" width="6" height="4" rx="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="m9 14 2 2 4-4"></path></svg>
              </span>
              <span>No clear record of who took what, when, and for how much — everything lives in memory or a scattered diary.</span>
            </li>
            <li>
              <span className="icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07"></path><path d="M14.5 2.5s4 0 4 5"></path><path d="m2 2 20 20"></path></svg>
              </span>
              <span>Manual follow-ups are exhausting, inconsistent, and easy to avoid when the relationship feels personal.</span>
            </li>
            <li>
              <span className="icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="12" x="2" y="6" rx="2"></rect><circle cx="12" cy="12" r="2"></circle><path d="M6 12h.01M18 12h.01"></path></svg>
              </span>
              <span>Money stuck for 3–6 months creates a cash flow crisis that limits what you can buy, stock, and sell.</span>
            </li>
            <li>
              <span className="icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
              </span>
              <span>Aggressive recovery risks damaging community relationships and your reputation in the market.</span>
            </li>
            <li>
              <span className="icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" x2="18" y1="20" y2="10"></line><line x1="12" x2="12" y1="20" y2="4"></line><line x1="6" x2="6" y1="20" y2="14"></line></svg>
              </span>
              <span>No data means no way to know who is reliable, who to trust with more credit, and who to stop supplying.</span>
            </li>
          </ul>

          <div className="problem-callout">
            <blockquote>
              "I know he owes me ₹2 lakhs — but I see him at the market every week. How do I chase without making it awkward?"
            </blockquote>
            <cite>— Every jewellery wholesaler, everywhere</cite>
          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="section-label">The Journey</div>
        <h2 className="section-title">How <em>Settle AI</em> Works</h2>
        <p className="section-desc">A five-step flow that takes an overdue account from outstanding to settled — with your team stepping in only when it truly matters.</p>

        <div className="flow-wrapper">
          <div className="flow-steps">

            <div className="flow-step">
              <div className="flow-num">1</div>
              <div className="flow-body">
                <h4>Account is Logged</h4>
                <p>You enter who took goods, which items, the amount, and the date. Settle AI creates a full account record and starts the clock. No spreadsheet needed — a simple, clean interface.</p>
                <span className="flow-tag">Tracker</span>
              </div>
            </div>

            <div className="flow-step">
              <div className="flow-num">2</div>
              <div className="flow-body">
                <h4>WhatsApp Reminder Fires</h4>
                <p>At 7 days, a warm, respectful WhatsApp message goes out automatically in the right language — Hindi, Urdu, or English. Personalised with their name and amount. No action needed from you.</p>
                <span className="flow-tag">WhatsApp Agent</span>
              </div>
            </div>

            <div className="flow-step">
              <div className="flow-num">3</div>
              <div className="flow-body">
                <h4>AI Voice Agent Calls</h4>
                <p>No response in 3 days? The AI agent calls the person directly. It speaks naturally, listens carefully, and handles the conversation — explaining the outstanding amount, asking about payment timing, and offering options.</p>
                <span className="flow-tag">Voice AI Agent</span>
              </div>
            </div>

            <div className="flow-step">
              <div className="flow-num">4</div>
              <div className="flow-body">
                <h4>Qualifies the Outcome</h4>
                <p>Based on the conversation, the agent places the account into one of three buckets — Ready to Pay, Needs More Time, or Needs Human Attention. Each bucket triggers a different automated action.</p>
                <span className="flow-tag">AI Qualification</span>
              </div>
            </div>

            <div className="flow-step">
              <div className="flow-num">5</div>
              <div className="flow-body">
                <h4>Your Team Steps In — Only When Ready</h4>
                <p>For escalated cases, your team receives a complete brief — what was said, what was disputed, the tone of the conversation, and the recommended approach. You walk in prepared, not blind.</p>
                <span className="flow-tag">Human Handoff</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* QUALIFICATION BUCKETS */}
      <section className="qualify" id="qualify">
        <div className="section-label">The Agent</div>
        <h2 className="section-title">Three <em>Buckets.</em><br />Every Call Resolved.</h2>
        <p className="section-desc">Like a sales lead qualifier, Settle AI scores every conversation and routes it to the right outcome — automatically.</p>

        <div className="buckets-grid">
          <div className="bucket green">
            <div className="bucket-badge"><div className="bucket-dot"></div> Hot — Ready</div>
            <h3>Will Pay Now</h3>
            <div className="bucket-sub">Immediate Action</div>
            <p>Person confirms they have the money and are ready to settle. Agent sends a payment link on WhatsApp immediately and marks the account as pending closure.</p>
            <div className="bucket-action">Payment link sent instantly</div>
          </div>

          <div className="bucket yellow">
            <div className="bucket-badge"><div className="bucket-dot"></div> Warm — Nurturing</div>
            <h3>Needs More Time</h3>
            <div className="bucket-sub">Scheduled Follow-Up</div>
            <p>Person asks for an extension or partial payment. Agent records the commitment date, schedules a follow-up call automatically, and continues nurturing until ready.</p>
            <div className="bucket-action">Follow-up auto-scheduled</div>
          </div>

          <div className="bucket red">
            <div className="bucket-badge"><div className="bucket-dot"></div> Cold — Escalate</div>
            <h3>Needs Human</h3>
            <div className="bucket-sub">Briefed Handoff</div>
            <p>Person disputes the amount, is unresponsive, or the situation requires a trusted human touch. Agent compiles a full brief and hands to your team — prepared, calm, and informed.</p>
            <div className="bucket-action">Full brief sent to your team</div>
          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* CALL SAMPLE */}
      <section className="callsample" id="agent">
        <div className="section-label">Live Agent</div>
        <h2 className="section-title">How the <em>Conversation</em> Sounds</h2>
        <p className="section-desc">Natural. Respectful. Effective. The agent never pressures — it simply informs, listens, and guides.</p>

        <div className="call-window">
          <div className="call-topbar">
            <div className="call-indicator"></div>
            <span className="call-topbar-text">Settle AI — Live Call Simulation</span>
          </div>
          <div className="call-body">

            <div className="call-line">
              <span className="call-who">Agent</span>
              <div className="call-text agent">Namaste, main Settle AI ki taraf se Sharma Jewellers ke liye bol raha hoon. Kya main Ramesh ji se baat kar sakta hoon?</div>
            </div>

            <div className="call-line">
              <span className="call-who human">Ramesh</span>
              <div className="call-text">Haan, main hi bol raha hoon.</div>
            </div>

            <div className="call-line">
              <span className="call-who">Agent</span>
              <div className="call-text agent">Ramesh ji, aapke paas hamare ₹1,85,000 outstanding hain jo 14 January se pending hain. Kya aap is baare mein thodi baat kar sakte hain?</div>
            </div>

            <div className="call-line">
              <span className="call-who human">Ramesh</span>
              <div className="call-text">Haan bhai, mujhe pata hai. Thoda time chahiye — is mahine ke end tak de sakte ho?</div>
            </div>

            <div className="call-line">
              <span className="call-who">Agent</span>
              <div className="call-text agent">Bilkul Ramesh ji. Main 31 March ka date note kar leta hoon. Ek reminder 3 din pehle bhi bhejunga. Kya partial payment abhi possible hai — ₹50,000? Remaining end of month?</div>
            </div>

            <div className="call-outcome">
              Account qualified as Warm. Partial payment date set. Follow-up scheduled for 28 March automatically.
            </div>

          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* IMPACT */}
      <section className="impact" id="impact">
        <div className="section-label">The Results</div>
        <h2 className="section-title">Before & After<br /><em>Settle AI</em></h2>
        <p className="section-desc">The difference is not just in numbers — it's in how your business feels to run every single day.</p>

        <div className="impact-grid">
          <div className="impact-cell">
            <div className="impact-cell-title">Time & Effort</div>
            <table>
              <tbody>
                <tr><th>Metric</th><th>Before</th><th>After</th></tr>
                <tr><td>Follow-up calls per day</td><td className="bad">5–10 manual</td><td className="good">100+ automated</td></tr>
                <tr><td>Staff time on collections</td><td className="bad">4–5 hrs/day</td><td className="good">30 min/day</td></tr>
                <tr><td>Missed follow-ups</td><td className="bad">Very common</td><td className="good">Zero</td></tr>
                <tr><td>Records accuracy</td><td className="bad">Memory / diary</td><td className="good">100% tracked</td></tr>
              </tbody>
            </table>
          </div>
          <div className="impact-cell">
            <div className="impact-cell-title">Money & Recovery</div>
            <table>
              <tbody>
                <tr><th>Metric</th><th>Before</th><th>After</th></tr>
                <tr><td>Average recovery time</td><td className="bad">3–6 months</td><td className="good">3–6 weeks</td></tr>
                <tr><td>Bad debt rate</td><td className="bad">High</td><td className="good">Significantly reduced</td></tr>
                <tr><td>Cash flow visibility</td><td className="bad">None</td><td className="good">Real-time dashboard</td></tr>
                <tr><td>Credit decision quality</td><td className="bad">Gut feel</td><td className="good">Data-driven</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* WHO BENEFITS */}
      <section className="who" id="who">
        <div className="section-label">Who It's For</div>
        <h2 className="section-title">Built for <em>Every Player</em><br />in the Trade.</h2>
        <p className="section-desc">Settle AI serves everyone in the jewellery and wholesale supply chain — from the owner to the accountant.</p>

        <div className="who-grid">
          <div className="who-card">
            <span className="who-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            </span>
            <div className="who-title">Wholesaler</div>
            <p className="who-desc">Cash flow clarity, less stress, money recovered faster without personal confrontation.</p>
          </div>
          <div className="who-card">
            <span className="who-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="14" x="2" y="7" rx="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
            </span>
            <div className="who-title">Sales Staff</div>
            <p className="who-desc">Clear call scripts, no confusion on who owes what, never walk into a conversation unprepared.</p>
          </div>
          <div className="who-card">
            <span className="who-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"></path><path d="M14 8H8"></path><path d="M16 12H8"></path><path d="M13 16H8"></path></svg>
            </span>
            <div className="who-title">Accountant</div>
            <p className="who-desc">Clean reports, automated reconciliation, full audit trail of every call and commitment.</p>
          </div>
          <div className="who-card">
            <span className="who-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7EC8C8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20.42 4.58a5.4 5.4 0 0 0-7.65 0l-.77.78-.77-.78a5.4 5.4 0 0 0-7.65 7.65l8.42 8.42 8.42-8.42a5.4 5.4 0 0 0 0-7.65z"></path></svg>
            </span>
            <div className="who-title">Retailer / Seller</div>
            <p className="who-desc">Gets timely, respectful reminders so dues never pile up into an uncomfortable surprise.</p>
          </div>
        </div>
      </section>

      <div className="blue-line"></div>

      {/* CTA */}
      <section className="settle-cta" id="contact">
        <h2>Ready to Recover Your Money?</h2>
        <p>Join wholesalers who are already using Settle AI to get their cash flow back on track.</p>
        <Link to="/contact" className="btn-primary"><span>Get Started Today</span><span>→</span></Link>
      </section>

      <div className="blue-line"></div>
      <div className="divider"><div className="divider-mark"></div></div>
      <div className="blue-line"></div>

      {/* FOOTER - BrandsXAI */}
      <footer className="settle-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3 className="footer-logo">BrandsXAI</h3>
            <p className="footer-tagline">BrandsXAI is the next step on our mission to make AI better for everyone.</p>
          </div>
          
          <div className="footer-links-grid">
            <div className="footer-col">
              <h4>Settle AI</h4>
              <a href="#how">How It Works</a>
              <a href="#qualify">The Agent</a>
              <a href="#impact">Impact</a>
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

export default SettleAI;
