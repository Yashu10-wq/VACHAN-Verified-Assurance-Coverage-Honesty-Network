import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { DEMO_USERS } from '../data/mockData';
import { apiClient } from '../services/api';

interface SignupData {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role?: UserRole;
}

interface AuthContextType {
  user: User | null;
  role: UserRole;
  token: string | null;
  login: (email: string, password?: string, role?: UserRole) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  loginAsDemo: (roleKey: 'customer' | 'agent' | 'authority') => void;
  logout: () => void;
  setRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('vachan_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('vachan_access_token') || null;
  });

  const role = user?.role || 'CUSTOMER';

  useEffect(() => {
    if (user) {
      localStorage.setItem('vachan_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('vachan_user');
    }
  }, [user]);

  const login = async (email: string, password: string = 'password123', _targetRole?: UserRole) => {
    try {
      const res = await apiClient.post('/auth/login', { email, password });
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token);
        localStorage.setItem('vachan_access_token', res.data.access_token);
        setUser(res.data.user);
        return;
      }
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.response?.data?.error ||
        err?.message ||
        'Authentication failed. Please verify credentials.';
      throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg));
    }
  };

  const signup = async (data: SignupData) => {
    const res = await apiClient.post('/auth/signup', {
      email: data.email,
      password: data.password,
      full_name: data.full_name,
      phone: data.phone || '+91 98402 11920',
      role: data.role || 'CUSTOMER',
    });
    // Auto login immediately after signup
    await login(data.email, data.password, data.role || 'CUSTOMER');
  };

  const loginAsDemo = (roleKey: 'customer' | 'agent' | 'authority') => {
    const demo = DEMO_USERS[roleKey];
    if (demo) {
      setUser(demo);
      setToken(`demo_token_${roleKey}`);
      localStorage.setItem('vachan_access_token', `demo_token_${roleKey}`);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('vachan_user');
    localStorage.removeItem('vachan_access_token');
  };

  const setRole = (newRole: UserRole) => {
    if (user) {
      const updated = { ...user, role: newRole };
      setUser(updated);
    } else {
      const matchKey = newRole === 'CUSTOMER' ? 'customer' : newRole === 'INSURANCE_AGENT' ? 'agent' : 'authority';
      loginAsDemo(matchKey as any);
    }
  };

  return (
    <AuthContext.Provider value={{ user, role, token, login, signup, loginAsDemo, logout, setRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
