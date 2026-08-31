import React, { useContext, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';
import { 
    FaUtensils, 
    FaUser, 
    FaSignOutAlt,
    FaSignInAlt,
    FaUserPlus,
    FaHome,
    FaCompass,
    FaHeart,
    FaBars,
    FaTimes,
    FaCrown,
    FaTimesCircle
} from 'react-icons/fa';

const Navbar = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { isGuest, user, logout } = useContext(SessionContext);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { sessionId, linkSessionToUser } = useContext(SessionContext);

    const isActive = (path) => location.pathname === path;

    const navItems = [
        { path: '/', icon: FaHome, label: 'Home' },
        { path: '/recommendations', icon: FaCompass, label: 'Discover' },
        { path: '/favorites', icon: FaHeart, label: 'Favorites' },
    ];

    const handleLogout = () => {
        logout();
        navigate('/');
        setIsProfileDropdownOpen(false);
    };

    const handleNavigate = (path) => {
        navigate(path);
        setIsMobileMenuOpen(false);
        setIsProfileDropdownOpen(false);
    };

    // Open auth modal
    const openAuthModal = (mode = 'login') => {
        setIsLoginMode(mode === 'login');
        setShowAuthModal(true);
        setError(null);
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setFirstName('');
        setLastName('');
        setIsMobileMenuOpen(false);
        setIsProfileDropdownOpen(false);
    };

    // Close auth modal
    const closeAuthModal = () => {
        setShowAuthModal(false);
        setError(null);
        setLoading(false);
    };

    // Handle Login
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, sessionId })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }

            if (data.token) {
                linkSessionToUser(data);
                closeAuthModal();
                // Stay on current page
                // Don't navigate anywhere
            }
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    // Handle Signup
    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    firstName: firstName.trim(),
                    lastName: lastName.trim(),
                    name: [firstName.trim(), lastName.trim()].filter(Boolean).join(' ') || email.split('@')[0],
                    sessionId
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Signup failed');
            }

            if (data.token) {
                linkSessionToUser(data);
                closeAuthModal();
                // Stay on current page
                // Don't navigate anywhere
            }
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Navigation Bar */}
            <motion.nav 
                className="navbar"
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.6, type: "spring", stiffness: 100 }}
            >
                <div className="navbar-container">
                    {/* Brand Logo */}
                    <motion.div 
                        className="navbar-brand"
                        onClick={() => handleNavigate('/')}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <div className="brand-icon">
                            <FaUtensils />
                            <div className="brand-glow"></div>
                        </div>
                        <span className="brand-text">Foodgram</span>
                        <span className="brand-badge">🍽️</span>
                    </motion.div>

                    {/* Desktop Navigation */}
                    <div className="navbar-links">
                        {navItems.map((item) => (
                            <motion.button
                                key={item.path}
                                className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                                onClick={() => handleNavigate(item.path)}
                                whileHover={{ y: -2 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <item.icon className="nav-icon" />
                                <span>{item.label}</span>
                                {isActive(item.path) && (
                                    <motion.div 
                                        className="nav-indicator"
                                        layoutId="navIndicator"
                                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                    />
                                )}
                            </motion.button>
                        ))}
                    </div>

                    {/* Right Side - Auth / Profile */}
                    <div className="navbar-right">
                        {isGuest ? (
                            <div className="auth-buttons">
                                <motion.button
                                    className="auth-btn login-btn"
                                    onClick={() => openAuthModal('login')}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    <FaSignInAlt />
                                    <span>Login</span>
                                </motion.button>
                                <motion.button
                                    className="auth-btn signup-btn"
                                    onClick={() => openAuthModal('signup')}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    <FaUserPlus />
                                    <span>Sign Up</span>
                                </motion.button>
                            </div>
                        ) : (
                            <div className="profile-section">
                                {/* Profile Avatar */}
                                <motion.div 
                                    className="profile-avatar"
                                    onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {user?.avatar ? (
                                        <img src={user.avatar} alt="Profile" />
                                    ) : (
                                        <div className="avatar-placeholder">
                                            {user?.email?.[0]?.toUpperCase() || 'U'}
                                        </div>
                                    )}
                                    <div className="online-dot"></div>
                                </motion.div>

                                {/* Profile Dropdown */}
                                <AnimatePresence>
                                    {isProfileDropdownOpen && (
                                        <motion.div 
                                            className="profile-dropdown"
                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <div className="dropdown-header">
                                                <div className="dropdown-avatar">
                                                    {user?.avatar ? (
                                                        <img src={user.avatar} alt="Profile" />
                                                    ) : (
                                                        <div className="avatar-placeholder small">
                                                            {user?.email?.[0]?.toUpperCase() || 'U'}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="dropdown-user-info">
                                                    <p className="dropdown-name">{user?.name || 'User'}</p>
                                                    <p className="dropdown-email">{user?.email}</p>
                                                </div>
                                            </div>
                                            
                                            <div className="dropdown-divider"></div>
                                            
                                            <button 
                                                className="dropdown-item"
                                                onClick={() => handleNavigate('/profile')}
                                            >
                                                <FaUser /> Profile
                                            </button>
                                            <button 
                                                className="dropdown-item"
                                                onClick={() => handleNavigate('/favorites')}
                                            >
                                                <FaHeart /> Favorites
                                            </button>
                                            <button 
                                                className="dropdown-item"
                                                onClick={() => handleNavigate('/orders')}
                                            >
                                                <FaCrown /> Orders
                                            </button>
                                            
                                            <div className="dropdown-divider"></div>
                                            
                                            <button 
                                                className="dropdown-item logout"
                                                onClick={handleLogout}
                                            >
                                                <FaSignOutAlt /> Logout
                                            </button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        )}

                        {/* Mobile Menu Toggle */}
                        <motion.button
                            className="mobile-menu-toggle"
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            {isMobileMenuOpen ? <FaTimes /> : <FaBars />}
                        </motion.button>
                    </div>
                </div>
            </motion.nav>

            {/* Mobile Menu */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <>
                        <motion.div 
                            className="mobile-overlay"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsMobileMenuOpen(false)}
                        />
                        <motion.div 
                            className="mobile-menu"
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        >
                            <div className="mobile-menu-header">
                                <div className="navbar-brand" onClick={() => handleNavigate('/')}>
                                    <div className="brand-icon">
                                        <FaUtensils />
                                    </div>
                                    <span className="brand-text">Foodgram</span>
                                </div>
                                <button 
                                    className="mobile-close"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    <FaTimes />
                                </button>
                            </div>

                            <div className="mobile-menu-links">
                                {navItems.map((item) => (
                                    <motion.button
                                        key={item.path}
                                        className={`mobile-nav-link ${isActive(item.path) ? 'active' : ''}`}
                                        onClick={() => handleNavigate(item.path)}
                                        whileHover={{ x: 10 }}
                                        whileTap={{ scale: 0.95 }}
                                    >
                                        <item.icon />
                                        <span>{item.label}</span>
                                    </motion.button>
                                ))}
                            </div>

                            <div className="mobile-menu-divider"></div>

                            {isGuest ? (
                                <div className="mobile-auth-buttons">
                                    <button 
                                        className="mobile-auth-btn login"
                                        onClick={() => openAuthModal('login')}
                                    >
                                        <FaSignInAlt /> Login
                                    </button>
                                    <button 
                                        className="mobile-auth-btn signup"
                                        onClick={() => openAuthModal('signup')}
                                    >
                                        <FaUserPlus /> Sign Up
                                    </button>
                                </div>
                            ) : (
                                <div className="mobile-profile">
                                    <div className="mobile-profile-info">
                                        <div className="avatar-placeholder small">
                                            {user?.email?.[0]?.toUpperCase() || 'U'}
                                        </div>
                                        <div>
                                            <p className="mobile-profile-name">{user?.name || 'User'}</p>
                                            <p className="mobile-profile-email">{user?.email}</p>
                                        </div>
                                    </div>
                                    <button 
                                        className="mobile-logout-btn"
                                        onClick={handleLogout}
                                    >
                                        <FaSignOutAlt /> Logout
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Auth Modal */}
            <AnimatePresence>
                {showAuthModal && (
                    <>
                        <motion.div 
                            className="auth-modal-overlay"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={closeAuthModal}
                        />
                        <motion.div 
                            className="auth-modal"
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            transition={{ type: "spring", damping: 25 }}
                        >
                            <div className="auth-modal-header">
                                <div className="auth-modal-brand">
                                    <FaUtensils />
                                    <span>Foodgram</span>
                                </div>
                                <button className="auth-modal-close" onClick={closeAuthModal}>
                                    <FaTimesCircle />
                                </button>
                            </div>

                            <div className="auth-modal-body">
                                <h2>{isLoginMode ? 'Welcome Back!' : 'Create Account'}</h2>
                                <p>{isLoginMode ? 'Login to continue your food journey' : 'Start your food discovery journey'}</p>

                                <form onSubmit={isLoginMode ? handleLogin : handleSignup}>
                                    {!isLoginMode && (
                                        <div className="form-row">
                                            <div className="form-group">
                                                <label>First Name</label>
                                                <input
                                                    type="text"
                                                    value={firstName}
                                                    onChange={(e) => setFirstName(e.target.value)}
                                                    required
                                                    placeholder="First name"
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Last Name</label>
                                                <input
                                                    type="text"
                                                    value={lastName}
                                                    onChange={(e) => setLastName(e.target.value)}
                                                    placeholder="Last name"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    <div className="form-group">
                                        <label>Email</label>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            placeholder="your@email.com"
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label>Password</label>
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            minLength="6"
                                            placeholder={isLoginMode ? 'Enter password' : 'Create password (min 6 chars)'}
                                        />
                                    </div>

                                    {!isLoginMode && (
                                        <div className="form-group">
                                            <label>Confirm Password</label>
                                            <input
                                                type="password"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                required
                                                placeholder="Confirm password"
                                            />
                                        </div>
                                    )}

                                    <AnimatePresence>
                                        {error && (
                                            <motion.p 
                                                className="auth-error"
                                                initial={{ opacity: 0, y: -10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -10 }}
                                            >
                                                {error}
                                            </motion.p>
                                        )}
                                    </AnimatePresence>

                                    <motion.button 
                                        type="submit" 
                                        className="auth-modal-submit"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        disabled={loading}
                                    >
                                        {loading ? '⏳ Processing...' : isLoginMode ? 'Login' : 'Create Account'}
                                    </motion.button>
                                </form>

                                <div className="auth-modal-footer">
                                    <p>
                                        {isLoginMode ? (
                                            <span>
                                                Don't have an account?{' '}
                                                <button 
                                                    className="auth-switch-btn"
                                                    onClick={() => { setIsLoginMode(false); setError(null); }}
                                                >
                                                    Sign Up
                                                </button>
                                            </span>
                                        ) : (
                                            <span>
                                                Already have an account?{' '}
                                                <button 
                                                    className="auth-switch-btn"
                                                    onClick={() => { setIsLoginMode(true); setError(null); }}
                                                >
                                                    Login
                                                </button>
                                            </span>
                                        )}
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
};

export default Navbar;