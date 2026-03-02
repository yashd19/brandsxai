import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Target, Users, Lightbulb, Award } from 'lucide-react';
import './About.css';

const About = () => {
  return (
    <div className="about-page">
      <div className="about-header">
        <Link to="/" className="back-button">
          <ArrowLeft size={20} />
          <span>Back to Home</span>
        </Link>
      </div>

      <div className="about-container">
        <div className="about-hero">
          <h1 className="about-title">About Brands X AI</h1>
          <p className="about-subtitle">
            We're on a mission to empower brands with intelligent AI solutions that drive growth, efficiency, and innovation.
          </p>
        </div>

        <div className="about-content">
          <section className="about-section">
            <div className="section-icon">
              <Target size={32} />
            </div>
            <h2>Our Mission</h2>
            <p>
              At Brands X AI, we believe that every brand deserves access to cutting-edge artificial intelligence.
              Our mission is to democratize AI technology, making it accessible, practical, and transformative for
              businesses of all sizes.
            </p>
          </section>

          <section className="about-section">
            <div className="section-icon">
              <Lightbulb size={32} />
            </div>
            <h2>What We Do</h2>
            <p>
              We specialize in developing AI-powered solutions across multiple domains:
            </p>
            <ul className="features-list">
              <li><strong>Voice AI:</strong> Intelligent conversational interfaces for seamless customer interactions</li>
              <li><strong>Automation:</strong> Smart workflows that reduce manual effort and increase efficiency</li>
              <li><strong>Inventory Management:</strong> AI-driven optimization for stock control and supply chain</li>
              <li><strong>Analytics:</strong> Data-driven insights that fuel strategic decision-making</li>
            </ul>
          </section>

          <section className="about-section">
            <div className="section-icon">
              <Users size={32} />
            </div>
            <h2>Our Team</h2>
            <p>
              We're a diverse team of AI experts, engineers, and innovators passionate about solving real-world
              problems with technology. Our collective expertise spans machine learning, natural language processing,
              computer vision, and enterprise software development.
            </p>
          </section>

          <section className="about-section">
            <div className="section-icon">
              <Award size={32} />
            </div>
            <h2>Why Choose Us</h2>
            <div className="values-grid">
              <div className="value-card">
                <h3>Innovation First</h3>
                <p>We stay at the forefront of AI technology, constantly exploring new possibilities</p>
              </div>
              <div className="value-card">
                <h3>Customer Focused</h3>
                <p>Your success is our success. We build solutions tailored to your unique needs</p>
              </div>
              <div className="value-card">
                <h3>Results Driven</h3>
                <p>We measure our impact through tangible business outcomes and ROI</p>
              </div>
              <div className="value-card">
                <h3>Ethical AI</h3>
                <p>We're committed to responsible AI development that respects privacy and fairness</p>
              </div>
            </div>
          </section>

          <section className="about-cta">
            <h2>Ready to Transform Your Brand?</h2>
            <p>Let's explore how AI can revolutionize your business</p>
            <Link to="/" className="cta-button">
              Get Started
            </Link>
          </section>
        </div>
      </div>
    </div>
  );
};

export default About;
