import { createApp } from 'vue'
import App from './App.vue'
import router from './router';
import { createPinia} from 'pinia';
import { IonicVue } from '@ionic/vue';
import { defineCustomElements } from '@ionic/pwa-elements/loader'
// Apollo Client
import { DefaultApolloClient } from '@vue/apollo-composable';
import ApolloClient from './apollo-client';

defineCustomElements(window);

/* Core CSS required for Ionic components to work properly */
import '@ionic/vue/css/core.css';

/* Basic CSS for apps built with Ionic */
import '@ionic/vue/css/normalize.css';
import '@ionic/vue/css/structure.css';
import '@ionic/vue/css/typography.css';

import { addIcons } from 'ionicons';
import { chatbubble, compass,  share, contract, home, add, remove, pin, heart, settings, homeOutline, mapOutline, personAddOutline, personCircleOutline, addCircleOutline, logInOutline, alertCircleOutline, locationOutline, timeOutline, logOutOutline } from 'ionicons/icons';
addIcons({
  compass,
  add,
  remove,
  home,
  pin,
  contract,
  heart,
  chatbubble,
  share,
  homeOutline,
  mapOutline,
  personAddOutline,
  personCircleOutline,
  addCircleOutline,
  logInOutline,
  alertCircleOutline,
  locationOutline,
  timeOutline,
  logOutOutline
})

/* Optional CSS utils that can be commented out */
import '@ionic/vue/css/padding.css';
import '@ionic/vue/css/float-elements.css';
import '@ionic/vue/css/text-alignment.css';
import '@ionic/vue/css/text-transformation.css';
import '@ionic/vue/css/flex-utils.css';
import '@ionic/vue/css/display.css';
import 'leaflet/dist/leaflet.css';
/**
 * Ionic Dark Mode
 * -----------------------------------------------------
 * For more info, please see:
 * https://ionicframework.com/docs/theming/dark-mode
 */

import '@ionic/vue/css/palettes/dark.always.css'; 
/* @import '@ionic/vue/css/palettes/dark.class.css'; */
// import '@ionic/vue/css/palettes/dark.system.css';

/* Theme variables */
import './theme/variables.css';


const pinia = createPinia();

const app = createApp(App)
  .use(IonicVue)
  .use(router).use(pinia)

app.provide(DefaultApolloClient, ApolloClient);

router.isReady().then(() => {
  app.mount('#app');
});
