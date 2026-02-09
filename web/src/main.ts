import { createApp } from 'vue'
import { createPinia } from 'pinia'
import i18n from './locales'
import { vSound } from './directives/vSound'
import './style.css'
import App from './App.vue'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(i18n)
app.directive('sound', vSound)
app.mount('#app')
