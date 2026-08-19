import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { setAuthToken } from '../api/client';

type Session = {
  token: string;
  userId: number;
  username: string;
};

type AuthContextValue = {
  session: Session | null;
  setSession: (session: Session | null) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<Session | null>(null);

  const setSession = useCallback((next: Session | null) => {
    setSessionState(next);
    setAuthToken(next?.token ?? null);
  }, []);

  const value = useMemo(() => ({ session, setSession }), [session, setSession]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
