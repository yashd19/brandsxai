import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [formStatus, setFormStatus] = useState({ loading: false, error: '' });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormStatus({ loading: true, error: '' });

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Invalid username or password');
      }

      const data = await response.json();

      // Store token and user data in localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user_data', JSON.stringify({
        user: data.user,
        brand: data.brand,
        features: data.features
      }));
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      setFormStatus({ loading: false, error: error.message });
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        {/* Logo */}
        <Link to="/" className="login-logo">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 4C12.954 4 4 12.954 4 24s8.954 20 20 20c4.125 0 7.968-1.252 11.157-3.396" stroke="#5534eb" strokeWidth="4" strokeLinecap="round"/>
            <path d="M24 14c-5.523 0-10 4.477-10 10s4.477 10 10 10" stroke="#5534eb" strokeWidth="4" strokeLinecap="round"/>
          </svg>
        </Link>

        {/* Heading */}
        <h2 className="login-title">Sign in to MadOver AI</h2>
        <p className="login-subtitle">Enter your credentials to continue</p>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleInputChange}
            required
            className="login-input"
            data-testid="login-username-input"
            autoComplete="username"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
            required
            className="login-input"
            data-testid="login-password-input"
            autoComplete="current-password"
          />
          
          <button 
            type="submit" 
            className="login-submit-btn"
            disabled={formStatus.loading}
            data-testid="login-submit-btn"
          >
            {formStatus.loading ? 'Signing in...' : 'Continue'}
          </button>

          {formStatus.error && (
            <div className="login-error" data-testid="login-error-message">
              {formStatus.error}
            </div>
          )}
        </form>

        {/* Footer text */}
        <p className="login-terms">
          By continuing, you agree to the <a href="#">terms</a> and acknowledge the <a href="#">privacy policy</a>
        </p>
      </div>
    </div>
  );
};

export default Login;
