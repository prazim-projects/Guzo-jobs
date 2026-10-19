import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '@/stores/userStore';

const api = vi.hoisted(() => ({ mutate: vi.fn(), clearStore: vi.fn().mockResolvedValue(undefined), push: vi.fn() }));
vi.mock('@vue/apollo-composable', () => ({ useApolloClient: () => ({ client: api }) }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: api.push }) }));

beforeEach(() => { localStorage.clear(); setActivePinia(createPinia()); api.mutate.mockReset(); });

describe('Security benchmark: authentication state', () => {
  it('starts unauthenticated without a stored session', () => expect(useAuthStore().isAuthenticated).toBe(false));
  it('recovers from corrupted local user JSON', () => {
    localStorage.setItem('user', '{invalid');
    expect(() => useAuthStore()).not.toThrow();
  });
  it('does not trust an expired persisted JWT', () => {
    const payload = btoa(JSON.stringify({ exp: 1, username: 'expired' }));
    localStorage.setItem('authToken', `eyJhbGciOiJIUzI1NiJ9.${payload}.invalid`);
    localStorage.setItem('user', JSON.stringify({ id: '1' }));
    expect(useAuthStore().isAuthenticated).toBe(false);
  });
  it('rejects incomplete sessions', () => {
    expect(() => useAuthStore().acceptSession('token', {})).toThrow('Invalid authentication response');
    expect(localStorage.getItem('authToken')).toBeNull();
  });
  it('clears cached private data when accepting a Fayda session', () => {
    useAuthStore().acceptSession('test-token', { id: '1' });
    expect(api.clearStore).toHaveBeenCalledOnce();
  });
  it('clears cached private data when switching accounts through login', async () => {
    api.mutate.mockResolvedValue({ data: { tokenAuth: { token: 'new-token', user: { id: '2' } } } });
    await useAuthStore().login('second-user', 'test-password');
    expect(api.clearStore).toHaveBeenCalledOnce();
  });
  it('clears credentials and the GraphQL cache on logout', () => {
    const store = useAuthStore();
    store.acceptSession('test-token', { id: '1' }); api.clearStore.mockClear();
    store.logout();
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(localStorage.getItem('authToken')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(api.clearStore).toHaveBeenCalledOnce();
    expect(api.push).toHaveBeenCalledWith('/home');
  });
});
