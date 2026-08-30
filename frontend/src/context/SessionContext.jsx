import React, { createContext, useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

export const SessionContext = createContext();

export const SessionProvider = ({ children }) => {
    const [sessionId, setSessionId] = useState(null);
    const [isGuest, setIsGuest] = useState(true);
    const [user, setUser] = useState(null);
    const [tasteDNA, setTasteDNA] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Check localStorage for existing session
        let storedSession = localStorage.getItem('sessionId');
        
        if (!storedSession) {
            storedSession = `guest_${uuidv4().slice(0, 8)}`;
            localStorage.setItem('sessionId', storedSession);
        }
        
        setSessionId(storedSession);
        checkSessionStatus(storedSession);
    }, []);

    const checkSessionStatus = async (sid) => {
        try {
            const response = await fetch(`/api/auth/session-status?sessionId=${sid}`);
            if (response.ok) {
                const data = await response.json();
                setIsGuest(data.is_guest !== false);
                if (data.user_id) {
                    // Fetch user data
                    const userData = await fetchUserData(data.user_id);
                    setUser(userData);
                }
            }
        } catch (error) {
            console.error('Session check failed:', error);
        }
    };

    const fetchUserData = async (userId) => {
        try {
            const response = await fetch(`/api/users/${userId}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
        }
        return null;
    };

    const linkSessionToUser = (userData) => {
        setUser(userData);
        setIsGuest(false);
        localStorage.setItem('user', JSON.stringify(userData));
        if (userData.token) {
            localStorage.setItem('token', userData.token);
        }
    };

    const logout = () => {
        setUser(null);
        setIsGuest(true);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
    };

    return (
        <SessionContext.Provider value={{
            sessionId,
            isGuest,
            user,
            tasteDNA,
            setTasteDNA,
            loading,
            setLoading,
            linkSessionToUser,
            logout,
            checkSessionStatus
        }}>
            {children}
        </SessionContext.Provider>
    );
};