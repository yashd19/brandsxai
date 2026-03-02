import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './CaseStudy.css';

const CaseStudy = () => {
  const { id } = useParams();

  const caseStudies = {
    'revenue-churn': {
      category: 'ISPs & BSPs',
      title: 'Increase your revenue and reduce customer churn',
      subtitle: 'By introducing whole home consumer electronics protection plans',
      fullContent: `
        <h2>Challenge</h2>
        <p>Internet Service Providers and Broadband Service Providers face increasing customer churn and need new revenue streams to maintain profitability in a competitive market.</p>
        
        <h2>Solution</h2>
        <p>By introducing comprehensive whole home consumer electronics protection plans, ISPs can provide additional value to customers while creating new recurring revenue streams.</p>
        
        <h2>Results</h2>
        <ul>
          <li>45% reduction in customer churn</li>
          <li>$2.5M additional annual recurring revenue</li>
          <li>92% customer satisfaction rating</li>
          <li>Enhanced brand loyalty and customer lifetime value</li>
        </ul>
        
        <h2>Implementation</h2>
        <p>Our AI-powered platform enabled seamless integration with existing billing systems, automated claims processing, and intelligent pricing optimization based on usage patterns.</p>
      `,
      image: 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&q=80'
    },
    'brandcare': {
      category: 'Carriers & MVNOs',
      title: "Enable your brand to build your own 'BrandCare'",
      subtitle: 'By providing your customers with superior, turn-key Product Protection Offerings and Affordability programs',
      fullContent: `
        <h2>Challenge</h2>
        <p>Mobile carriers needed a way to differentiate their brand and provide comprehensive product protection that builds customer loyalty.</p>
        
        <h2>Solution</h2>
        <p>Our AI-powered BrandCare platform enables carriers to create white-label product protection programs that seamlessly integrate with their existing customer experience.</p>
        
        <h2>Results</h2>
        <ul>
          <li>300% increase in protection plan adoption</li>
          <li>65% improvement in customer retention</li>
          <li>$5M+ additional revenue in first year</li>
          <li>Industry-leading NPS scores</li>
        </ul>
        
        <h2>Key Features</h2>
        <p>AI-driven pricing, instant claims approval, predictive maintenance alerts, and seamless integration with existing systems.</p>
      `,
      image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80'
    }
  };

  const study = caseStudies[id];

  if (!study) {
    return <div className="case-study-page"><h1>Case Study Not Found</h1></div>;
  }

  return (
    <div className="case-study-page">
      <Link to="/" className="back-button">
        <ArrowLeft size={20} />
        <span>Back to Home</span>
      </Link>

      <div className="case-study-header" style={{ backgroundImage: `url(${study.image})` }}>
        <div className="header-overlay">
          <span className="category-badge">{study.category}</span>
          <h1 className="study-title">{study.title}</h1>
          <p className="study-subtitle">{study.subtitle}</p>
        </div>
      </div>

      <div className="case-study-content">
        <div dangerouslySetInnerHTML={{ __html: study.fullContent }} />
      </div>
    </div>
  );
};

export default CaseStudy;
