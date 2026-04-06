"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { APP_CONFIG } from '@/config/constants';

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  title: string;
  avatar_url: string;
  email_summaries: boolean;
  action_item_alerts: boolean;
  product_updates: boolean;
}

interface UserContextType {
  user: UserProfile | null;
  loading: boolean;
  updateUser: (data: Partial<UserProfile>) => void;
  refreshUser: () => Promise<void>;
  logout: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Using a mock email for development since we don't have login yet
const DEFAULT_EMAIL = "admin@synapnote.com";
const API_BASE_URL = "/api";

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile?email=${DEFAULT_EMAIL}`);
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        console.error("Failed to fetch user profile");
      }
    } catch (error) {
      console.error("Error fetching user profile:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const updateUser = (data: Partial<UserProfile>) => {
    if (user) {
      setUser({ ...user, ...data });
    }
  };

  const refreshUser = async () => {
    setLoading(true);
    await fetchUser();
  };

  const logout = () => {
    setUser(null);
    setLoading(false);
  };

  return (
    <UserContext.Provider value={{ user, loading, updateUser, refreshUser, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
