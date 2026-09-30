import { VueQueryPlugin } from '@tanstack/vue-query'
import { createApp } from 'vue'

import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/outfit/400.css'
import '@fontsource/outfit/500.css'
import '@fontsource/outfit/600.css'

import App from './App.vue'
import router from './router'
import './styles/theme.css'

const app = createApp(App)

app.use(router)
app.use(VueQueryPlugin)

app.mount('#app')
