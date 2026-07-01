// AuthPage.jsx — restyled to match the Study PDF Search theme (cream / ink / amber)
// Handles both Login and Signup flows in one component with Supabase auth and Google OAuth.

import { useState } from "react";
import { supabase } from "../lib/supabaseClient";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  CheckCircle,
  BookOpen,
} from "lucide-react";

const T = {
  cream: "#F5F0E8",
  ink: "#1A1714",
  inkMid: "#4A443E",
  inkFaint: "#9B938A",
  amber: "#C4830A",
  amberBg: "#FEF3DC",
  border: "#E2D9CE",
  borderMid: "#CFC5BA",
  white: "#FFFFFF",
  sidebarBg: "#EDE8DF",
  cardHover: "#E8E1D6",
  danger: "#C0392B",
  dangerBg: "rgba(192,57,43,0.07)",
  dangerBorder: "rgba(192,57,43,0.2)",
  success: "#3E7C4A",
  successBg: "rgba(62,124,74,0.07)",
  successBorder: "rgba(62,124,74,0.2)",
};

const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  *, *::before, *::after { box-sizing: border-box; }
  .auth-btn-primary { background: ${T.ink}; color: ${T.white}; border: none; border-radius: 7px; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s, opacity 0.15s; letter-spacing: 0.01em; }
  .auth-btn-primary:hover:not(:disabled) { background: #2E2925; }
  .auth-btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
  .auth-btn-ghost { background: none; color: ${T.inkMid}; border: 1px solid ${T.border}; border-radius: 99px; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s; }
  .auth-btn-ghost:hover { background: ${T.border}; color: ${T.ink}; border-color: ${T.borderMid}; }
  .auth-social-btn { background: ${T.white}; color: ${T.inkMid}; border: 1px solid ${T.border}; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s; text-decoration: none; }
  .auth-social-btn:hover { background: ${T.cardHover}; color: ${T.ink}; border-color: ${T.borderMid}; }
  .auth-input-wrap { border: 1.5px solid ${T.borderMid}; border-radius: 8px; background: ${T.white}; transition: border-color 0.2s, box-shadow 0.2s; }
  .auth-input-wrap:focus-within { border-color: ${T.amber}; box-shadow: 0 0 0 3px rgba(196,131,10,0.12); }
  .auth-input-field { width: 100%; background: none; border: none; outline: none; font-size: 13px; color: ${T.ink}; font-family: 'Inter', sans-serif; }
  .auth-input-field::placeholder { color: ${T.inkFaint}; }
  .auth-google-btn { width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 9px 14px; border-radius: 8px; border: 1px solid ${T.border}; background: ${T.white}; color: ${T.inkMid}; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s; font-family: 'Inter', sans-serif; }
  .auth-google-btn:hover:not(:disabled) { background: ${T.cardHover}; border-color: ${T.borderMid}; color: ${T.ink}; }
  .auth-google-btn:disabled { opacity: 0.6; cursor: not-allowed; }
  @keyframes authSpin { to { transform: rotate(360deg); } }
  @keyframes authFadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .auth-fade-up { animation: authFadeUp 0.3s ease forwards; }
  @media (max-width: 768px) { .auth-hidden-mobile { display: none !important; } }
`;

// ─── Subtle paper backdrop (matches the muted, warm tone of the main app) ────
function BackgroundTexture() {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        background: `
          radial-gradient(600px 400px at 12% 15%, ${T.amberBg} 0%, transparent 60%),
          radial-gradient(700px 500px at 90% 85%, ${T.sidebarBg} 0%, transparent 55%)
        `,
      }}
    />
  );
}

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleEmailAuth(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      if (mode === "signup") {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setSuccess("Check your email to confirm your account.");
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleAuth() {
    setError(null);
    setGoogleLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/auth/callback` },
      });
      if (error) throw error;
    } catch (err) {
      setError(err.message);
      setGoogleLoading(false);
    }
  }

  function switchMode(m) {
    setMode(m);
    setError(null);
    setSuccess(null);
  }

  return (
    <>
      <style>{GLOBAL_CSS}</style>
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden",
          padding: "24px 16px",
          background: T.cream,
          fontFamily: "'Inter', system-ui, sans-serif",
          color: T.ink,
        }}
      >
        <BackgroundTexture />

        {/* ── Main Card Shell ── */}
        <div
          className="auth-fade-up"
          style={{
            width: "100%",
            maxWidth: "1080px",
            minHeight: "620px",
            borderRadius: 16,
            padding: "40px",
            display: "flex",
            flexDirection: "column",
            position: "relative",
            zIndex: 2,
            background: T.white,
            border: `1px solid ${T.border}`,
            boxShadow: "0 8px 40px rgba(26,23,20,0.08)",
          }}
        >
          {/* ── Top Navigation Bar ── */}
          <header
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "60px",
            }}
          >
            {/* Logo Brand */}
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: T.ink,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <BookOpen size={18} color={T.cream} />
              </div>
              <span
                style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontStyle: "italic",
                  fontWeight: 400,
                  fontSize: 18,
                  letterSpacing: "-0.01em",
                  color: T.ink,
                }}
              >
                Recall
              </span>
            </div>

            {/* Nav CTAs */}
            <button
              onClick={() => switchMode(mode === "login" ? "signup" : "login")}
              className="auth-btn-ghost"
              style={{ padding: "6px 14px" }}
            >
              {mode === "login" ? "Create Account" : "Sign In"}
            </button>
          </header>

          {/* ── Left Content / Right Card Split ── */}
          <div style={{ display: "flex", flex: 1, gap: "40px" }}>
            {/* Headline and showcase */}
            <div
              className="auth-hidden-mobile"
              style={{
                flex: "0 0 55%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                paddingRight: "20px",
              }}
            >
              <h2
                style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontSize: "44px",
                  fontWeight: 700,
                  lineHeight: "1.15",
                  letterSpacing: "-0.02em",
                  margin: 0,
                  color: T.ink,
                }}
              >
                Intelligent
                <br />
                <span style={{ fontStyle: "italic", color: T.amber }}>
                  document shelf.
                </span>
              </h2>
              <p
                style={{
                  margin: "18px 0 32px",
                  fontSize: "14px",
                  lineHeight: "1.65",
                  color: T.inkMid,
                  maxWidth: "380px",
                }}
              >
                Search across your PDFs with semantic understanding. Scan,
                ingest, and jump straight to the passage you're looking for —
                highlighted, in context.
              </p>
              {/* Social Icons */}
              {/* <div style={{ display: "flex", gap: "12px", marginTop: "auto" }}>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="auth-social-btn"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                  </svg>
                </a>
                <a
                  href="https://twitter.com"
                  target="_blank"
                  rel="noreferrer"
                  className="auth-social-btn"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
                  </svg>
                </a>
                <a
                  href="https://studypdfsearch.com"
                  target="_blank"
                  rel="noreferrer"
                  className="auth-social-btn"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                </a>
              </div> */}
            </div>

            {/* Right Form Card */}
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div
                style={{
                  width: "100%",
                  maxWidth: "380px",
                  padding: "28px",
                  background: T.sidebarBg,
                  border: `1px solid ${T.border}`,
                  borderRadius: 12,
                  boxShadow: "0 2px 16px rgba(26,23,20,0.06)",
                }}
              >
                <div style={{ textAlign: "center", marginBottom: "20px" }}>
                  <h3
                    style={{
                      fontFamily: "'Playfair Display', Georgia, serif",
                      fontStyle: "italic",
                      fontWeight: 700,
                      fontSize: "18px",
                      color: T.ink,
                      margin: 0,
                    }}
                  >
                    {mode === "login" ? "Sign In" : "Register"}
                  </h3>
                  <p
                    style={{
                      fontSize: "11px",
                      color: T.inkFaint,
                      marginTop: "4px",
                    }}
                  >
                    {mode === "login"
                      ? "Access your study materials instantly"
                      : "Ingest documents in seconds"}
                  </p>
                </div>

                {/* Google OAuth Button */}
                <button
                  onClick={handleGoogleAuth}
                  disabled={googleLoading || loading}
                  className="auth-google-btn"
                  style={{ marginBottom: "16px" }}
                >
                  {googleLoading ? (
                    <Loader2
                      size={14}
                      style={{ animation: "authSpin 1s linear infinite" }}
                    />
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                  )}
                  {mode === "login"
                    ? "Continue with Google"
                    : "Register with Google"}
                </button>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    marginBottom: "16px",
                  }}
                >
                  <div style={{ flex: 1, height: 1, background: T.border }} />
                  <span
                    style={{
                      fontSize: "10px",
                      color: T.inkFaint,
                      fontWeight: 600,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    OR
                  </span>
                  <div style={{ flex: 1, height: 1, background: T.border }} />
                </div>

                {/* Form details */}
                <form
                  onSubmit={handleEmailAuth}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "11px",
                        fontWeight: 600,
                        color: T.inkMid,
                        marginBottom: "4px",
                      }}
                    >
                      Email address
                    </label>
                    <div
                      className="auth-input-wrap"
                      style={{
                        position: "relative",
                        display: "flex",
                        alignItems: "center",
                        padding: "8px 10px 8px 32px",
                      }}
                    >
                      <Mail
                        size={13}
                        color={T.inkFaint}
                        style={{
                          position: "absolute",
                          left: 10,
                          pointerEvents: "none",
                        }}
                      />
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        className="auth-input-field"
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "11px",
                        fontWeight: 600,
                        color: T.inkMid,
                        marginBottom: "4px",
                      }}
                    >
                      Password
                    </label>
                    <div
                      className="auth-input-wrap"
                      style={{
                        position: "relative",
                        display: "flex",
                        alignItems: "center",
                        padding: "8px 32px 8px 32px",
                      }}
                    >
                      <Lock
                        size={13}
                        color={T.inkFaint}
                        style={{
                          position: "absolute",
                          left: 10,
                          pointerEvents: "none",
                        }}
                      />
                      <input
                        type={showPassword ? "text" : "password"}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={6}
                        className="auth-input-field"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        style={{
                          position: "absolute",
                          right: 8,
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          color: T.inkFaint,
                          padding: 2,
                          display: "flex",
                        }}
                      >
                        {showPassword ? (
                          <EyeOff size={13} />
                        ) : (
                          <Eye size={13} />
                        )}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 6,
                        padding: "8px 10px",
                        borderRadius: 7,
                        background: T.dangerBg,
                        border: `1px solid ${T.dangerBorder}`,
                      }}
                    >
                      <AlertCircle
                        size={12}
                        color={T.danger}
                        style={{ marginTop: 1, flexShrink: 0 }}
                      />
                      <p
                        style={{
                          margin: 0,
                          fontSize: "11px",
                          color: T.danger,
                          lineHeight: 1.4,
                        }}
                      >
                        {error}
                      </p>
                    </div>
                  )}

                  {success && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 6,
                        padding: "8px 10px",
                        borderRadius: 7,
                        background: T.successBg,
                        border: `1px solid ${T.successBorder}`,
                      }}
                    >
                      <CheckCircle
                        size={12}
                        color={T.success}
                        style={{ marginTop: 1, flexShrink: 0 }}
                      />
                      <p
                        style={{
                          margin: 0,
                          fontSize: "11px",
                          color: T.success,
                          lineHeight: 1.4,
                        }}
                      >
                        {success}
                      </p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading || googleLoading}
                    className="auth-btn-primary"
                    style={{
                      width: "100%",
                      padding: "9px 0",
                      fontSize: "12px",
                      marginTop: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 6,
                    }}
                  >
                    {loading && (
                      <Loader2
                        size={13}
                        style={{ animation: "authSpin 1s linear infinite" }}
                      />
                    )}
                    {mode === "login" ? "Sign In" : "Register"}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
