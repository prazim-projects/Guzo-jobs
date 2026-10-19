import { Capacitor } from '@capacitor/core';

// The welcome screen does not need Ionic, Apollo, app icons or native plugins.
const route = location.hash.slice(1).split('?')[0];
const bypassOnboarding = ['/reset-password', '/fayda/callback'].includes(route);
if (!Capacitor.isNativePlatform() && !bypassOnboarding && localStorage.getItem('onboardingCompleted') !== 'true') {
  void import('./onboarding').then(({ mountOnboarding }) => mountOnboarding());
} else {
  void import('./bootstrap');
}
