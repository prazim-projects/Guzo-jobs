import { Capacitor } from '@capacitor/core';
import { Browser } from '@capacitor/browser';

export const faydaBackendUrl = (path: string) => {
  const graphqlUrl = import.meta.env.VITE_GRAPHQL_ENDPOINT ||
    (import.meta.env.DEV ? 'http://10.0.2.2:8000/graphql/' : '');
  if (!graphqlUrl) throw new Error('Fayda sign-in is not configured.');
  return new URL(path, new URL(graphqlUrl, window.location.href).origin).toString();
};

export const faydaPlatform = () => Capacitor.getPlatform() === 'android' ? 'android' : 'web';

export const openFaydaUrl = async (url: string) => {
  if (faydaPlatform() === 'android') {
    await Browser.open({ url });
  } else {
    window.location.assign(url);
  }
};

export const startFayda = async () => {
  const native = faydaPlatform() === 'android';
  const url = faydaBackendUrl(`/auth/fayda/start/${native ? '?platform=android' : ''}`);
  await openFaydaUrl(url);
};
