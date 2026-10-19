export interface EscrowContract {
  escrowPayments?: Array<{ status: string; amount?: number }>;
}

export function hasPaidEscrow(contract?: EscrowContract) {
  return contract?.escrowPayments?.some(payment => ['PAID', 'RELEASED'].includes(payment.status)) === true;
}
