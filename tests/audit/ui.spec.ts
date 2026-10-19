import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { IonInput, IonButton } from '@ionic/vue';
import Login from '@/views/login.vue';
import Register from '@/views/register.vue';
import ResetPassword from '@/views/ResetPassword.vue';
import { setLanguage } from '@/utils/i18n';

const api = vi.hoisted(() => ({ login: vi.fn(), register: vi.fn(), mutate: vi.fn(), push: vi.fn(), replace: vi.fn(), isAuthenticated: false, query: {} as Record<string, string> }));
vi.mock('@/stores/userStore', () => ({ useAuthStore: () => api }));
vi.mock('vue-router', () => ({ useRouter: () => api, useRoute: () => ({ query: api.query }) }));
vi.mock('@vue/apollo-composable', () => ({ useApolloClient: () => ({ client: api }) }));

const options = { global: { renderStubDefaultSlot: true, stubs: { RouterLink: true } } };
beforeEach(() => { setLanguage('en'); api.isAuthenticated = false; api.query = {}; api.login.mockReset(); api.register.mockReset(); api.mutate.mockReset(); });

describe('UI benchmark: account forms', () => {
  it('shows an accessible required-fields error without a request', async () => {
    const wrapper = shallowMount(Login, options);
    await wrapper.findAll('ion-button-stub').find(b => b.text() === 'Login')!.trigger('click');
    expect(wrapper.get('[role="alert"]').text()).toBe('Please fill in all required fields.');
    expect(api.login).not.toHaveBeenCalled();
  });
  it('toggles password visibility and its accessible name', async () => {
    const wrapper = shallowMount(Login, options);
    expect(wrapper.findAllComponents(IonInput)[1].props('type')).toBe('password');
    await wrapper.get('[aria-label="Show password"]').trigger('click');
    expect(wrapper.findAllComponents(IonInput)[1].props('type')).toBe('text');
    expect(wrapper.find('[aria-label="Hide password"]').exists()).toBe(true);
  });
  it('blocks duplicate login requests while pending and recovers after a network error', async () => {
    let reject!: (err: unknown) => void;
    api.login.mockReturnValue(new Promise((_, rejectPromise) => { reject = rejectPromise; }));
    const wrapper = shallowMount(Login, options);
    const inputs = wrapper.findAllComponents(IonInput);
    inputs[0].vm.$emit('update:modelValue', 'traveler'); inputs[1].vm.$emit('update:modelValue', 'invalid');
    const submit = wrapper.findAll('ion-button-stub').find(b => b.text() === 'Login')!;
    await submit.trigger('click'); await submit.trigger('click');
    expect(api.login).toHaveBeenCalledOnce(); expect(wrapper.findAllComponents(IonButton).find(b => b.text() === 'Working...')!.props('disabled')).toBe(true);
    reject({ networkError: new Error('offline') }); await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('Check your connection');
    expect(wrapper.findAllComponents(IonButton).find(b => b.text() === 'Login')!.props('disabled')).toBe(false);
  });
  it('submits trimmed valid registration values and navigates only after success', async () => {
    api.register.mockResolvedValue(undefined);
    const wrapper = shallowMount(Register, options);
    const values = [' traveler ', ' +251900000001 ', ' traveler@example.com ', 'Strong-Pass123!', 'Strong-Pass123!'];
    wrapper.findAllComponents(IonInput).forEach((input, i) => input.vm.$emit('update:modelValue', values[i]));
    await wrapper.get('form').trigger('submit'); await flushPromises();
    expect(api.register).toHaveBeenCalledWith('traveler', '+251900000001', 'Strong-Pass123!', 'Strong-Pass123!', 'traveler@example.com');
    expect(api.replace).toHaveBeenCalledWith('/profile');
  });
  it('generated registration passwords fill both fields and satisfy policy', async () => {
    const wrapper = shallowMount(Register, options);
    await wrapper.findAll('ion-button-stub').find(b => b.text() === 'Suggest a strong password')!.trigger('click');
    const inputs = wrapper.findAllComponents(IonInput);
    expect(inputs[3].props('modelValue')).toHaveLength(20);
    expect(inputs[4].props('modelValue')).toBe(inputs[3].props('modelValue'));
  });
  it('shows password recovery confirmation without exposing account existence', async () => {
    api.mutate.mockResolvedValue({ data: { requestPasswordReset: { success: true } } });
    const wrapper = shallowMount(ResetPassword, options);
    wrapper.getComponent(IonInput).vm.$emit('update:modelValue', ' missing@example.com ');
    await wrapper.get('form').trigger('submit'); await flushPromises();
    expect(api.mutate.mock.calls[0][0].variables).toEqual({ email: 'missing@example.com' });
    expect(wrapper.get('[role="status"]').text()).toContain('If an account matches');
  });
  it('rejects reset password mismatch before contacting the backend', async () => {
    api.query = { uid: 'uid', token: 'ticket' };
    const wrapper = shallowMount(ResetPassword, options);
    wrapper.findAllComponents(IonInput)[0].vm.$emit('update:modelValue', 'Strong-Pass123!');
    wrapper.findAllComponents(IonInput)[1].vm.$emit('update:modelValue', 'different');
    await wrapper.get('form').trigger('submit');
    expect(wrapper.get('[role="alert"]').text()).toBe('Passwords do not match.');
    expect(api.mutate).not.toHaveBeenCalled();
  });
});
