import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaReceipt, FaCompass, FaSignInAlt } from 'react-icons/fa';
import { SessionContext } from '../context/SessionContext';

const statusColor = (s) => ({
    confirmed: '#2e7d32',
    pending: '#ef6c00',
    preparing: '#1565c0',
    delivered: '#2e7d32',
    cancelled: '#c62828'
}[s] || '#555');

const Orders = () => {
    const navigate = useNavigate();
    const { isGuest } = useContext(SessionContext);
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { setLoading(false); return; }
        (async () => {
            try {
                const res = await fetch('/api/orders', { headers: { Authorization: `Bearer ${token}` } });
                if (res.ok) {
                    const data = await res.json();
                    if (data.success) setOrders(data.orders || []);
                }
            } catch (e) {
                console.error('Load orders failed:', e);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    if (loading) {
        return <div className="loading-container"><div className="spinner">⏳</div><p>Loading your orders...</p></div>;
    }

    // Guests have no server-side order history.
    if (isGuest && !localStorage.getItem('token')) {
        return (
            <motion.div className="list-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="list-header"><h1><FaReceipt className="header-icon" /> Your Orders</h1></div>
                <motion.div className="empty-state" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <span className="empty-emoji">🔐</span>
                    <h2>Log in to see your orders</h2>
                    <p>Sign in from the top bar to place orders and track your history.</p>
                    <button className="primary-btn" onClick={() => navigate('/recommendations')}>
                        <FaSignInAlt /> Browse dishes
                    </button>
                </motion.div>
            </motion.div>
        );
    }

    return (
        <motion.div className="list-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="list-header">
                <h1><FaReceipt className="header-icon" /> Your Orders</h1>
                <p>{orders.length > 0 ? `${orders.length} order${orders.length > 1 ? 's' : ''}` : 'Your order history lives here'}</p>
            </div>

            {orders.length === 0 ? (
                <motion.div className="empty-state" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <span className="empty-emoji">🧾</span>
                    <h2>No previous orders</h2>
                    <p>You haven't placed any orders yet. Find something delicious to get started!</p>
                    <button className="primary-btn" onClick={() => navigate('/recommendations')}>
                        <FaCompass /> Discover food
                    </button>
                </motion.div>
            ) : (
                <div className="orders-list">
                    {orders.map((order) => {
                        const items = Array.isArray(order.items) ? order.items : [];
                        return (
                            <motion.div key={order.id} className="order-card" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
                                <div className="order-card-header">
                                    <div>
                                        <span className="order-number">{order.order_number}</span>
                                        <span className="order-date">
                                            {new Date(order.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                                        </span>
                                    </div>
                                    <span className="order-status" style={{ background: statusColor(order.status) }}>
                                        {order.status}
                                    </span>
                                </div>
                                <div className="order-items">
                                    {items.map((it, i) => (
                                        <div className="order-item-row" key={i}>
                                            {it.image_url ? (
                                                <img src={it.image_url} alt={it.name} className="order-thumb" loading="lazy" />
                                            ) : (
                                                <div className="order-thumb placeholder-image">🍽️</div>
                                            )}
                                            <span className="order-item-name">{it.name}{it.quantity > 1 ? ` ×${it.quantity}` : ''}</span>
                                            <span className="order-item-price">Rs. {Math.round(it.total_price || it.unit_price || 0)}</span>
                                        </div>
                                    ))}
                                </div>
                                <div className="order-card-footer">
                                    <span>Total</span>
                                    <strong>Rs. {Math.round(order.total_amount || 0)}</strong>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            )}
        </motion.div>
    );
};

export default Orders;
