import React, { createContext, useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

export const SessionContext = createContext();

const foodKey = (f) => String(f?.food_id || f?.id || f?.name || '');

export const SessionProvider = ({ children }) => {
    const [sessionId, setSessionId] = useState(null);
    const [isGuest, setIsGuest] = useState(true);
    const [user, setUser] = useState(null);
    const [tasteDNA, setTasteDNA] = useState(null);
    const [loading, setLoading] = useState(false);
    const [favorites, setFavorites] = useState([]); // array of dish snapshots
    // Has the user completed the taste game at least once? Controls whether the
    // home route shows the game or jumps straight to Discover.
    const [hasPlayedGame, setHasPlayedGame] = useState(
        () => localStorage.getItem('hasPlayedGame') === 'true'
    );

    // ---- boot: restore session + any stored auth ----
    useEffect(() => {
        let storedSession = localStorage.getItem('sessionId');
        if (!storedSession) {
            storedSession = `guest_${uuidv4().slice(0, 8)}`;
            localStorage.setItem('sessionId', storedSession);
        }
        setSessionId(storedSession);

        // Optimistically restore a logged-in user from localStorage so the UI
        // doesn't flash "guest" on reload; the server check below confirms it.
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem('token');
        if (storedUser && storedToken) {
            try {
                setUser(JSON.parse(storedUser));
                setIsGuest(false);
            } catch (_) { /* ignore bad json */ }
        }

        const storedDNA = localStorage.getItem('tasteDNA');
        if (storedDNA) {
            try { setTasteDNA(JSON.parse(storedDNA)); } catch (_) { /* ignore */ }
        }

        checkSessionStatus(storedSession);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const fetchUserData = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) return null;
        try {
            const response = await fetch('/api/users/me', {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                if (data.success) return data.user;
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
        }
        return null;
    }, []);

    const checkSessionStatus = useCallback(async (sid) => {
        try {
            const response = await fetch(`/api/auth/session-status?sessionId=${sid}`);
            if (response.ok) {
                const data = await response.json();
                if (data.user_id) {
                    const userData = await fetchUserData();
                    if (userData) {
                        setUser(userData);
                        setIsGuest(false);
                        localStorage.setItem('user', JSON.stringify(userData));
                        if (userData.taste_dna && Object.keys(userData.taste_dna).length > 0) {
                            markGamePlayed();
                        }
                    }
                }
                // Don't force guest=true here: a locally restored token is still
                // valid even if this un-linked guest session has no user_id.
            }
        } catch (error) {
            console.error('Session check failed:', error);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fetchUserData]);

    // ---- taste game state ----
    const markGamePlayed = useCallback(() => {
        localStorage.setItem('hasPlayedGame', 'true');
        setHasPlayedGame(true);
    }, []);

    // ---- favorites: server-backed when logged in, localStorage for guests ----
    const loadFavorites = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const res = await fetch('/api/favorites', {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.success) {
                        setFavorites(data.favorites || []);
                        return;
                    }
                }
            } catch (e) {
                console.error('Load favorites failed:', e);
            }
        }
        // Guest fallback
        try {
            const local = JSON.parse(localStorage.getItem('guestFavorites') || '[]');
            setFavorites(Array.isArray(local) ? local : []);
        } catch (_) {
            setFavorites([]);
        }
    }, []);

    useEffect(() => { loadFavorites(); }, [loadFavorites, user]);

    const isFavorite = useCallback(
        (food) => favorites.some((f) => foodKey(f) === foodKey(food)),
        [favorites]
    );

    const persistGuestFavorites = (list) => {
        localStorage.setItem('guestFavorites', JSON.stringify(list));
    };

    const toggleFavorite = useCallback(async (food) => {
        const token = localStorage.getItem('token');
        const key = foodKey(food);
        const already = favorites.some((f) => foodKey(f) === key);

        // Optimistic UI update.
        const next = already
            ? favorites.filter((f) => foodKey(f) !== key)
            : [{ ...food, food_id: key }, ...favorites];
        setFavorites(next);

        if (token) {
            try {
                if (already) {
                    await fetch(`/api/favorites/${encodeURIComponent(key)}`, {
                        method: 'DELETE',
                        headers: { Authorization: `Bearer ${token}` }
                    });
                } else {
                    await fetch('/api/favorites', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`
                        },
                        body: JSON.stringify({ food: { ...food, food_id: key } })
                    });
                }
            } catch (e) {
                console.error('Toggle favorite failed:', e);
            }
        } else {
            persistGuestFavorites(next);
        }
        return !already; // now favorited?
    }, [favorites]);

    const linkSessionToUser = (userData) => {
        // userData is the raw /login|/signup response: { token, user: {...} }
        const u = userData.user || userData;
        setUser(u);
        setIsGuest(false);
        localStorage.setItem('user', JSON.stringify(u));
        if (userData.token) localStorage.setItem('token', userData.token);
        if (u.taste_dna && Object.keys(u.taste_dna).length > 0) markGamePlayed();
        // Reload favorites now that we're authenticated.
        setTimeout(() => loadFavorites(), 0);
    };

    const logout = () => {
        setUser(null);
        setIsGuest(true);
        setFavorites([]);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
    };

    return (
        <SessionContext.Provider value={{
            sessionId,
            isGuest,
            user,
            setUser,
            tasteDNA,
            setTasteDNA,
            loading,
            setLoading,
            favorites,
            loadFavorites,
            isFavorite,
            toggleFavorite,
            hasPlayedGame,
            markGamePlayed,
            linkSessionToUser,
            logout,
            checkSessionStatus
        }}>
            {children}
        </SessionContext.Provider>
    );
};
