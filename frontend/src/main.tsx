import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { TranslationProvider } from '@/hooks/useTranslation'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TranslationProvider>
      <App />
    </TranslationProvider>
  </StrictMode>,
)