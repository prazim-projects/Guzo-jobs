/// <reference types="cypress" />
// Mock the network boundary only: exercise real Ionic custom elements in Electron.
const openAuditPage = (route: string, user?: string) => {
  cy.visit(`/index.html#${route}`, { onBeforeLoad(win) {
    win.localStorage.clear();
    win.localStorage.setItem('app_language', 'en');
    win.localStorage.setItem('onboardingCompleted', 'true');
    if (user !== undefined) {
      win.localStorage.setItem('user', user);
      win.localStorage.setItem('authToken', 'audit-synthetic-token');
    }
  } });
};
const fillAuditInput = (index: number, value: string) => cy.get('ion-input').eq(index).find('input').clear().type(value);
const noHorizontalOverflow = () => cy.get('ion-content:visible').shadow().find('[part="scroll"]').then($scroll => {
  expect($scroll[0].scrollWidth).to.be.at.most($scroll[0].clientWidth + 1);
});

beforeEach(() => {
  cy.intercept('POST', '**/graphql*', req => {
    const query = req.body.query || '';
    if (query.includes('tokenAuth')) {
      req.reply({ errors: [{ message: 'invalid_credentials' }], data: { tokenAuth: null } });
    } else if (query.includes('RegisterUser')) {
      req.reply({ data: { RegisterUser: { token: 'audit-synthetic-token', user: { id: '1', username: 'traveler', phoneNumber: '+251900000001' } } } });
    } else {
      req.reply({ data: { availableJobs: [], allJobs: [], myJobs: [], myNotifications: [], mySupportTickets: [],
        userById: { id: '1', username: 'traveler', email: '', phoneNumber: '+251900000001', bio: '', profilePicture: '', faydaLinked: false },
        myTransactionSummary: { totalPaid: 0, totalReceived: 0, totalTransacted: 0 } } });
    }
  }).as('graphql');
});

it('allows browser zoom for users who need larger text', () => {
  openAuditPage('/login');
  cy.get('meta[name="viewport"]').invoke('attr', 'content').should('not.match', /user-scalable=no|maximum-scale=1(?:\.0)?(?:,|$)/);
});

for (const [width, height] of [[360, 800], [1440, 900]]) {
  it(`renders login and registration without horizontal overflow at ${width}px`, () => {
    cy.viewport(width, height); openAuditPage('/login');
    cy.contains('ion-card-title', 'Welcome Back!').should('be.visible');
    cy.get('ion-input').should('have.length', 2); noHorizontalOverflow();
    openAuditPage('/signup'); cy.get('h1').should('contain.text', 'Create an Account');
    cy.get('ion-input').should('have.length', 5); noHorizontalOverflow();
  });
}

it('redirects unauthenticated access to protected routes', () => {
  for (const route of ['/profile', '/myJobs', '/postJob', '/support', '/notifications']) {
    openAuditPage(route); cy.hash().should('eq', '#/login');
  }
});

it('announces invalid credentials and permits a retry', () => {
  openAuditPage('/login'); fillAuditInput(0, 'traveler'); fillAuditInput(1, 'Incorrect-password123!');
  cy.contains('ion-button', /^Login$/).click(); cy.wait('@graphql');
  cy.get('[role="alert"]').should('be.visible').and('contain.text', 'Incorrect username or password');
  cy.contains('ion-button', /^Login$/).should('not.have.attr', 'disabled');
});

it('shows a strong generated password and matching confirmation', () => {
  openAuditPage('/signup'); cy.contains('ion-button', 'Suggest a strong password').click();
  cy.get('ion-input').eq(3).find('input').invoke('val').then(password => {
    expect(password).to.have.length(20);
    cy.get('ion-input').eq(4).find('input').should('have.value', password);
  });
});

it('lets a keyboard user submit login by pressing Enter', () => {
  openAuditPage('/login'); fillAuditInput(0, 'traveler'); fillAuditInput(1, 'Incorrect-password123!');
  cy.get('ion-input').eq(1).find('input').type('{enter}');
  cy.get('[role="alert"]').should('contain.text', 'Incorrect username or password');
});

it('recovers from corrupted stored user data with a usable login screen', () => {
  openAuditPage('/profile', '{invalid-json');
  cy.contains('ion-card-title', 'Welcome Back!').should('be.visible');
});

it('gives the public feed an empty-state explanation', () => {
  openAuditPage('/home'); cy.wait('@graphql');
  cy.get('ion-content').invoke('text').should('match', /no (?:available )?jobs|nothing .*yet|check back/i);
});

it('reaches interactive login within a generous local 5-second navigation budget', () => {
  openAuditPage('/login'); cy.contains('ion-card-title', 'Welcome Back!').should('be.visible');
  cy.window().then(win => {
    const navigation = win.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    expect(navigation.domContentLoadedEventEnd).to.be.greaterThan(0).and.lessThan(5000);
    cy.writeFile('docs/audit/results/navigation.json', { domContentLoadedMs: navigation.domContentLoadedEventEnd,
      note: 'One warm local development-server navigation in Electron; not LCP/INP/CLS or a production-device benchmark.' });
  });
});
