import { createApp } from 'vue';
import OnboardingContent from './components/OnboardingContent.vue';

export function mountOnboarding() {
  history.replaceState(null, '', `${location.pathname}${location.search}#/onboarding`);
  let started = false;
  const app = createApp(OnboardingContent, {
    onComplete() {
      localStorage.setItem('onboardingCompleted', 'true');
      history.replaceState(null, '', `${location.pathname}${location.search}#/home`);
      startApp();
    },
  });
  function startApp() {
    if (started) return;
    started = true;
    window.removeEventListener('hashchange', onHashChange);
    app.unmount();
    const root = document.querySelector('#app');
    if (root) {
      root.textContent = 'Loading Guzo Jobs…';
      root.setAttribute('role', 'status');
    }
    void import('./bootstrap').then(() => root?.removeAttribute('role')).catch(() => {
      if (root) root.textContent = 'Unable to load the app. Check your connection and reload this page.';
    });
  }
  function onHashChange() {
    const path = location.hash.slice(1).split('?')[0];
    if (['/reset-password', '/fayda/callback'].includes(path) || localStorage.getItem('onboardingCompleted') === 'true') startApp();
  }
  app.mount('#app');
  window.addEventListener('hashchange', onHashChange);
}
