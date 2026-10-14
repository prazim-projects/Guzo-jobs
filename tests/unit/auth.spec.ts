import { describe, expect, it, vi, beforeEach } from 'vitest';
import { shallowMount, flushPromises } from '@vue/test-utils';
import { IonInput } from '@ionic/vue';
import Register from '@/views/register.vue';
import Login from '@/views/login.vue';
import { isStrongPassword, suggestPassword } from '@/utils/password';
import { setLanguage, t } from '@/utils/i18n';

const auth = vi.hoisted(() => ({ register: vi.fn(), login: vi.fn(), isAuthenticated: false }));
vi.mock('@/stores/userStore', () => ({ useAuthStore: () => auth }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn() }) }));
beforeEach(() => { vi.clearAllMocks(); setLanguage('en'); });

describe('account forms', () => {
  it('blocks mismatched and weak registration passwords before sending a request', async () => {
    const wrapper = shallowMount(Register, { global: { renderStubDefaultSlot: true, stubs: { RouterLink: true } } });
    const inputs = wrapper.findAllComponents(IonInput);
    inputs[0].vm.$emit('update:modelValue', 'traveler');
    inputs[1].vm.$emit('update:modelValue', '+251900000001');
    inputs[3].vm.$emit('update:modelValue', 'Strong-Pass123!');
    inputs[4].vm.$emit('update:modelValue', 'different');
    await wrapper.find('form').trigger('submit');
    expect(wrapper.text()).toContain('Passwords do not match.');
    expect(auth.register).not.toHaveBeenCalled();
    inputs[3].vm.$emit('update:modelValue', 'weak');
    inputs[4].vm.$emit('update:modelValue', 'weak');
    await wrapper.find('form').trigger('submit');
    expect(wrapper.text()).toContain('Choose a strong');
    expect(auth.register).not.toHaveBeenCalled();
  });

  it('generates distinct strong passwords', () => {
    const passwords = Array.from({ length: 30 }, suggestPassword);
    expect(passwords.every(isStrongPassword)).toBe(true);
    expect(new Set(passwords).size).toBe(passwords.length);
  });

  it('shows incorrect password errors to the user', async () => {
    auth.login.mockRejectedValue(new Error('Please enter valid credentials'));
    const wrapper = shallowMount(Login, { global: { renderStubDefaultSlot: true, stubs: { RouterLink: true } } });
    const inputs = wrapper.findAllComponents(IonInput);
    inputs[0].vm.$emit('update:modelValue', 'traveler');
    inputs[1].vm.$emit('update:modelValue', 'incorrect');
    await wrapper.findAll('ion-button-stub').find(button => button.text() === 'Login')!.trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('Incorrect username or password.');
  });

  it('switches button labels in both directions', () => {
    setLanguage('am'); expect(t('Accept Job')).toBe('ሥራውን ተቀበል');
    setLanguage('en'); expect(t('Job Title')).toBe('Job Title');
  });
});
