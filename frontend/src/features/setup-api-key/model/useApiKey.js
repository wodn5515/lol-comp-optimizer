import { create } from 'zustand';

const STORAGE_KEY = 'lol-comp-api-key';

function loadApiKey() {
  try {
    return localStorage.getItem(STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

function saveApiKey(key) {
  try {
    if (key) {
      localStorage.setItem(STORAGE_KEY, key);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage not available
  }
}

export const useApiKeyStore = create((set) => ({
  apiKey: loadApiKey(),
  isValid: loadApiKey().startsWith('RGAPI-'),

  setApiKey: (key) => {
    saveApiKey(key);
    set({ apiKey: key, isValid: key.startsWith('RGAPI-') });
  },

  clearApiKey: () => {
    saveApiKey('');
    set({ apiKey: '', isValid: false });
  },
}));
