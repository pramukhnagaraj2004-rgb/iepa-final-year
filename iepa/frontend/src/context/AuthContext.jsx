import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const isHydratedRef = useRef(false);

  const logout = useCallback(() => {
    localStorage.removeItem('iepa_token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  }, []);

  const fetchMe = useCallback(async (authToken) => {
    if (!authToken) return;
    try {
      const res = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.data.success) {
        setUser(res.data.data);
      }
    } catch (e) {
      console.error('Failed to fetch user profile:', e);
      if (e.response && (e.response.status === 401 || e.response.status === 403)) {
        logout();
      }
    }
  }, [logout]);

  const login = useCallback((jwtToken) => {
    try {
      localStorage.setItem('iepa_token', jwtToken);
      const decoded = jwtDecode(jwtToken);
      setToken(jwtToken);
      setUser(decoded);
      axios.defaults.headers.common['Authorization'] = `Bearer ${jwtToken}`;
      fetchMe(jwtToken);
    } catch (e) {
      console.error('Invalid token on login:', e);
    }
  }, [fetchMe]);

  useEffect(() => {
    if (isHydratedRef.current) return;
    isHydratedRef.current = true;

    const savedToken = localStorage.getItem('iepa_token');
    if (savedToken) {
      try {
        const decoded = jwtDecode(savedToken);
        const currentTime = Date.now() / 1000;
        if (decoded.exp && decoded.exp < currentTime) {
          logout();
          setLoading(false);
        } else {
          setToken(savedToken);
          setUser(decoded);
          axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
          fetchMe(savedToken).finally(() => setLoading(false));
          return;
        }
      } catch (e) {
        logout();
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [fetchMe, logout]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, fetchMe, API_BASE }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
