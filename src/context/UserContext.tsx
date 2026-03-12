"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  title: string | null;
  avatar_url: string | null;
  email_summaries: boolean;
  action_item_alerts: boolean;
  product_updates: boolean;
}

interface UserContextType {
  user: UserProfile | null;
  isLoading: boolean;
  updateUser: (data: Partial<UserProfile>) => void;
  refreshUser: (email: string) => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async (email: string) => {
    try {
      const response = await fetch(`http://localhost:8000/auth/profile?email=${email}`);
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // For now, we use a fixed email as we don't have a real auth session yet
    refreshUser("admin@synapnote.com");
  }, [refreshUser]);

  const updateUser = (data: Partial<UserProfile>) => {
    setUser(prev => prev ? { ...prev, ...data } : null);
  };

  return (
    <UserContext.Provider value={{ user, isLoading, updateUser, refreshUser }}>
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
