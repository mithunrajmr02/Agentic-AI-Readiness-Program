import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { TOKEN_STORAGE_KEY, applyToken, identityFromToken } from './lib/api';
import AppLayout from './layout/AppLayout';
import LoginScreen from './screens/LoginScreen';
import routes from './routes';

/**
 * 07-UX-ARCHITECTURE.md §9 & 14-PARALLEL-WORKSTREAMS.md §WS-6
 * Decomposed App Shell.
 * Holds authentication state, renders AppLayout shell, and routes to screen components.
 */
export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [currentUser, setCurrentUser] = useState(() => {
    const existing = localStorage.getItem(TOKEN_STORAGE_KEY);
    return existing ? identityFromToken(existing) : null;
  });

  const signIn = (accessToken, email) => {
    applyToken(accessToken);
    setToken(accessToken);
    setCurrentUser(identityFromToken(accessToken) || { email, role: 'manager' });
  };

  const signOut = () => {
    applyToken(null);
    setToken(null);
    setCurrentUser(null);
  };

  if (!token) {
    return <LoginScreen onAuthenticated={signIn} />;
  }

  return (
    <Routes>
      <Route element={<AppLayout currentUser={currentUser} onSignOut={signOut} />}>
        {routes.map((r, idx) => (
          <Route key={r.path || idx} path={r.path} element={r.element} />
        ))}
      </Route>
    </Routes>
  );
}
