import type { Dictionary } from './es';

export const en: Dictionary = {
    auth: {
        signIn: 'Sign in',
        signUp: 'Create account',
        email: 'Email address',
        password: 'Password',
        signInDesc: 'Use your email and password to access Document Copilot.',
        signUpDesc: 'Register with your email to use Document Copilot.',
        noAccount: 'Need an account?',
        hasAccount: 'Already have an account?',
        signingIn: 'Signing in...',
        creatingAccount: 'Creating account...',
    },
    chat: {
        newChat: 'New chat',
        placeholder: 'Ask about the files...',
        generating: 'Generating response...',
        emptyTitle: 'How can I help you with your files?',
        emptyDesc: 'Ask about the files. Every answer is grounded in source documents with verifiable citations.',
        sources: 'Sources',
        sourcePassage: 'Source passage',
        closePanel: 'Close panel',
        copyExcerpt: 'Copy excerpt',
    },
    common: {
        loading: 'Loading...',
        error: 'Error',
        retry: 'Retry',
        signOut: 'Sign out',
        settings: 'Settings',
    }
};