import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enTranslation from './locales/en.json';
import viTranslation from './locales/vi.json';

// Read saved language from localStorage, fallback to 'en'
const savedLanguage = localStorage.getItem('app_language') || 'en';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslation },
      vi: { translation: viTranslation }
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

// Persist language changes to localStorage
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('app_language', lng);
});
