import React, { useState, useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

const money = (n) => `Rs. ${Math.round(Number(n) || 0)}`;

const Checkout = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { sessionId, isGuest } = useContext(SessionContext);
    const [selectedItem, setSelectedItem] = useState(null);
    const [quantity, setQuantity] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const item = location.state?.selectedItem;
        if (item) {
            setSelectedItem(item);
        } else {
            navigate('/recommendations');
        }
    }, [location]);

    if (!selectedItem) {
        return <div className="loading-container"><div className="spinner">⏳</div><p>Loading...</p></div>;
    }

    const unitPrice = Number(selectedItem.price) || 0;
    const subtotal = unitPrice * quantity;
    const deliveryFee = subtotal > 2000 || subtotal === 0 ? 0 : 149;
    const tax = Math.round(subtotal * 0.05);
    const total = subtotal + deliveryFee + tax;

    const loggedIn = !isGuest && !!localStorage.getItem('token');

    const completeOrder = async () => {
        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    sessionId,
                    items: [{
                        food_id: selectedItem.food_id || selectedItem.id,
                        name: selectedItem.name || selectedItem.food_name,
                        price: unitPrice,
                        quantity,
                        image_url: selectedItem.image_url || '',
                        restaurant: selectedItem.restaurant || '',
                        cuisine: selectedItem.cuisine || '',
                        currency: selectedItem.currency || 'PKR'
                    }]
                })
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Order failed');
            }
            navigate('/orders');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            className="checkout-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
        >
            <motion.h2 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
                🍽️ Complete Your Order
            </motion.h2>

            <motion.div
                className="order-summary"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <div className="checkout-item">
                    {selectedItem.image_url ? (
                        <img src={selectedItem.image_url} alt={selectedItem.name} className="checkout-thumb" />
                    ) : (
                        <div className="checkout-thumb placeholder-image">🍽️</div>
                    )}
                    <div className="checkout-item-info">
                        <h3>{selectedItem.name || selectedItem.food_name}</h3>
                        {selectedItem.restaurant && <p className="muted">🏬 {selectedItem.restaurant}</p>}
                        <span className="price">{money(unitPrice)}</span>
                    </div>
                </div>

                <div className="qty-row">
                    <span>Quantity</span>
                    <div className="qty-controls">
                        <button type="button" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
                        <span className="qty-value">{quantity}</span>
                        <button type="button" onClick={() => setQuantity((q) => q + 1)}>+</button>
                    </div>
                </div>

                <div className="summary-line"><span>Subtotal</span><span>{money(subtotal)}</span></div>
                <div className="summary-line"><span>Delivery</span><span>{deliveryFee === 0 ? 'Free' : money(deliveryFee)}</span></div>
                <div className="summary-line"><span>Tax (5%)</span><span>{money(tax)}</span></div>
                <div className="order-total"><strong>Total</strong><strong>{money(total)}</strong></div>
            </motion.div>

            {!loggedIn ? (
                <div className="guest-checkout">
                    <div className="login-prompt">
                        <p>🔐 You need to login or sign up to complete your order</p>
                        <div className="benefits">
                            <p>✓ Save your taste profile</p>
                            <p>✓ Track order history</p>
                            <p>✓ Get better recommendations</p>
                        </div>
                    </div>
                    <div className="checkout-actions">
                        <button className="checkout-btn" onClick={() => navigate('/recommendations')}>
                            Keep browsing
                        </button>
                        <p className="checkout-hint">Click Login or Sign Up in the top bar to order!</p>
                    </div>
                </div>
            ) : (
                <button className="checkout-btn" onClick={completeOrder} disabled={loading}>
                    {loading ? '⏳ Processing...' : `Place Order · ${money(total)} ✅`}
                </button>
            )}

            {error && <p className="error">{error}</p>}
        </motion.div>
    );
};

export default Checkout;
