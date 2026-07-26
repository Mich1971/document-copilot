import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { es } from '@/i18n/es';
import { en } from '@/i18n/en';
import { pt } from '@/i18n/pt';
import type { Dictionary } from '@/i18n/es';

type Language = 'es' | 'en' | 'pt';

interface TranslationContextType {
    t: Dictionary;
    language: Language;
    setLanguage: (lang: Language) => void;
}

const dictionaries: Record<Language, Dictionary> = { es, en, pt };

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export function TranslationProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>(() => {
        const saved = localStorage.getItem('app-language');
        return (saved === 'en' || saved === 'pt' || saved === 'es') ? saved : 'es';
    });

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('app-language', lang);
    };

    return (
        <TranslationContext.Provider value={{ t: dictionaries[language], language, setLanguage }}>
            {children}
        </TranslationContext.Provider>
    );
}

export function useTranslation() {
    const context = useContext(TranslationContext);
    if (!context) {
        throw new Error('useTranslation must be used within a TranslationProvider');
    }
    return context;
}