import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomeNew from "./pages/HomeNew";
import About from "./pages/About";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomeNew />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
