import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SessionContext } from '../context/SessionContext';

const Home = () => {
    const navigate = useNavigate();
    const { sessionId, isGuest } = useContext(SessionContext);
    const [currentRound, setCurrentRound] = useState(0);
    const [responses, setResponses] = useState([]);
    const [gameStarted, setGameStarted] = useState(false);
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const totalRounds = 7;

    const startGame = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/game/questions');
            if (!response.ok) throw new Error('Failed to load questions');
            const data = await response.json();
            setQuestions(data.questions || []);
            setGameStarted(true);
        } catch (error) {
            console.error('Failed to load questions:', error);
            setError('Failed to load game. Please try again.');
        }
        setLoading(false);
    };

    const handleChoice = async (optionId, questionId, foodId) => {
        const newResponse = { 
            questionId, 
            optionId,
            foodId: foodId || null,
            timestamp: new Date().toISOString()
        };
        const updatedResponses = [...responses, newResponse];
        setResponses(updatedResponses);

        if (currentRound + 1 < totalRounds) {
            setCurrentRound(currentRound + 1);
        } else {
            await submitGameResponses(updatedResponses);
        }
    };

    const submitGameResponses = async (allResponses) => {
        setLoading(true);
        try {
            const response = await fetch('/api/game/responses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sessionId,
                    responses: allResponses
                })
            });

            if (!response.ok) throw new Error('Failed to submit responses');

            const data = await response.json();
            
            localStorage.setItem('tasteDNA', JSON.stringify(data.taste_dna));
            localStorage.setItem('recommendations', JSON.stringify(data.recommendations));
            localStorage.setItem('gameResponses', JSON.stringify(allResponses));

            navigate('/recommendations', { 
                state: { 
                    tasteDNA: data.taste_dna,
                    recommendations: data.recommendations 
                }
            });
        } catch (error) {
            console.error('Failed to submit game:', error);
            setError('Failed to save your responses. Please try again.');
        }
        setLoading(false);
    };

    // Particles Background
    const Particles = () => (
        <div className="particles">
            {[...Array(8)].map((_, i) => (
                <div key={i} className="particle" />
            ))}
        </div>
    );

    if (!gameStarted) {
        return (
            <>
                <Particles />
                <motion.div 
                    className="landing-page"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8 }}
                >
                    <motion.div 
                        className="landing-content"
                        initial={{ y: 40, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                    >
                        <motion.span 
                            className="emoji-hero"
                            animate={{ 
                                y: [0, -10, 0],
                                rotate: [0, 5, -5, 0]
                            }}
                            transition={{ 
                                duration: 3,
                                repeat: Infinity,
                                ease: "easeInOut"
                            }}
                        >
                            🍽️
                        </motion.span>
                        
                        <h1>Find Your Flavor Match!</h1>
                        
                        <motion.p 
                            className="subtitle"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.4 }}
                        >
                            Answer 7 quick questions and get personalized food recommendations
                        </motion.p>
                        
                        <motion.div 
                            className="features"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6 }}
                        >
                            <div className="feature">
                                <span>⚡</span>
                                <p>Quick & fun 2-minute game</p>
                            </div>
                            <div className="feature">
                                <span>🎯</span>
                                <p>Personalized recommendations</p>
                            </div>
                            <div className="feature">
                                <span>🔓</span>
                                <p>No login required to start</p>
                            </div>
                        </motion.div>

                        <motion.button 
                            className="start-btn"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={startGame}
                            disabled={loading}
                        >
                            {loading ? '⏳ Loading...' : '🚀 Start Rapid Fire Game'}
                        </motion.button>

                        {isGuest && (
                            <motion.p 
                                className="guest-note"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.8 }}
                            >
                                💡 Play now as guest! <strong>Login later</strong> to save your taste profile and order.
                            </motion.p>
                        )}

                        {error && <p className="error">{error}</p>}
                    </motion.div>
                </motion.div>
            </>
        );
    }

    const question = questions[currentRound];
    if (!question) {
        return <div className="loading-container">Loading questions...</div>;
    }

    const progressPercentage = ((currentRound) / totalRounds) * 100;

    return (
        <>
            <Particles />
            <motion.div 
                className="game-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                <div className="game-header">
                    <motion.h2
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        Round {currentRound + 1} of {totalRounds}
                    </motion.h2>
                    <div className="progress-bar">
                        <motion.div 
                            className="progress-fill"
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercentage}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>
                    <span className="progress-text">
                        {Math.round(progressPercentage)}%
                    </span>
                </div>

                <AnimatePresence mode="wait">
                    <motion.div 
                        key={currentRound}
                        className="question-card"
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.4 }}
                    >
                        <motion.h3
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            {question.text}
                        </motion.h3>
                        
                        <div className="options-grid">
                            {question.options.map((option, index) => (
                                <motion.button
                                    key={option.id}
                                    className="option-btn"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.08 }}
                                    whileHover={{ scale: 1.03 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleChoice(option.id, question.id, option.food_id)}
                                    disabled={loading}
                                >
                                    <span className="option-label">
                                        {option.text}
                                    </span>
                                </motion.button>
                            ))}
                        </div>
                    </motion.div>
                </AnimatePresence>

                {loading && (
                    <motion.div 
                        className="loading-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <div className="spinner">⏳</div>
                        <p>Saving your preferences...</p>
                    </motion.div>
                )}
            </motion.div>
        </>
    );
};

export default Home;