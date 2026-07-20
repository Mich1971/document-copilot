import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Dashboard } from '@/pages/Dashboard'
import { ChatEmptyPage } from '@/pages/chat/ChatEmptyPage'
import { ChatThreadPage } from '@/pages/chat/ChatThreadPage'
import { Login } from '@/pages/Login'
import { SignUp } from '@/pages/SignUp'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chats" element={<ChatEmptyPage />} />
          <Route path="/chats/:threadId" element={<ChatThreadPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
