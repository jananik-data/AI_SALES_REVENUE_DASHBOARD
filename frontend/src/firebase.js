import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// Your web app's Firebase configuration
export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDVOjKbKhUV6V5agRCDFwy4FS1pNA_Wfw0",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "revpulse-ai-15f12.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "revpulse-ai-15f12",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "revpulse-ai-15f12.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "890059663007",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:890059663007:web:36c059b76f7010d49aa4aa",
  measurementId: "G-DHTHEE5765"
};

// Check if Firebase is configured
export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId
);

// Initialize Firebase App
const app = isFirebaseConfigured
  ? (getApps().length > 0 ? getApp() : initializeApp(firebaseConfig))
  : null;

// Initialize Firebase Auth
export const auth = app ? getAuth(app) : null;

// Configure Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

export default app;
