import React, { useState, useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

const Checkout = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { sessionId, isGuest, user, linkSessionToUser } = useContext(SessionContext);
    const [selectedItem, setSelectedItem] = useState(null);
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

    const completeOrder = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    sessionId,
                    foodItems: [selectedItem]
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Order failed');
            }

            navigate('/order-confirmation', { state: { order: data } });
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    if (!selectedItem) {
        return <div className="loading-container">Loading...</div>;
    }

    return (
        <motion.div 
            className="checkout-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
        >
            <motion.h2
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                🍽️ Complete Your Order
            </motion.h2>
            
            <motion.div 
                className="order-summary"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h3>Order Summary</h3>
                <div className="order-item">
                    <span className="item-name">
                        {selectedItem.name || selectedItem.food_name}
                    </span>
                    <span className="item-price">$14.99</span>
                </div>
                <div className="order-total">
                    <strong>Total:</strong> $14.99
                </div>
            </motion.div>

            {isGuest ? (
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
                        <button 
                            className="checkout-btn"
                            onClick={() => navigate('/')}
                        >
                            Go to Home
                        </button>
                        <p className="checkout-hint">
                            Click Login or Sign Up in the top bar!
                        </p>
                    </div>
                </div>
            ) : (
                <button 
                    className="checkout-btn"
                    onClick={completeOrder}
                    disabled={loading}
                >
                    {loading ? '⏳ Processing...' : 'Place Order ✅'}
                </button>
            )}
            
            {error && <p className="error">{error}</p>}
        </motion.div>
    );
};

export default Checkout;