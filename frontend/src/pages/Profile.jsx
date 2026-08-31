import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaUserCircle, FaHeart, FaReceipt, FaRedo, FaSignOutAlt, FaSignInAlt, FaSave } from 'react-icons/fa';
import { SessionContext } from '../context/SessionContext';

const Profile = () => {
    const navigate = useNavigate();
    const { user, setUser, isGuest, favorites, logout } = useContext(SessionContext);
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [ordersCount, setOrdersCount] = useState(0);

    useEffect(() => {
        if (user) {
            setFirstName(user.first_name || '');
            setLastName(user.last_name || '');
        }
    }, [user]);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) return;
        (async () => {
            try {
                const res = await fetch('/api/orders', { headers: { Authorization: `Bearer ${token}` } });
                if (res.ok) {
                    const data = await res.json();
                    if (data.success) setOrdersCount((data.orders || []).length);
                }
            } catch (_) { /* ignore */ }
        })();
    }, []);

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('/api/users/me', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({ firstName: firstName.trim(), lastName: lastName.trim() })
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.message || 'Update failed');
            setUser(data.user);
            localStorage.setItem('user', JSON.stringify(data.user));
            setMessage({ type: 'success', text: 'Profile updated!' });
        } catch (err) {
            setMessage({ type: 'error', text: err.message });
        } finally {
            setSaving(false);
        }
    };

    if (isGuest && !localStorage.getItem('token')) {
        return (
            <motion.div className="list-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="list-header"><h1><FaUserCircle className="header-icon" /> Profile</h1></div>
                <motion.div className="empty-state" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <span className="empty-emoji">🙋</span>
                    <h2>You're browsing as a guest</h2>
                    <p>Log in or sign up from the top bar to manage your profile, favorites and orders.</p>
                    <button className="primary-btn" onClick={() => navigate('/recommendations')}>
                        <FaSignInAlt /> Continue exploring
                    </button>
                </motion.div>
            </motion.div>
        );
    }

    const initial = (user?.first_name?.[0] || user?.name?.[0] || user?.email?.[0] || 'U').toUpperCase();

    return (
        <motion.div className="list-page profile-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="profile-hero">
                <div className="profile-avatar-lg">{initial}</div>
                <div>
                    <h1>{user?.name || 'Your profile'}</h1>
                    <p className="muted">{user?.email}</p>
                </div>
            </div>

            <div className="profile-stats">
                <button className="stat-card" onClick={() => navigate('/favorites')}>
                    <FaHeart className="stat-icon heart" />
                    <span className="stat-value">{favorites.length}</span>
                    <span className="stat-label">Favorites</span>
                </button>
                <button className="stat-card" onClick={() => navigate('/orders')}>
                    <FaReceipt className="stat-icon" />
                    <span className="stat-value">{ordersCount}</span>
                    <span className="stat-label">Orders</span>
                </button>
            </div>

            <form className="profile-form" onSubmit={handleSave}>
                <h3>Profile settings</h3>
                <div className="form-row">
                    <div className="form-group">
                        <label>First Name</label>
                        <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="First name" />
                    </div>
                    <div className="form-group">
                        <label>Last Name</label>
                        <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Last name" />
                    </div>
                </div>
                <div className="form-group">
                    <label>Email</label>
                    <input type="email" value={user?.email || ''} disabled />
                </div>

                {message && (
                    <p className={message.type === 'success' ? 'form-success' : 'auth-error'}>{message.text}</p>
                )}

                <button type="submit" className="primary-btn" disabled={saving}>
                    <FaSave /> {saving ? 'Saving...' : 'Save changes'}
                </button>
            </form>

            <div className="profile-actions">
                <button className="secondary-btn" onClick={() => navigate('/game')}>
                    <FaRedo /> Retake taste quiz
                </button>
                <button className="secondary-btn danger" onClick={() => { logout(); navigate('/'); }}>
                    <FaSignOutAlt /> Log out
                </button>
            </div>
        </motion.div>
    );
};

export default Profile;
