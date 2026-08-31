import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { SessionProvider, SessionContext } from './context/SessionContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Recommendations from './pages/Recommendations';
import FoodDetail from './pages/FoodDetail';
import Checkout from './pages/Checkout';
import Favorites from './pages/Favorites';
import Orders from './pages/Orders';
import Profile from './pages/Profile';
import './App.css';

// The home route shows the taste game ONLY until the user has played once.
// After that, "/" opens straight to Discover (recommendations). The game stays
// replayable via the dedicated /game route (e.g. the "Retake quiz" button).
const HomeGate = () => {
    const { hasPlayedGame } = useContext(SessionContext);
    return hasPlayedGame ? <Navigate to="/recommendations" replace /> : <Home />;
};

function App() {
    return (
        <SessionProvider>
            <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <div className="app">
                    <Navbar />
                    <AnimatePresence mode="wait">
                        <Routes>
                            <Route path="/" element={<HomeGate />} />
                            <Route path="/game" element={<Home />} />
                            <Route path="/recommendations" element={<Recommendations />} />
                            <Route path="/food/:foodId" element={<FoodDetail />} />
                            <Route path="/favorites" element={<Favorites />} />
                            <Route path="/orders" element={<Orders />} />
                            <Route path="/profile" element={<Profile />} />
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
