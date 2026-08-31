import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

// Attributes a chosen dish contributes to the Taste DNA.
const TASTE_ATTRS = ['cuisine', 'protein', 'flavor', 'spice_level', 'meal_type', 'base'];

// Expand the dishes the user picked into {attribute, value, preference} answers
// (one per known attribute). Repeated picks of the same value reinforce it.
const buildResponses = (chosenDishes) => {
    const out = [];
    chosenDishes.forEach((dish, di) => {
        TASTE_ATTRS.forEach((attr) => {
            const value = dish && dish[attr];
            if (value) {
                out.push({
                    questionId: `round_${di + 1}`,
                    optionId: dish.food_id,
                    attribute: attr,
                    value: String(value).toLowerCase(),
                    preference: 1,
                    foodId: dish.food_id,
                    timestamp: new Date().toISOString()
                });
            }
        });
    });
    return out;
};

// One tappable dish photo in a "this or that" round.
const PhotoCard = ({ dish, side, onPick, disabled }) => {
    const [broken, setBroken] = useState(false);
    const showImg = dish.image_url && !broken;
    // Dedupe and drop meaningless "unknown" values so the chips are clean and,
    // crucially, so their React keys never collide (a dish with e.g. protein
    // and flavor both "unknown" previously produced two key="unknown" spans).
    const tags = [...new Set(
        [dish.cuisine, dish.protein, dish.flavor]
            .filter(Boolean)
            .map((t) => String(t))
            .filter((t) => t.toLowerCase() !== 'unknown')
    )].slice(0, 3);
    return (
        <motion.button
            type="button"
            className={`photo-card ${side}`}
            onClick={() => onPick(dish)}
            disabled={disabled}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
        >
            <div className="photo-card-img">
                {showImg ? (
                    <img src={dish.image_url} alt={dish.name} loading="lazy" onError={() => setBroken(true)} />
                ) : (
                    <div className="placeholder-image big">🍽️</div>
                )}
                <div className="photo-card-shade" />
                <span className="photo-pick-hint">Tap to pick 👆</span>
            </div>
            <div className="photo-card-body">
                <h3>{dish.name}</h3>
                {dish.restaurant && <p className="muted">🏬 {dish.restaurant}</p>}
                <div className="photo-tags">
                    {tags.map((t, i) => <span className="photo-tag" key={`${t}-${i}`}>{t}</span>)}
                </div>
            </div>
        </motion.button>
    );
};

const Home = () => {
    const navigate = useNavigate();
    const { sessionId, isGuest, setTasteDNA, markGamePlayed } = useContext(SessionContext);
    const [rounds, setRounds] = useState([]);
    const [currentRound, setCurrentRound] = useState(0);
    const [chosen, setChosen] = useState([]);
    const [gameStarted, setGameStarted] = useState(false);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const totalRounds = rounds.length || 8;

    const startGame = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/game/photo-rounds?rounds=8');
            if (!response.ok) throw new Error('Failed to load the game');
            const data = await response.json();
            const rs = data.rounds || [];
            if (rs.length === 0) throw new Error('No dishes available right now');
            setRounds(rs);
            setChosen([]);
            setCurrentRound(0);
            setGameStarted(true);
        } catch (err) {
            console.error('Failed to load photo rounds:', err);
            setError('Failed to load the game. Please try again.');
        }
        setLoading(false);
    };

    const choose = async (dish) => {
        if (submitting) return;
        const updated = [...chosen, dish];
        setChosen(updated);
        if (currentRound + 1 < totalRounds) {
            setCurrentRound(currentRound + 1);
        } else {
            await submitGame(updated);
        }
    };

    const submitGame = async (chosenDishes) => {
        setSubmitting(true);
        try {
            const responses = buildResponses(chosenDishes);
            const response = await fetch('/api/game/responses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sessionId, responses })
            });
            if (!response.ok) throw new Error('Failed to build your taste profile');
            const data = await response.json();

            localStorage.setItem('tasteDNA', JSON.stringify(data.taste_dna));
            localStorage.setItem('recommendations', JSON.stringify(data.recommendations));
            localStorage.setItem('gameResponses', JSON.stringify(responses));
            setTasteDNA(data.taste_dna);
            markGamePlayed();

            navigate('/recommendations', {
                state: { tasteDNA: data.taste_dna, recommendations: data.recommendations }
            });
        } catch (err) {
            console.error('Failed to submit game:', err);
            setError('Failed to save your picks. Please try again.');
            setSubmitting(false);
        }
    };

    /* __LANDING__ */
    if (!gameStarted) {
        return (
            <div className="tot-wrap">
                <motion.div
                    className="tot-landing"
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    <motion.span
                        className="emoji-hero"
                        animate={{ y: [0, -10, 0], rotate: [0, 6, -6, 0] }}
                        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                    >
                        😋
                    </motion.span>
                    <h1>This or That?</h1>
                    <p className="subtitle">
                        Two dishes, one tap. Pick the one that looks tastier — we'll learn your
                        flavor profile and serve up dishes you'll love.
                    </p>
                    <div className="features">
                        <div className="feature"><span>📸</span><p>Real dishes, real photos</p></div>
                        <div className="feature"><span>⚡</span><p>8 quick rounds</p></div>
                        <div className="feature"><span>🎯</span><p>Personalized picks</p></div>
                    </div>
                    <motion.button
                        className="start-btn"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={startGame}
                        disabled={loading}
                    >
                        {loading ? '⏳ Loading...' : '🍔 Start Tasting'}
                    </motion.button>
                    {isGuest && (
                        <p className="guest-note">
                            💡 Play as guest — <strong>log in later</strong> to save favorites & order.
                        </p>
                    )}
                    {error && <p className="error">{error}</p>}
                </motion.div>
            </div>
        );
    }

    /* __GAME__ */
    const pair = rounds[currentRound];
    if (!pair) {
        return <div className="loading-container"><div className="spinner">⏳</div><p>Loading dishes...</p></div>;
    }
    const progress = (currentRound / totalRounds) * 100;

    return (
        <div className="tot-wrap">
            <div className="tot-header">
                <h2>Which looks tastier?</h2>
                <div className="progress-bar">
                    <motion.div
                        className="progress-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.4 }}
                    />
                </div>
                <span className="progress-text">Round {currentRound + 1} of {totalRounds}</span>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={currentRound}
                    className="tot-arena"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                    transition={{ duration: 0.3 }}
                >
                    <PhotoCard dish={pair.left} side="left" onPick={choose} disabled={submitting} />
                    <div className="tot-vs">VS</div>
                    <PhotoCard dish={pair.right} side="right" onPick={choose} disabled={submitting} />
                </motion.div>
            </AnimatePresence>

            {submitting && (
                <motion.div className="loading-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <div className="spinner">🍳</div>
                    <p>Cooking up your recommendations...</p>
                </motion.div>
            )}
        </div>
    );
};

export default Home;

