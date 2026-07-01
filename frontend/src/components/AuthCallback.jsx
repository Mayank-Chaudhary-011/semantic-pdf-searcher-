// AuthCallback.jsx
// This page handles the redirect back from Google after OAuth.
// Supabase automatically extracts the session from the URL hash/params.
// We just need to wait for it, then redirect to the main app.

import { useEffect } from "react";
import { supabase } from "../lib/supabaseClient";

export default function AuthCallback() {
  useEffect(() => {
    // supabase.auth.getSession() will pick up the tokens from the URL
    // and establish the session automatically.
    // The onAuthStateChange listener in App.jsx will then fire and redirect.
    supabase.auth.getSession();
  }, []);

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
        Signing you in…
      </p>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
