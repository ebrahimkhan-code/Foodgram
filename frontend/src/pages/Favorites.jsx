import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaHeart, FaShoppingCart, FaCompass } from 'react-icons/fa';
import { SessionContext } from '../context/SessionContext';

const DishImage = ({ food }) => {
    const [broken, setBroken] = React.useState(false);
    const show = food.image_url && !broken;
    return (
        <div className="fav-image">
            {show ? (
                <img src={food.image_url} alt={food.name} loading="lazy" onError={() => setBroken(true)} />
            ) : (
                <div className="placeholder-image">🍽️</div>
            )}
        </div>
    );
};

const Favorites = () => {
    const navigate = useNavigate();
    const { favorites, loadFavorites, toggleFavorite, isGuest } = useContext(SessionContext);

    useEffect(() => { loadFavorites(); }, [loadFavorites]);

    const handleOrder = (food) => navigate('/checkout', { state: { selectedItem: food } });

    return (
        <motion.div
            className="list-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
        >
            <div className="list-header">
                <h1><FaHeart className="header-icon heart" /> Your Favorites</h1>
                <p>{favorites.length > 0
                    ? `${favorites.length} dish${favorites.length > 1 ? 'es' : ''} you love`
                    : 'Tap the heart on any dish to save it here'}
                </p>
                {isGuest && favorites.length > 0 && (
                    <p className="hint-note">💡 Log in to keep your favorites across devices.</p>
                )}
            </div>

            {favorites.length === 0 ? (
                <motion.div className="empty-state" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <span className="empty-emoji">💔</span>
                    <h2>No favorites yet</h2>
                    <p>Discover dishes picked for your taste and save the ones you love.</p>
                    <button className="primary-btn" onClick={() => navigate('/recommendations')}>
                        <FaCompass /> Explore recommendations
                    </button>
                </motion.div>
            ) : (
                <div className="dish-grid">
                    {favorites.map((food) => (
                        <motion.div
                            key={food.food_id || food.name}
                            className="dish-card"
                            whileHover={{ y: -6 }}
                            transition={{ duration: 0.25 }}
                        >
                            <DishImage food={food} />
                            <div className="dish-info">
                                <h3>{food.name || 'Dish'}</h3>
                                {food.restaurant && <p className="muted">🏬 {food.restaurant}</p>}
                                <div className="dish-meta">
                                    {food.price > 0 && <span className="price">Rs. {Math.round(food.price)}</span>}
                                    {food.rating > 0 && <span className="muted">⭐ {Number(food.rating).toFixed(1)}</span>}
                                </div>
                                <div className="dish-actions">
                                    <button className="icon-btn active" title="Remove from favorites" onClick={() => toggleFavorite(food)}>
                                        <FaHeart />
                                    </button>
                                    <button className="order-btn" onClick={() => handleOrder(food)}>
                                        <FaShoppingCart /> Order
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </motion.div>
    );
};

export default Favorites;
