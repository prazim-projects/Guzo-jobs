import { beforeEach, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import HomePage from '@/views/HomePage.vue'
import { describe, expect, test } from 'vitest'

const api = vi.hoisted(() => ({ subscribe: vi.fn(), unsubscribe: vi.fn(), stopPolling: vi.fn(), refetch: vi.fn() }));
vi.mock('@/stores/userStore', () => ({ useAuthStore: () => ({ user: null, isAuthenticated: false }) }));
vi.mock('@vue/apollo-composable', () => ({ useApolloClient: () => ({ client: {
  watchQuery: () => ({ subscribe: api.subscribe, stopPolling: api.stopPolling, refetch: api.refetch }),
} }) }));
beforeEach(() => { api.subscribe.mockReturnValue({ unsubscribe: api.unsubscribe }); });

describe('HomePage.vue', () => {
  test('renders the actual home heading and loading state', () => {
    const wrapper = shallowMount(HomePage, { global: { renderStubDefaultSlot: true } })
    expect(wrapper.text()).toContain('Welcome to Guzo Jobs')
    expect(wrapper.text()).toContain('Loading...')
    wrapper.unmount();
    expect(api.unsubscribe).toHaveBeenCalledOnce();
    expect(api.stopPolling).toHaveBeenCalledOnce();
  })
})
