import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

const Recommendations = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { sessionId, isGuest, tasteDNA, setTasteDNA } = useContext(SessionContext);
    const [recommendations, setRecommendations] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (location.state?.recommendations) {
            setRecommendations(location.state.recommendations);
            if (location.state?.tasteDNA) {
                setTasteDNA(location.state.tasteDNA);
            }
            setLoading(false);
            return;
        }

        const storedRecs = localStorage.getItem('recommendations');
        const storedDNA = localStorage.getItem('tasteDNA');
        
        if (storedRecs && storedDNA) {
            setRecommendations(JSON.parse(storedRecs));
            setTasteDNA(JSON.parse(storedDNA));
            setLoading(false);
            return;
        }

        fetchRecommendations();
    }, []);

    const fetchRecommendations = async () => {
        try {
            const response = await fetch(`/api/recommendations?sessionId=${sessionId}`);
            if (!response.ok) throw new Error('Failed to fetch recommendations');
            const data = await response.json();
            setRecommendations(data);
            localStorage.setItem('recommendations', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to fetch recommendations:', error);
            setError('Failed to load recommendations. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleFoodClick = (foodId) => {
        navigate(`/food/${foodId}`);
    };

    const handleOrder = (food) => {
        navigate('/checkout', { state: { selectedItem: food } });
    };

    const handleFeedback = async (foodId, type, rating = null) => {
        try {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sessionId,
                    foodId,
                    interactionType: type,
                    rating,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Feedback failed:', error);
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.5 }
        }
    };

    if (loading) {
        return (
            <motion.div 
                className="loading-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
            >
                <div className="spinner">⏳</div>
                <p>Loading your personalized recommendations...</p>
            </motion.div>
        );
    }

    if (error) {
        return (
            <motion.div 
                className="error-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
            >
                <p>❌ {error}</p>
                <motion.button 
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={fetchRecommendations}
                    className="start-btn"
                    style={{ marginTop: 16 }}
                >
                    Try Again
                </motion.button>
            </motion.div>
        );
    }

    if (!recommendations) {
        return (
            <motion.div 
                className="empty-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
            >
                <p>No recommendations found. Play the game first!</p>
                <motion.button 
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/')}
                    className="start-btn"
                    style={{ marginTop: 16 }}
                >
                    Play Game
                </motion.button>
            </motion.div>
        );
    }

    return (
        <motion.div 
            className="recommendations-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
        >
            {/* <motion.div 
                className={`guest-banner ${!isGuest ? 'logged-in' : ''}`}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                {isGuest ? (
                    <p>
                        🔓 You're browsing as a guest. 
                        <button onClick={() => navigate('/login')} className="link-btn">
                            Login
                        </button> 
                        or 
                        <button onClick={() => navigate('/signup')} className="link-btn">
                            Sign up
                        </button> 
                        to save and order!
                    </p>
                ) : (
                    <p>✅ Welcome back! Your personalized recommendations are ready.</p>
                )}
            </motion.div> */}

            {recommendations.exploitation?.length > 0 && (
                <motion.section 
                    className="recommendation-section"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <div className="section-header">
                        <motion.h2
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            🎯 For You
                        </motion.h2>
                        <p>High-confidence matches based on your taste profile</p>
                    </div>
                    <div className="food-grid">
                        {recommendations.exploitation.map((food, index) => (
                            <motion.div
                                key={food.food_id}
                                variants={itemVariants}
                                whileHover={{ 
                                    scale: 1.03,
                                    transition: { duration: 0.2 }
                                }}
                            >
                                <FoodCard
                                    food={food}
                                    type="exploitation"
                                    onClick={() => handleFoodClick(food.food_id)}
                                    onOrder={() => handleOrder(food)}
                                    onFeedback={(type, rating) => handleFeedback(food.food_id, type, rating)}
                                />
                            </motion.div>
                        ))}
                    </div>
                </motion.section>
            )}

            {recommendations.exploration?.length > 0 && (
                <motion.section 
                    className="recommendation-section"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <div className="section-header">
                        <motion.h2
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            🌟 Discover Something New
                        </motion.h2>
                        <p>Explore dishes you might love</p>
                    </div>
                    <div className="food-grid">
                        {recommendations.exploration.map((food, index) => (
                            <motion.div
                                key={food.food_id}
                                variants={itemVariants}
                                whileHover={{ 
                                    scale: 1.03,
                                    transition: { duration: 0.2 }
                                }}
                            >
                                <FoodCard
                                    food={food}
                                    type="exploration"
                                    onClick={() => handleFoodClick(food.food_id)}
                                    onOrder={() => handleOrder(food)}
                                    onFeedback={(type, rating) => handleFeedback(food.food_id, type, rating)}
                                />
                            </motion.div>
                        ))}
                    </div>
                </motion.section>
            )}
        </motion.div>
    );
};

const FoodCard = ({ food, type, onClick, onOrder, onFeedback }) => {
    return (
        <motion.div 
            className={`food-card ${type}`}
            whileHover={{ y: -8 }}
            transition={{ duration: 0.3 }}
            onClick={onClick}
        >
            <div className="food-image">
                {food.image_url ? (
                    <motion.img 
                        src={food.image_url} 
                        alt={food.name}
                        whileHover={{ scale: 1.05 }}
                        transition={{ duration: 0.4 }}
                    />
                ) : (
                    <div className="placeholder-image">🍽️</div>
                )}
                <div className="confidence-badge">
                    {food.confidence === 'high' ? '🔥' : '💡'} {Math.round(food.score * 100)}%
                </div>
            </div>
            
            <div className="food-info">
                <h3>{food.name || food.food_name || 'Dish'}</h3>
                <p className="cuisine">{food.cuisine || 'Various'}</p>
                <motion.p 
                    className="reason"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    💡 {food.reason || 'Recommended for you'}
                </motion.p>
                <div className="food-actions" onClick={(e) => e.stopPropagation()}>
                    <motion.button 
                        className="action-btn like"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => onFeedback('like')}
                    >
                        👍
                    </motion.button>
                    <motion.button 
                        className="action-btn dislike"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => onFeedback('dislike')}
                    >
                        👎
                    </motion.button>
                    <motion.button 
                        className="action-btn save"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => onFeedback('save')}
                    >
                        ⭐
                    </motion.button>
                    <motion.button 
                        className="action-btn order"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => onOrder()}
                    >
                        🛒 Order
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
};

export default Recommendations;