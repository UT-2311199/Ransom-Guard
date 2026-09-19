import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authApi } from '../services/api';
import toast from 'react-hot-toast';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar?: string;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  loginWithGoogle: (customPayload?: { credential?: string; email?: string; name?: string; picture?: string }) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const TOKEN_KEY = 'rg_token';
const USER_KEY = 'rg_user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
  });

  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [isLoading, setIsLoading] = useState(true);

  // Validate stored token on load
  useEffect(() => {
    const verifySession = async () => {
      const activeToken = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
      if (!activeToken) {
        setIsLoading(false);
        return;
      }

      try {
        const res = await authApi.getMe();
        if (res.data) {
          const userData = res.data;
          setUser(userData);
          if (localStorage.getItem(TOKEN_KEY)) {
            localStorage.setItem(USER_KEY, JSON.stringify(userData));
          } else {
            sessionStorage.setItem(USER_KEY, JSON.stringify(userData));
          }
        }
      } catch (err) {
        console.warn('[Auth] Token verification failed or server offline, keeping local session if valid:', err);
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, []);

  const saveAuth = (tokenVal: string, userVal: User, rememberMe: boolean = true) => {
    setToken(tokenVal);
    setUser(userVal);
    if (rememberMe) {
      localStorage.setItem(TOKEN_KEY, tokenVal);
      localStorage.setItem(USER_KEY, JSON.stringify(userVal));
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);
    } else {
      sessionStorage.setItem(TOKEN_KEY, tokenVal);
      sessionStorage.setItem(USER_KEY, JSON.stringify(userVal));
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  };

  const login = async (email: string, password: string, rememberMe: boolean = false): Promise<boolean> => {
    try {
      const res = await authApi.login({ email, password, remember_me: rememberMe });
      const { access_token, user: userData } = res.data;
      saveAuth(access_token, userData, rememberMe);
      toast.success(`Welcome back, ${userData.name}!`, {
        icon: '🛡️',
        style: {
          background: '#0F172A',
          color: '#F8FAFC',
          border: '1px solid #3B82F6',
        },
      });
      return true;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Authentication failed. Check your credentials.';
      toast.error(msg, {
        icon: '⚠️',
      });
      return false;
    }
  };

  const register = async (email: string, password: string, name: string, role: string = 'Security Analyst'): Promise<boolean> => {
    try {
      const res = await authApi.register({ email, password, name, role });
      const { access_token, user: userData } = res.data;
      saveAuth(access_token, userData, true);
      toast.success(`Security account initialized for ${name}!`, {
        icon: '🔐',
        style: {
          background: '#0F172A',
          color: '#F8FAFC',
          border: '1px solid #10B981',
        },
      });
      return true;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Registration failed. Try again.';
      toast.error(msg);
      return false;
    }
  };

  const loginWithGoogle = async (customPayload?: { credential?: string; email?: string; name?: string; picture?: string }): Promise<boolean> => {
    try {
      const payload = customPayload || {
        email: 'analyst@ransomguard.io',
        name: 'Sarah Connor',
      };
      const res = await authApi.googleLogin(payload);
      const { access_token, user: userData } = res.data;
      saveAuth(access_token, userData, true);
      toast.success(`Signed in as ${userData.name}!`, {
        icon: '🌐',
        style: {
          background: '#0F172A',
          color: '#F8FAFC',
          border: '1px solid #3B82F6',
        },
      });
      return true;
    } catch (err: any) {
      // Offline / fallback session creation if user provided their email
      if (customPayload?.email) {
        const mockUser: User = {
          id: `google_${customPayload.email}`,
          email: customPayload.email,
          name: customPayload.name || customPayload.email.split('@')[0],
          role: 'Security Analyst',
          avatar: customPayload.picture || `https://api.dicebear.com/7.x/bottts/svg?seed=${customPayload.email}`,
        };
        saveAuth(`offline_token_${Date.now()}`, mockUser, true);
        toast.success(`Signed in as ${mockUser.name} (Direct Session)`, { icon: '🌐' });
        return true;
      }
      toast.error('Google authentication failed. Please ensure the backend is running.');
      return false;
    }
  };

  const logout = useCallback(() => {
    try {
      authApi.logout().catch(() => {});
    } catch {}
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    toast('Logged out from security session', {
      icon: '🔒',
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        loginWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
