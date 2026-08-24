import React, { useState } from 'react';
import { 
  Sparkles, 
  Lock, 
  User, 
  Mail, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  KeyRound,
  X,
  Send,
  Check
} from 'lucide-react';
import { signInWithPopup, sendPasswordResetEmail } from 'firebase/auth';
import { auth, googleProvider, isFirebaseConfigured } from '../firebase';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../api/client';

export default function LoginPage() {
  const { login, register, demoLogin, googleLogin, resetPassword } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  // Forgot Password Modal State
  const [isForgotOpen, setIsForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSuccessMsg, setForgotSuccessMsg] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState(null);

  // Handle Tab Switch (Clean state to prevent old credentials from persisting)
  const handleTabSwitch = (toRegister) => {
    setIsRegister(toRegister);
    setUsername('');
    setEmail('');
    setPassword('');
    setError(null);
  };

  // Handle "Continue with Google" click via Real Firebase Google Auth
  const handleGoogleButtonClick = async () => {
    setError(null);

    // 1. Check if Firebase configuration is provided
    if (!isFirebaseConfigured || !auth) {
      setError(
        'Firebase configuration is missing. Please add your Firebase project keys to frontend/.env file.'
      );
      return;
    }

    setGoogleLoading(true);

    try {
      // 2. Launch Google's Official Account Chooser via Firebase Popup
      const result = await signInWithPopup(auth, googleProvider);
      const firebaseUser = result.user;
      const idToken = await firebaseUser.getIdToken();

      // 3. Send verified Firebase credentials to FastAPI backend
      await googleLogin({
        id_token: idToken,
        email: firebaseUser.email,
        displayName: firebaseUser.displayName,
        uid: firebaseUser.uid,
        photoURL: firebaseUser.photoURL
      });
    } catch (err) {
      console.error('Firebase Google Sign-In error:', err);
      if (err.code === 'auth/popup-closed-by-user' || err.code === 'auth/cancelled-popup-request') {
        // User voluntarily closed popup window
      } else if (err.code === 'auth/unauthorized-domain') {
        const currentDomain = window.location.hostname || 'your domain';
        setError(
          `Domain "${currentDomain}" is not authorized in your Firebase Console. Go to Firebase Console -> Authentication -> Settings -> Authorized domains and add "${currentDomain}".`
        );
      } else if (err.code === 'auth/popup-blocked') {
        setError('Popup was blocked by your browser. Please enable popups for this site and try again.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Firebase Google authentication failed.');
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(username.trim(), email.trim(), password);
      } else {
        await login(username.trim(), password);
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        setError(`Unable to connect to backend server at ${API_BASE_URL}. If the backend was sleeping, please wait 30 seconds and try again.`);
      } else {
        setError('Authentication failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setDemoLoading(true);
    try {
      await demoLogin();
    } catch (err) {
      console.error('Demo login error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        setError(`Unable to connect to backend at ${API_BASE_URL}. Please check VITE_API_URL or wait for backend startup.`);
      } else {
        setError('Demo login failed. Please try again.');
      }
    } finally {
      setDemoLoading(false);
    }
  };

  // Send real password reset link to user email via Firebase Authentication
  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    const cleanEmail = forgotEmail.trim();
    if (!cleanEmail) {
      setForgotError('Please enter your email address.');
      return;
    }

    if (!auth) {
      setForgotError('Firebase Authentication is not initialized. Please verify frontend/.env settings.');
      return;
    }

    setForgotLoading(true);
    setForgotError(null);
    setForgotSuccessMsg('');

    try {
      // Call Firebase Authentication sendPasswordResetEmail
      await sendPasswordResetEmail(auth, cleanEmail);
      setForgotSuccessMsg(
        `We have sent a password reset link to ${cleanEmail}. Please check your email inbox (and spam folder) to reset your password.`
      );
    } catch (err) {
      console.error('Firebase password reset dispatch error:', err);
      if (err.code === 'auth/user-not-found') {
        setForgotError('No registered account found with this email address.');
      } else if (err.code === 'auth/invalid-email') {
        setForgotError('Please enter a valid email address.');
      } else if (err.code === 'auth/missing-email') {
        setForgotError('Please provide a valid email address.');
      } else if (err.code === 'auth/too-many-requests') {
        setForgotError('Too many password reset requests. Please wait a moment and try again.');
      } else {
        setForgotError(err.message || 'Failed to send password reset email. Please check your email and try again.');
      }
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
      background: '#070a14'
    }}>
      {/* Background Animated Glowing Mesh & Floating Orbs */}
      <div style={{
        position: 'absolute',
        width: '450px',
        height: '450px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, rgba(99, 102, 241, 0) 70%)',
        top: '-10%',
        left: '15%',
        filter: 'blur(45px)',
        pointerEvents: 'none',
        animation: 'floatOrb1 10s ease-in-out infinite'
      }} />

      <div style={{
        position: 'absolute',
        width: '500px',
        height: '500px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6, 182, 212, 0.22) 0%, rgba(6, 182, 212, 0) 70%)',
        bottom: '-12%',
        right: '10%',
        filter: 'blur(50px)',
        pointerEvents: 'none',
        animation: 'floatOrb2 12s ease-in-out infinite'
      }} />

      <div style={{
        position: 'absolute',
        width: '350px',
        height: '350px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(236, 72, 153, 0.16) 0%, rgba(236, 72, 153, 0) 70%)',
        top: '40%',
        right: '25%',
        filter: 'blur(40px)',
        pointerEvents: 'none',
        animation: 'floatOrb3 9s ease-in-out infinite'
      }} />

      {/* Grid Pattern Overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px)',
        backgroundSize: '24px 24px',
        pointerEvents: 'none',
        opacity: 0.6
      }} />

      {/* Main Glassmorphic Login Card */}
      <div
        className="glass-card login-card-entrance"
        style={{
          width: '100%',
          maxWidth: '450px',
          padding: '38px 32px',
          position: 'relative',
          zIndex: 10,
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(99, 102, 241, 0.2)'
        }}
      >
        {/* Floating Top AI Tag */}
        <div style={{ textAlign: 'center', marginBottom: '10px' }}>
          <span
            className="badge badge-primary badge-floating"
            style={{
              fontSize: '11px',
              padding: '4px 12px',
              background: 'rgba(99, 102, 241, 0.18)',
              borderColor: 'rgba(99, 102, 241, 0.4)'
            }}
          >
            ✨ AI-Powered Intelligence Platform
          </span>
        </div>

        {/* Brand Logo & Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 24px rgba(99, 102, 241, 0.6)',
            marginBottom: '10px'
          }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <h1 style={{ fontSize: '23px', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>
            RevPulse <span style={{ color: '#818cf8' }}>AI</span>
          </h1>
          <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Enterprise Sales & Revenue Forecasting Suite
          </p>
        </div>

        {/* Real Continue with Google Button (Firebase Google Auth) */}
        <button
          type="button"
          onClick={handleGoogleButtonClick}
          disabled={googleLoading || loading}
          style={{
            width: '100%',
            padding: '11px 16px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            background: 'rgba(255, 255, 255, 0.06)',
            color: '#f8fafc',
            fontSize: '13.5px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            cursor: 'pointer',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            marginBottom: '14px',
            fontFamily: 'inherit'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.28)';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.14)';
            e.currentTarget.style.transform = 'none';
          }}
        >
          {/* Official Google SVG Icon */}
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z" />
            <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.26v3.15C3.29 21.36 7.36 24 12 24z" />
            <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.26C.46 8.16 0 9.94 0 12s.46 3.84 1.26 5.42l4.02-3.15z" />
            <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.36 0 3.29 2.64 1.26 6.58l4.02 3.15c.95-2.83 3.6-4.98 6.72-4.98z" />
          </svg>
          <span>{googleLoading ? 'Connecting to Google...' : 'Continue with Google'}</span>
        </button>

        {/* Divider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          margin: '16px 0',
          color: 'var(--text-muted)',
          fontSize: '11.5px'
        }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-glass)' }} />
          <span>or sign in with username or email</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-glass)' }} />
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '4px',
          background: 'rgba(15, 23, 42, 0.7)',
          padding: '4px',
          borderRadius: '8px',
          marginBottom: '18px',
          border: '1px solid var(--border-glass)'
        }}>
          <button
            type="button"
            onClick={() => handleTabSwitch(false)}
            style={{
              padding: '7px',
              border: 'none',
              borderRadius: '6px',
              background: !isRegister ? '#6366f1' : 'transparent',
              color: '#fff',
              fontWeight: 600,
              fontSize: '12.5px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch(true)}
            style={{
              padding: '7px',
              border: 'none',
              borderRadius: '6px',
              background: isRegister ? '#6366f1' : 'transparent',
              color: '#fff',
              fontWeight: 600,
              fontSize: '12.5px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Register
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            fontSize: '12px',
            marginBottom: '16px',
            lineHeight: '1.4'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} autoComplete="off">
          <div className="form-group">
            <label className="form-label">{isRegister ? 'Username' : 'Username or Email'}</label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder={isRegister ? "Choose a username" : "Enter username or email"}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="off"
                required
              />
            </div>
          </div>

          {isRegister && (
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="email"
                  className="form-input"
                  style={{ paddingLeft: '36px' }}
                  placeholder="analyst@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="off"
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
              {!isRegister && (
                <button
                  type="button"
                  onClick={() => {
                    setIsForgotOpen(true);
                    setForgotSuccessMsg('');
                    setForgotError(null);
                    setForgotIdentifier(username || '');
                    setNewPassword('');
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#818cf8',
                    fontSize: '11.5px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0,
                    fontFamily: 'inherit'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  Forgot password?
                </button>
              )}
            </div>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '6px', padding: '11px' }}
            disabled={loading || googleLoading || demoLoading}
          >
            <span>{loading ? 'Authenticating...' : isRegister ? 'Create Analyst Account' : 'Sign In to Dashboard'}</span>
            <ArrowRight size={16} />
          </button>

          {/* 1-Click Instant Demo Guest Login Button */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading || googleLoading || demoLoading}
            style={{
              width: '100%',
              marginTop: '12px',
              padding: '10px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(99, 102, 241, 0.12)',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              color: '#a5b4fc',
              fontSize: '12.5px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(99, 102, 241, 0.22)';
              e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.55)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(99, 102, 241, 0.12)';
              e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.35)';
            }}
          >
            <Sparkles size={15} color="#818cf8" />
            <span>{demoLoading ? 'Launching Demo...' : '⚡ 1-Click Instant Demo Access (No Password)'}</span>
          </button>
        </form>
      </div>

      {/* Forgot Password Modal */}
      {isForgotOpen && (
        <div className="modal-overlay" onClick={() => setIsForgotOpen(false)}>
          <div
            className="modal-content"
            style={{ maxWidth: '420px', padding: '28px' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <KeyRound size={18} color="#818cf8" />
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>Reset Password</h3>
              </div>
              <button
                onClick={() => setIsForgotOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            {forgotError && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 12px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#f87171',
                fontSize: '12px',
                marginBottom: '14px'
              }}>
                <AlertCircle size={15} style={{ flexShrink: 0 }} />
                <span>{forgotError}</span>
              </div>
            )}

            {!forgotSuccessMsg ? (
              <form onSubmit={handleForgotSubmit}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.5' }}>
                  Enter your registered account email and we will send a password reset link directly to your inbox.
                </p>

                <div className="form-group">
                  <label className="form-label">Account Email Address</label>
                  <div style={{ position: 'relative' }}>
                    <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="email"
                      className="form-input"
                      style={{ paddingLeft: '36px' }}
                      placeholder="analyst@company.com"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: '100%', marginTop: '8px', padding: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                  disabled={forgotLoading}
                >
                  <Send size={15} />
                  <span>{forgotLoading ? 'Dispatching Reset Link...' : 'Send Reset Link to Email'}</span>
                </button>
              </form>
            ) : (
              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '12px'
                }}>
                  <CheckCircle2 size={24} />
                </div>
                <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>
                  Reset Link Sent!
                </h4>
                <p style={{ fontSize: '12.5px', color: '#cbd5e1', lineHeight: '1.5', marginBottom: '16px' }}>
                  {forgotSuccessMsg}
                </p>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%' }}
                  onClick={() => setIsForgotOpen(false)}
                >
                  Back to Sign In
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
