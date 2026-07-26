export const es = {
    auth: {
        signIn: 'Iniciar sesión',
        signUp: 'Crear cuenta',
        email: 'Correo electrónico',
        password: 'Contraseña',
        signInDesc: 'Utilice su correo y contraseña para acceder a Document Copilot.',
        signUpDesc: 'Regístrese con su correo electrónico para utilizar Document Copilot.',
        noAccount: '¿No tienes una cuenta?',
        hasAccount: '¿Ya tienes una cuenta?',
        signingIn: 'Iniciando sesión...',
        creatingAccount: 'Creando cuenta...',
    },
    chat: {
        newChat: 'Nuevo chat',
        placeholder: 'Pregunta sobre los archivos...',
        generating: 'Generando respuesta...',
        emptyTitle: '¿En qué puedo ayudarte con tus archivos?',
        emptyDesc: 'Pregunta sobre los archivos. Cada respuesta está fundamentada en documentos fuente con citas verificables.',
        sources: 'Fuentes',
        sourcePassage: 'Pasaje fuente',
        closePanel: 'Cerrar panel',
        copyExcerpt: 'Copiar fragmento',
    },
    common: {
        loading: 'Cargando...',
        error: 'Error',
        retry: 'Reintentar',
        signOut: 'Cerrar sesión',
        settings: 'Configuración',
    }
};

export type Dictionary = typeof es;