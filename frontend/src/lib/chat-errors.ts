import { ApiError } from '@/lib/http'

export interface ClassifiedChatError {
  title: string
  message: string
  showLoginLink: boolean
}

export function classifyChatError(error: unknown): ClassifiedChatError {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return {
          title: 'Session expired',
          message: 'Please sign in again to continue chatting.',
          showLoginLink: true,
        }
      case 403:
        return {
          title: 'Access denied',
          message: 'You do not have permission to access this conversation.',
          showLoginLink: false,
        }
      case 404:
        return {
          title: 'Conversation not found',
          message: 'This conversation may have been deleted or never existed.',
          showLoginLink: false,
        }
      case 429:
        return {
          title: 'Too many requests',
          message: 'Please wait a moment before sending another message.',
          showLoginLink: false,
        }
      case 500:
      case 502:
      case 503:
      case 504:
        return {
          title: 'Server error',
          message: 'Something went wrong on our end. Please try again in a moment.',
          showLoginLink: false,
        }
      default:
        return {
          title: 'Request failed',
          message: error.message ?? 'An unexpected error occurred.',
          showLoginLink: false,
        }
    }
  }

  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      title: 'Connection failed',
      message: 'Unable to reach the server. Check your internet connection.',
      showLoginLink: false,
    }
  }

  return {
    title: 'Unexpected error',
    message: error instanceof Error ? error.message : 'An unknown error occurred.',
    showLoginLink: false,
  }
}