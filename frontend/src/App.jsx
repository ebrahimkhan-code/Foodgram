import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { SessionProvider } from './context/SessionContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Recommendations from './pages/Recommendations';
import Checkout from './pages/Checkout';
import './App.css';

function App() {
    return (
        <SessionProvider>
            <Router>
                <div className="app">
                    <Navbar />
                    <AnimatePresence mode="wait">
                        <Routes>
                            <Route path="/" element={<Home />} />
                            <Route path="/recommendations" element={<Recommendations />} />
                            <Route path="/checkout" element={<Checkout />} />
                            <Route path="*" element={<Navigate to="/" />} />
                        </Routes>
                    </AnimatePresence>
                </div>
            </Router>
        </SessionProvider>
    );
}

export default App;