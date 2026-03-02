import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: ''
  });
  const [formStatus, setFormStatus] = useState({ loading: false, success: false, error: '' });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormStatus({ loading: true, success: false, error: '' });

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/leads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to submit form');
      }

      setFormStatus({ loading: false, success: true, error: '' });
      setFormData({ name: '', email: '', company: '', message: '' });
    } catch (error) {
      setFormStatus({ loading: false, success: false, error: error.message });
    }
  };

  return (
    <div className="contact-page">
      <div className="contact-container">
        {/* Logo */}
        <Link to="/" className="contact-logo">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 4C12.954 4 4 12.954 4 24s8.954 20 20 20c4.125 0 7.968-1.252 11.157-3.396" stroke="#5534eb" strokeWidth="4" strokeLinecap="round"/>
            <path d="M24 14c-5.523 0-10 4.477-10 10s4.477 10 10 10" stroke="#5534eb" strokeWidth="4" strokeLinecap="round"/>
          </svg>
        </Link>

        {/* Heading */}
        <h2 className="contact-title">Contact MadOver AI</h2>
        <p className="contact-subtitle">Tell us about your brand</p>

        {/* Form */}
        <form className="contact-form" onSubmit={handleSubmit}>
          <input
            type="text"
            name="name"
            placeholder="Enter your name"
            value={formData.name}
            onChange={handleInputChange}
            required
            className="contact-input"
            data-testid="contact-name-input"
          />
          <input
            type="email"
            name="email"
            placeholder="Enter your email"
            value={formData.email}
            onChange={handleInputChange}
            required
            className="contact-input"
            data-testid="contact-email-input"
          />
          <input
            type="text"
            name="company"
            placeholder="Enter your company name"
            value={formData.company}
            onChange={handleInputChange}
            className="contact-input"
            data-testid="contact-company-input"
          />
          <textarea
            name="message"
            placeholder="Tell us about your AI needs..."
            value={formData.message}
            onChange={handleInputChange}
            className="contact-textarea"
            rows={4}
            data-testid="contact-message-input"
          />
          
          <button 
            type="submit" 
            className="contact-submit-btn"
            disabled={formStatus.loading}
            data-testid="contact-submit-btn"
          >
            {formStatus.loading ? 'Sending...' : 'Continue'}
          </button>

          {formStatus.success && (
            <div className="contact-success" data-testid="contact-success-message">
              Thank you! We'll be in touch soon.
            </div>
          )}
          {formStatus.error && (
            <div className="contact-error" data-testid="contact-error-message">
              {formStatus.error}
            </div>
          )}
        </form>

        {/* Footer text */}
        <p className="contact-terms">
          By continuing, you agree to the <a href="#">terms</a> and acknowledge the <a href="#">privacy policy</a>
        </p>
      </div>
    </div>
  );
};

export default Contact;
