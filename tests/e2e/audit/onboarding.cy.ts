/// <reference types="cypress" />
function firstVisit(language = 'en') {
  cy.intercept('POST', '**/graphql*', { data: { availableJobs: [] } }).as('welcomeApi');
  cy.visit('/index.html', { onBeforeLoad(win) {
    win.localStorage.clear();
    win.localStorage.setItem('app_language', language);
  } });
  cy.contains('.slide-title', 'Welcome to Guzo Jobs').should('be.visible');
}

it('shows the welcome screen without starting the full application', () => {
  cy.viewport(360, 800); firstVisit();
  cy.window().then(win => {
    const requests = win.performance.getEntriesByType('resource').map(entry => entry.name);
    expect(requests.filter(url => /bootstrap|apollo|swiper|ionicons|@ionic_vue/.test(url))).to.deep.equal([]);
    expect(win.document.documentElement.scrollWidth).to.be.at.most(360);
  });
  cy.get('@welcomeApi.all').should('have.length', 0);
  cy.screenshot('lightweight-onboarding-mobile');
});

it('supports slides, back navigation and entering the application', () => {
  firstVisit();
  cy.contains('button', 'Next').click();
  cy.get('.slide').eq(1).should('not.have.attr', 'inert');
  cy.contains('button', 'Back').click();
  cy.get('.slide').eq(0).should('not.have.attr', 'inert');
  cy.get('button[aria-label^="Go to slide 5"]').click();
  cy.contains('button', 'Get Started').should('be.visible').click();
  cy.location('hash').should('equal', '#/home');
  cy.contains('No jobs available yet.').should('be.visible');
  cy.window().then(win => expect(win.localStorage.getItem('onboardingCompleted')).to.equal('true'));
  cy.reload();
  cy.location('hash').should('equal', '#/home');
});

it('keeps translated skip controls and password-reset deep links usable', () => {
  firstVisit('am');
  cy.contains('button', 'ዝለል').click();
  cy.location('hash').should('equal', '#/home');
  cy.visit('/index.html#/reset-password', { onBeforeLoad(win) { win.localStorage.clear(); } });
  cy.location('hash').should('equal', '#/reset-password');
  cy.get('.welcome').should('not.exist');
});
