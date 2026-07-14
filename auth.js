/**
 * auth.js — Simple password authentication + Supabase client.
 * Load AFTER the supabase-js CDN script and BEFORE page scripts.
 *
 * Exposes:
 *   window.sbClient          — shared Supabase client
 *   window.Auth.isSignedIn() — boolean
 *   window.Auth.requireAuth()— Promise<true|null> (shows password modal if not authenticated)
 *   window.Auth.signOut()
 *   window.escapeHtml(str)   — shared HTML escaper
 */
(function () {
  'use strict';

  var SUPABASE_URL = 'https://pjorqdzlzgwqpivoibyx.supabase.co';
  var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqb3JxZHpsemd3cXBpdm9pYnl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1NjM5MjUsImV4cCI6MjA5MzEzOTkyNX0.TWTRGFbN9Pommqx6VW4N3M1KaO6L0FN0LXZ6lf2ZA5Q';
  var PASSWORD_HASH = '5bd887caace65b71b8056d531a5a7653986a2677f6597053c89aef0e07cb46ea';
  var SESSION_KEY = 'scout_authenticated';

  if (typeof supabase === 'undefined' || !supabase.createClient) {
    console.error('[Auth] supabase-js not loaded — include the CDN script before auth.js');
    return;
  }

  window.sbClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  // Shared escaper
  window.escapeHtml = function (str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  // SHA-256 hash function
  async function sha256(message) {
    var msgBuffer = new TextEncoder().encode(message);
    var hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    var hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  }

  var pendingResolve = null;

  function buildModal() {
    if (document.getElementById('auth-modal')) return;
    var overlay = document.createElement('div');
    overlay.id = 'auth-modal';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:99999;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;';
    overlay.innerHTML =
      '<div style="background:#fff;border-radius:12px;padding:28px;width:320px;max-width:90vw;box-shadow:0 10px 40px rgba(0,0,0,.3);">' +
      '<h3 style="margin:0 0 4px;font-size:18px;color:#1a1a2e;">Scout Access</h3>' +
      '<p style="margin:0 0 16px;font-size:13px;color:#666;">Enter password to continue.</p>' +
      '<input id="auth-pw" type="password" placeholder="Password" autocomplete="current-password" style="width:100%;box-sizing:border-box;padding:10px;margin-bottom:8px;border:1px solid #ccc;border-radius:6px;font-size:14px;">' +
      '<div id="auth-err" style="color:#0071e3;font-size:12px;min-height:16px;margin-bottom:8px;"></div>' +
      '<button id="auth-submit" style="width:100%;padding:10px;background:#0071e3;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;">Sign In</button>' +
      '<button id="auth-cancel" style="width:100%;padding:8px;margin-top:6px;background:none;color:#666;border:none;font-size:13px;cursor:pointer;">Cancel</button>' +
      '</div>';
    document.body.appendChild(overlay);

    async function submit() {
      var pw = document.getElementById('auth-pw').value;
      var err = document.getElementById('auth-err');
      err.textContent = '';
      if (!pw) { err.textContent = 'Enter password.'; return; }

      var hash = await sha256(pw);
      if (hash === PASSWORD_HASH) {
        sessionStorage.setItem(SESSION_KEY, 'true');
        overlay.style.display = 'none';
        document.getElementById('auth-pw').value = '';
        if (pendingResolve) { pendingResolve(true); pendingResolve = null; }
      } else {
        err.textContent = 'Incorrect password.';
      }
    }

    document.getElementById('auth-submit').addEventListener('click', submit);
    document.getElementById('auth-pw').addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); });
    document.getElementById('auth-cancel').addEventListener('click', function () {
      overlay.style.display = 'none';
      document.getElementById('auth-pw').value = '';
      if (pendingResolve) { pendingResolve(null); pendingResolve = null; }
    });
  }

  window.Auth = {
    isSignedIn: function () {
      return sessionStorage.getItem(SESSION_KEY) === 'true';
    },

    requireAuth: function () {
      if (window.Auth.isSignedIn()) {
        return Promise.resolve(true);
      }
      buildModal();
      document.getElementById('auth-err').textContent = '';
      document.getElementById('auth-modal').style.display = 'flex';
      document.getElementById('auth-pw').focus();
      return new Promise(function (resolve) { pendingResolve = resolve; });
    },

    signOut: function () {
      sessionStorage.removeItem(SESSION_KEY);
      return Promise.resolve();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildModal);
  } else {
    buildModal();
  }
})();
