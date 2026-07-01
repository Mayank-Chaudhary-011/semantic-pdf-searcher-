// App.jsx
// Root auth wrapper. Routes between: loading, OAuth callback, auth page, main app.

import { useState, useEffect } from "react";
import { supabase } from "./lib/supabaseClient";
import AuthPage from "./components/AuthPage";
import AuthCallback from "./components/AuthCallback";
import MainApp from "./MainApp";

function LoadingScreen() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F5F0E8",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 20,
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          border: "2.5px solid #E2D9CE",
          borderTopColor: "#C4830A",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <p
        style={{
          margin: 0,
          fontSize: 13,
          color: "#9B938A",
          letterSpacing: "0.02em",
        }}
      >
        Loading…
      </p>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

// Evaluated once at module load — pathname never changes during a session.
const isAuthCallback = window.location.pathname === "/auth/callback";

export default function App() {
  const [user, setUser] = useState(null); // null = checking, false = no session, object = logged in
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? false);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? false);
      if (session?.user && isAuthCallback) {
        window.location.href = "/";
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) return <LoadingScreen />;
  if (isAuthCallback) return <AuthCallback />;
  if (!user) return <AuthPage />;

  return (
    <MainApp
      user={user}
      onSignOut={async () => {
        await supabase.auth.signOut();
      }}
    />
  );
}
