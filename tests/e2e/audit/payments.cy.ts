/// <reference types="cypress" />
const cbeReceipt = 'https://mbreciept.cbe.com.et/v2-SYNTHETIC12345';
const token = `eyJhbGciOiJIUzI1NiJ9.${btoa(JSON.stringify({ exp: 4102444800, username: 'poster' }))}.synthetic`;

function fundingPage(options: { configured?: boolean; success?: boolean; awaitingWorker?: boolean } = {}) {
  let paid = false;
  cy.intercept('POST', '**/graphql*', req => {
    const query = req.body.query || '';
    if (query.includes('escrowRecipients')) {
      req.reply({ data: { escrowRecipients: options.configured === false ? [] : [
        { provider: 'CBE', name: 'Test Escrow Account', accountNumber: '1000000001234', updatedAt: '2026-10-17T10:00:00Z' },
        { provider: 'TELEBIRR', name: 'Test Escrow Wallet', accountNumber: '251910001234', updatedAt: '2026-10-17T10:00:00Z' },
      ] } });
    } else if (query.includes('initiateEscrowPayment')) {
      expect(req.body.variables.receiptUrl).to.equal(cbeReceipt);
      paid = options.success !== false;
      req.reply({ data: { initiateEscrowPayment: { verified: paid,
        message: paid ? 'Receipt verified. Escrow is funded.' : 'The receipt recipient name does not match the escrow account.',
        payment: paid ? { id: '10', status: 'PAID', amount: 100 } : null } } });
    } else if (query.includes('myJobs')) {
      const jobs = [{ __typename: 'JobPostingType', id: '1', title: 'Payment test delivery', description: 'Synthetic delivery', origin: 'Addis', destination: 'Adama',
        price: 100, postType: 'DELIVERY', user: { __typename: 'UserType', id: '1', username: 'poster' }, contracts: [
          { __typename: 'ContractType', id: '2', agreedPrice: 100, status: options.awaitingWorker ? 'COMPLETED_BY_POSTER' : 'ACCEPTED', preferredPaymentMethod: 'TELEBIRR', acceptor: { __typename: 'UserType', id: '3', username: 'worker' },
            escrowPayments: paid || options.awaitingWorker ? [{ __typename: 'EscrowPaymentType', id: '10', status: 'PAID', amount: 100, paymentMethod: 'CBE' }] : [] },
        ] }];
      req.reply({ data: query.includes('jobs:') ? { jobs } : { myJobs: jobs } });
    } else req.reply({ data: { myNotifications: [] } });
  }).as('paymentsApi');
  cy.visit('/index.html#/myJobs', { onBeforeLoad(win) {
    win.localStorage.clear();
    win.localStorage.setItem('onboardingCompleted', 'true');
    win.localStorage.setItem('app_language', 'en');
    win.localStorage.setItem('authToken', token);
    win.localStorage.setItem('user', JSON.stringify(options.awaitingWorker ? { id: '3', username: 'worker' } : { id: '1', username: 'poster' }));
  } });
  cy.contains('ion-segment-button', 'Accepted').click();
}

it('shows database recipients and funds an unpaid contract after verified receipt submission', () => {
  cy.viewport(360, 800); fundingPage();
  cy.contains('Test Escrow Account').should('be.visible');
  cy.contains('Test Escrow Wallet').should('be.visible');
  cy.contains('100.00 ETB').should('be.visible');
  cy.get('section[aria-label="Fund escrow"] ion-input input').type(cbeReceipt);
  cy.screenshot('escrow-funding-mobile', { capture: 'fullPage' });
  cy.contains('ion-button', 'Verify payment').click();
  cy.contains('Escrow funded. Waiting').should('be.visible');
  cy.contains('ion-button', 'Mark as Completed').should('be.visible');
  cy.get('section[aria-label="Fund escrow"]').should('not.exist');
});

it('keeps escrow unfunded and shows a recipient mismatch', () => {
  fundingPage({ success: false });
  cy.get('section[aria-label="Fund escrow"] ion-input input').type(cbeReceipt);
  cy.contains('ion-button', 'Verify payment').click();
  cy.get('[role="alert"]').should('contain.text', 'recipient name does not match');
  cy.contains('ion-button', 'Mark as Completed').should('not.exist');
});

it('does not invent payment instructions when recipients are unconfigured', () => {
  fundingPage({ configured: false });
  cy.contains('Escrow accounts are not configured').should('be.visible');
  cy.contains('ion-button', 'Verify payment').should('not.exist');
});

it('keeps a funded job visible to the worker after the poster marks it complete', () => {
  fundingPage({ awaitingWorker: true });
  cy.contains('Payment test delivery').should('be.visible');
  cy.contains('ion-button', 'Confirm Completion').should('be.visible');
  cy.get('section[aria-label="Fund escrow"]').should('not.exist');
});
