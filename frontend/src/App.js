import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomeNew from "./pages/HomeNew";
import About from "./pages/About";
import CaseStudy from "./pages/CaseStudy";
import Contact from "./pages/Contact";
import Login from "./pages/Login";
import AdminLogin from "./pages/AdminLogin";
import AdminPortal from "./pages/AdminPortal";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomeNew />} />
          <Route path="/about" element={<About />} />
          <Route path="/case-study/:id" element={<CaseStudy />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/login" element={<Login />} />
          
          {/* Admin Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/portal" element={<AdminPortal />} />
          
          {/* User Dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
