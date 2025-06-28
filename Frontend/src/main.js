import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'

// Global error handler
const handleError = (err, vm, info) => {
  console.error('Global error:', err)
  console.error('Component:', vm)
  console.error('Error info:', info)
  
  // You can add error reporting service here (e.g., Sentry)
  // reportError(err)
}

// Create the Vue app with modern configuration
const app = createApp(App)

// Global error handler
app.config.errorHandler = handleError

// Global properties (if needed)
app.config.globalProperties.$appName = 'Smart Agentic Web App'

// Performance optimization: disable devtools in production
if (import.meta.env.PROD) {
  app.config.devtools = false
}

// Mount the app
app.mount('#app')

// Export for potential testing or external access
export default app
