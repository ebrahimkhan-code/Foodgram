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

    // Accepts either a full food object (from a card — carried via router state
    // so the detail page renders instantly) or just a food_id string (from the
    // Ask Foodgram source chips, which only know the id).
    const handleFoodClick = (foodOrId) => {
        if (foodOrId && typeof foodOrId === 'object') {
            navigate(`/food/${foodOrId.food_id}`, { state: { food: foodOrId } });
        } else {
            navigate(`/food/${foodOrId}`);
        }
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
            <div className="recs-topbar">
                <div className="recs-topbar-text">
                    <h1>🍴 Your Recommendations</h1>
                    <p>Handpicked for your taste profile</p>
                </div>
                <motion.button
                    className="retake-btn"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/game')}
                >
                    🔄 Retake quiz
                </motion.button>
            </div>

            <AskBar onFoodClick={handleFoodClick} onOrder={handleOrder} onFeedback={handleFeedback} />
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
                                    onClick={() => handleFoodClick(food)}
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
                                    onClick={() => handleFoodClick(food)}
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

// Natural-language food search / Q&A powered by Member 2 (RAG/LLM) via the
// backend /api/ask proxy. Fully self-contained and degrades quietly: if the
// service is offline the answer area just shows a soft "unavailable" note.
const AskBar = ({ onFoodClick, onOrder, onFeedback }) => {
    const [query, setQuery] = useState('');
    const [asking, setAsking] = useState(false);
    const [result, setResult] = useState(null);

    const parseName = (src) => {
        if (!src) return null;
        if (src.name) return src.name;
        const doc = src.document || '';
        if (doc.includes(' is ')) return doc.split(' is ')[0].trim();
        if (doc.includes(' — ')) return doc.split(' — ')[0].trim();
        return src.food_id || null;
    };

    // Catalog-fallback sources are full dish objects (image/price/score) → render
    // them as proper recommendation cards. Member 2's RAG sources are sparse
    // (food_id + document only) → render those as lightweight name chips.
    const hasCards = (sources) =>
        Array.isArray(sources) && sources.length > 0 &&
        sources.some((s) => s && (s.image_url || s.price || s.score !== undefined));

    const submit = async (e) => {
        e.preventDefault();
        const q = query.trim();
        if (!q || asking) return;
        setAsking(true);
        setResult(null);
        try {
            const resp = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: q, top_k: 9 })
            });
            const data = await resp.json();
            setResult(data);
        } catch (err) {
            setResult({ available: false, answer: '' });
        } finally {
            setAsking(false);
        }
    };

    const suggestions = ['Something spicy and non-veg', 'A good vegetarian option', 'High-protein lunch', 'Sweet dessert'];

    return (
        <motion.div
            className="ask-bar"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
        >
            <form className="ask-form" onSubmit={submit}>
                <span className="ask-icon">🔎</span>
                <input
                    type="text"
                    className="ask-input"
                    placeholder="Ask Foodgram… e.g. “a spicy vegetarian dish under Rs. 800”"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
                <motion.button
                    type="submit"
                    className="ask-submit"
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    disabled={asking || !query.trim()}
                >
                    {asking ? '…' : 'Ask'}
                </motion.button>
            </form>

            {!result && !asking && (
                <div className="ask-suggestions">
                    {suggestions.map((s) => (
                        <button key={s} type="button" className="ask-chip" onClick={() => setQuery(s)}>
                            {s}
                        </button>
                    ))}
                </div>
            )}

            <AnimatePresence>
                {result && (
                    <motion.div
                        className="ask-answer"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                    >
                        {result.available === false ? (
                            <p className="ask-unavailable">
                                🤖 The food assistant is offline right now — browse your picks below instead.
                            </p>
                        ) : (
                            <>
                                <p className="ask-text">{result.answer}</p>
                                {hasCards(result.sources) ? (
                                    <div className="food-grid ask-results-grid">
                                        {result.sources.map((food, i) => (
                                            <motion.div
                                                key={food.food_id || i}
                                                initial={{ opacity: 0, y: 16 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ duration: 0.35, delay: i * 0.05 }}
                                                whileHover={{ scale: 1.03, transition: { duration: 0.2 } }}
                                            >
                                                <FoodCard
                                                    food={food}
                                                    type={food.confidence === 'high' ? 'exploitation' : 'exploration'}
                                                    onClick={() => onFoodClick && onFoodClick(food)}
                                                    onOrder={() => onOrder && onOrder(food)}
                                                    onFeedback={(type, rating) => onFeedback && onFeedback(food.food_id, type, rating)}
                                                />
                                            </motion.div>
                                        ))}
                                    </div>
                                ) : (
                                    Array.isArray(result.sources) && result.sources.length > 0 && (
                                        <div className="ask-sources">
                                            <span className="ask-sources-label">Based on:</span>
                                            {result.sources.map((s, i) => {
                                                const name = parseName(s);
                                                if (!name) return null;
                                                return (
                                                    <button
                                                        key={s.food_id || i}
                                                        type="button"
                                                        className="ask-source-chip"
                                                        onClick={() => s.food_id && onFoodClick && onFoodClick(s.food_id)}
                                                    >
                                                        {name}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    )
                                )}
                            </>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

const FoodCard = ({ food, type, onClick, onOrder, onFeedback }) => {
    const [imgError, setImgError] = useState(false);
    const { isFavorite, toggleFavorite } = useContext(SessionContext);
    const fav = isFavorite(food);
    const showImage = food.image_url && !imgError;
    return (
        <motion.div
            className={`food-card ${type}`}
            whileHover={{ y: -8 }}
            transition={{ duration: 0.3 }}
            onClick={onClick}
        >
            <div className="food-image">
                {showImage ? (
                    <motion.img
                        src={food.image_url}
                        alt={food.name}
                        loading="lazy"
                        onError={() => setImgError(true)}
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
                {food.restaurant && (
                    <p className="restaurant" style={{ margin: '2px 0', fontSize: '0.85rem', color: '#666' }}>
                        🏬 {food.restaurant}
                    </p>
                )}
                <p className="cuisine">{food.cuisine || 'Various'}</p>
                <div
                    className="food-meta"
                    style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', margin: '6px 0' }}
                >
                    {food.price > 0 && (
                        <span className="price" style={{ fontWeight: 700, color: '#e65100' }}>
                            Rs. {Math.round(food.price)}
                        </span>
                    )}
                    {food.rating > 0 && (
                        <span className="rating" style={{ fontSize: '0.85rem', color: '#666' }}>
                            ⭐ {Number(food.rating).toFixed(1)}
                        </span>
                    )}
                </div>
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
                        className={`action-btn save ${fav ? 'active' : ''}`}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        title={fav ? 'Remove from favorites' : 'Add to favorites'}
                        onClick={() => toggleFavorite(food)}
                    >
                        {fav ? '❤️' : '🤍'}
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