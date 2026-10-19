import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { IonInput } from '@ionic/vue';
import EscrowFunding from '@/components/EscrowFunding.vue';
import { hasPaidEscrow } from '@/utils/payments';

const api = vi.hoisted(() => ({ query: vi.fn(), mutate: vi.fn() }));
vi.mock('@vue/apollo-composable', () => ({ useApolloClient: () => ({ client: api }) }));
const mount = () => shallowMount(EscrowFunding, { props: { contractId: '42', amount: 100 }, global: { renderStubDefaultSlot: true } });
const receipt = 'https://mbreciept.cbe.com.et/v2-SYNTHETIC12345';
beforeEach(() => {
  api.query.mockReset(); api.mutate.mockReset();
  api.query.mockResolvedValue({ data: { escrowRecipients: [{ provider: 'CBE', name: 'Configured Escrow', accountNumber: '1000000001234' }] } });
});

describe('Escrow funding UI', () => {
  it('does not treat missing or initiated payments as funded', () => {
    expect(hasPaidEscrow()).toBe(false);
    expect(hasPaidEscrow({})).toBe(false);
    expect(hasPaidEscrow({ escrowPayments: [{ status: 'INITIATED' }, { status: 'REFUNDED' }] })).toBe(false);
    expect(hasPaidEscrow({ escrowPayments: [{ status: 'PAID' }] })).toBe(true);
  });
  it('loads account instructions from the backend without fallback accounts', async () => {
    const wrapper = mount(); await flushPromises();
    expect(wrapper.text()).toContain('Configured Escrow');
    expect(wrapper.text()).toContain('1000000001234');
    expect(wrapper.text()).toContain('100.00 ETB');
    expect(api.query.mock.calls[0][0].fetchPolicy).toBe('network-only');
  });
  it('blocks funding when no active accounts are configured', async () => {
    api.query.mockResolvedValue({ data: { escrowRecipients: [] } });
    const wrapper = mount(); await flushPromises();
    expect(wrapper.text()).toContain('not configured');
    expect(wrapper.find('form').exists()).toBe(false);
  });
  it('rejects an unsafe link without a network request', async () => {
    const wrapper = mount(); await flushPromises();
    wrapper.getComponent(IonInput).vm.$emit('update:modelValue', 'https://evil.invalid/receipt/TEST123456');
    await wrapper.get('form').trigger('submit');
    expect(api.mutate).not.toHaveBeenCalled();
    expect(wrapper.get('[role="alert"]').text()).toContain('original HTTPS');
  });
  it('emits funded only after backend verification succeeds', async () => {
    const wrapper = mount(); await flushPromises();
    wrapper.getComponent(IonInput).vm.$emit('update:modelValue', receipt);
    api.mutate.mockResolvedValue({ data: { initiateEscrowPayment: { verified: false, message: 'Recipient does not match.' } } });
    await wrapper.get('form').trigger('submit'); await flushPromises();
    expect(wrapper.emitted('funded')).toBeUndefined();
    expect(wrapper.get('[role="alert"]').text()).toContain('Recipient does not match');
    api.mutate.mockResolvedValue({ data: { initiateEscrowPayment: { verified: true, message: 'Escrow funded.' } } });
    await wrapper.get('form').trigger('submit'); await flushPromises();
    expect(api.mutate.mock.calls[1][0].variables).toEqual({ contractId: '42', receiptUrl: receipt });
    expect(wrapper.emitted('funded')).toHaveLength(1);
  });
  it('prevents duplicate requests and advises retry after network failure', async () => {
    let reject!: (reason: Error) => void;
    api.mutate.mockReturnValue(new Promise((_, fail) => { reject = fail; }));
    const wrapper = mount(); await flushPromises();
    wrapper.getComponent(IonInput).vm.$emit('update:modelValue', receipt);
    await wrapper.get('form').trigger('submit'); await wrapper.get('form').trigger('submit');
    expect(api.mutate).toHaveBeenCalledOnce();
    reject(new Error('offline')); await flushPromises();
    expect(wrapper.text()).toContain('do not send another payment');
  });
});
