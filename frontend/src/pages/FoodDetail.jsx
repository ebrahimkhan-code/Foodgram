import React, { useState, useEffect, useContext, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

// Recommended dishes come from the enriched CSV catalog, whose food_id values
// (e.g. "x8l5__beef-gyro") are NOT rows in the Postgres `foods` table. So we
// resolve the dish from the data the user already has — router state first,
// then the cached recommendations / favorites in localStorage — and only fall
// back to /api/foods/:id (which works just for seeded dishes) as a last resort.
const findCachedFood = (foodId) => {
    const pools = [];
    try {
        const recs = JSON.parse(localStorage.getItem('recommendations') || 'null');
        if (recs) {
            if (Array.isArray(recs.exploitation)) pools.push(...recs.exploitation);
            if (Array.isArray(recs.exploration)) pools.push(...recs.exploration);
        }
    } catch (_) { /* ignore bad json */ }
    try {
        const favs = JSON.parse(localStorage.getItem('guestFavorites') || '[]');
        if (Array.isArray(favs)) pools.push(...favs);
    } catch (_) { /* ignore bad json */ }
    return pools.find((f) => String(f.food_id || f.id) === String(foodId)) || null;
};

const SUGGESTIONS = ['Is this spicy?', 'Is it vegetarian?', "What's in it?", 'How big is the portion?'];

const FoodDetail = () => {
    const { foodId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { isFavorite, toggleFavorite } = useContext(SessionContext);

    const [food, setFood] = useState(location.state?.food || null);
    const [imgError, setImgError] = useState(false);

    // "Ask about this dish" state (Member 2 RAG/LLM via /api/food/:id/explain).
    const [query, setQuery] = useState('');
    const [asking, setAsking] = useState(false);
    const [answer, setAnswer] = useState(null); // { available, answer }

    // Resolve the dish if we didn't arrive with it in router state.
    useEffect(() => {
        if (food) return;
        const cached = findCachedFood(foodId);
        if (cached) { setFood(cached); return; }
        let active = true;
        (async () => {
            try {
                const res = await fetch(`/api/foods/${encodeURIComponent(foodId)}`);
                if (res.ok) {
                    const data = await res.json();
                    if (active && data.success && data.food) setFood(data.food);
                }
            } catch (_) { /* seeded-only endpoint; ignore misses */ }
        })();
        return () => { active = false; };
    }, [foodId, food]);

    const askAbout = useCallback(async (raw) => {
        const q = (raw != null ? raw : query).trim();
        if (!q || asking) return;
        setAsking(true);
        setAnswer(null);
        try {
            const res = await fetch(`/api/food/${encodeURIComponent(foodId)}/explain?query=${encodeURIComponent(q)}`);
            const data = await res.json();
            setAnswer(data);
        } catch (_) {
            setAnswer({ available: false, answer: '' });
        } finally {
            setAsking(false);
        }
    }, [foodId, query, asking]);

    const submit = (e) => { e.preventDefault(); askAbout(); };

    const name = food?.name || food?.food_name || 'This dish';
    const showImage = food?.image_url && !imgError;
    const fav = food ? isFavorite(food) : false;

    return (
        <motion.div
            className="food-detail-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
        >
            <button className="detail-back-btn" onClick={() => navigate(-1)}>
                ← Back
            </button>

            <div className="detail-hero">
                <div className="detail-image">
                    {showImage ? (
                        <motion.img
                            src={food.image_url}
                            alt={name}
                            loading="lazy"
                            onError={() => setImgError(true)}
                            initial={{ scale: 1.05, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ duration: 0.5 }}
                        />
                    ) : (
                        <div className="placeholder-image">🍽️</div>
                    )}
                </div>

                <div className="detail-info">
                    <h1>{name}</h1>
                    {food?.restaurant && <p className="detail-restaurant">🏬 {food.restaurant}</p>}
                    <p className="detail-cuisine">{food?.cuisine || 'Various'}</p>

                    <div className="detail-meta">
                        {food?.price > 0 && <span className="detail-price">Rs. {Math.round(food.price)}</span>}
                        {food?.rating > 0 && <span className="detail-rating">⭐ {Number(food.rating).toFixed(1)}</span>}
                        {food?.score > 0 && (
                            <span className="detail-confidence">
                                {food.confidence === 'high' ? '🔥' : '💡'} {Math.round(food.score * 100)}% match
                            </span>
                        )}
                    </div>

                    {food?.reason && <p className="detail-reason">💡 {food.reason}</p>}

                    <div className="detail-actions">
                        <motion.button
                            className={`detail-fav ${fav ? 'active' : ''}`}
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.96 }}
                            disabled={!food}
                            onClick={() => food && toggleFavorite(food)}
                        >
                            {fav ? '❤️ Saved' : '🤍 Save'}
                        </motion.button>
                        <motion.button
                            className="detail-order"
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.96 }}
                            disabled={!food}
                            onClick={() => food && navigate('/checkout', { state: { selectedItem: food } })}
                        >
                            🛒 Order now
                        </motion.button>
                    </div>
                </div>
            </div>
            {/* Ask about this dish — grounded answers from Member 2 (RAG/LLM). */}
            <motion.div
                className="detail-ask"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
            >
                <h2>🤖 Ask about this dish</h2>
                <p className="detail-ask-sub">Grounded answers from Foodgram's food assistant.</p>

                <form className="ask-form" onSubmit={submit}>
                    <span className="ask-icon">💬</span>
                    <input
                        type="text"
                        className="ask-input"
                        placeholder={`Ask something about ${name}…`}
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

                {!answer && !asking && (
                    <div className="ask-suggestions">
                        {SUGGESTIONS.map((s) => (
                            <button
                                key={s}
                                type="button"
                                className="ask-chip"
                                onClick={() => { setQuery(s); askAbout(s); }}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                )}

                <AnimatePresence>
                    {(asking || answer) && (
                        <motion.div
                            className="ask-answer"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                        >
                            {asking ? (
                                <p className="ask-text">Thinking…</p>
                            ) : answer.available === false || !answer.answer ? (
                                <p className="ask-unavailable">
                                    🤖 The food assistant is offline right now — try again in a moment.
                                </p>
                            ) : (
                                <p className="ask-text">{answer.answer}</p>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </motion.div>
    );
};

export default FoodDetail;

