/// <reference types="cypress" />

type MockUser = {
  id: string;
  username: string;
  email: string;
  phoneNumber: string;
  bio: string;
  profilePicture: string;
};

type MockNotification = {
  id: string;
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
  type: string;
};

type MockSupportTicket = {
  id: string;
  subject: string;
  message: string;
  status: string;
  createdAt: string;
  contract?: {
    id: string;
    jobPost: {
      id: string;
      title: string;
    };
  } | null;
};

type MockEscrowPayment = {
  id: string;
  status: string;
  paymentMethod: string;
  amount: number;
  receiptUrl: string;
  verificationNote: string;
};

type MockContract = {
  id: string;
  status: string;
  preferredPaymentMethod?: string;
  preferredChapaBank?: string | null;
  poster: MockUser;
  acceptor: MockUser;
  jobPost: {
    id: string;
    title: string;
  };
  escrowPayments: MockEscrowPayment[];
};

type MockJob = {
  id: string;
  title: string;
  description: string;
  origin: string;
  destination: string;
  price: number;
  postType: string;
  expiresAt: string;
  productImage?: string;
  user: MockUser;
  contracts: MockContract[];
};

type MockState = {
  currentUser: MockUser;
  authToken: string;
  jobs: MockJob[];
  notifications: MockNotification[];
  supportTickets: MockSupportTicket[];
  transactionSummary: {
    totalPaid: number;
    totalReceived: number;
    totalTransacted: number;
  };
  counters: {
    user: number;
    job: number;
    contract: number;
    ticket: number;
    notification: number;
    escrow: number;
  };
};

const TELEBIRR_RECEIPT_PREFIX = 'https://transactioninfo.ethiotelecom.et/receipt/';
const USER_RECEIPT_URL = 'https://transactioninfo.ethiotelecom.et/receipt/DDJ41R74V4';

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const createUser = (
  id: string,
  username: string,
  email: string,
  phoneNumber: string,
  bio: string,
  profilePicture: string,
): MockUser => ({
  id,
  username,
  email,
  phoneNumber,
  bio,
  profilePicture,
});

const createState = (): MockState => {
  const alice = createUser('1', 'alice', 'alice@example.com', '+251900000001', 'Primary tester', '');
  const bob = createUser('2', 'bob', 'bob@example.com', '+251900000002', 'Courier partner', '');
  const clara = createUser('3', 'clara', 'clara@example.com', '+251900000003', 'Support contact', '');

  return {
    currentUser: clone(alice),
    authToken: 'token-alice',
    jobs: [
      {
        id: 'job-1',
        title: 'Owner approval needed',
        description: 'A posted job with a pending applicant to accept or reject.',
        origin: 'Addis Ababa',
        destination: 'Bahir Dar',
        price: 1200,
        postType: 'Delivery',
        expiresAt: '2026-04-30T12:00:00.000Z',
        productImage: '',
        user: clone(alice),
        contracts: [
          {
            id: 'contract-1',
            status: 'PENDING',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(alice),
            acceptor: clone(bob),
            jobPost: { id: 'job-1', title: 'Owner approval needed' },
            escrowPayments: [],
          },
        ],
      },
      {
        id: 'job-6',
        title: 'Draft post ready for delete',
        description: 'A post that should be removed from the list.',
        origin: 'Adama',
        destination: 'Nazret',
        price: 700,
        postType: 'Transport',
        expiresAt: '2026-04-29T12:00:00.000Z',
        productImage: '',
        user: clone(alice),
        contracts: [],
      },
      {
        id: 'job-7',
        title: 'Owner reject branch',
        description: 'A second posted job so we can test rejection too.',
        origin: 'Hawassa',
        destination: 'Mekelle',
        price: 950,
        postType: 'Delivery',
        expiresAt: '2026-04-28T12:00:00.000Z',
        productImage: '',
        user: clone(alice),
        contracts: [
          {
            id: 'contract-7',
            status: 'PENDING',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(alice),
            acceptor: clone(clara),
            jobPost: { id: 'job-7', title: 'Owner reject branch' },
            escrowPayments: [],
          },
        ],
      },
      {
        id: 'job-2',
        title: 'Telebirr escrow run',
        description: 'Accepted job waiting for escrow funding.',
        origin: 'Addis Ababa',
        destination: 'Dire Dawa',
        price: 1800,
        postType: 'Transport',
        expiresAt: '2026-04-27T12:00:00.000Z',
        productImage: '',
        user: clone(bob),
        contracts: [
          {
            id: 'contract-2',
            status: 'ACCEPTED',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(bob),
            acceptor: clone(alice),
            jobPost: { id: 'job-2', title: 'Telebirr escrow run' },
            escrowPayments: [],
          },
        ],
      },
      {
        id: 'job-8',
        title: 'Poster escrow target',
        description: 'Stable escrow target where current user is the poster.',
        origin: 'Addis Ababa',
        destination: 'Dessie',
        price: 30,
        postType: 'Delivery',
        expiresAt: '2026-04-27T12:00:00.000Z',
        productImage: '',
        user: clone(alice),
        contracts: [
          {
            id: 'contract-8',
            status: 'ACCEPTED',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(alice),
            acceptor: clone(bob),
            jobPost: { id: 'job-8', title: 'Poster escrow target' },
            escrowPayments: [],
          },
        ],
      },
      {
        id: 'job-3',
        title: 'Pending cancellation run',
        description: 'A pending application the acceptor can cancel.',
        origin: 'Gondar',
        destination: 'Jimma',
        price: 1100,
        postType: 'Delivery',
        expiresAt: '2026-04-26T12:00:00.000Z',
        productImage: '',
        user: clone(bob),
        contracts: [
          {
            id: 'contract-3',
            status: 'PENDING',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(bob),
            acceptor: clone(alice),
            jobPost: { id: 'job-3', title: 'Pending cancellation run' },
            escrowPayments: [],
          },
        ],
      },
      {
        id: 'job-4',
        title: 'Completed delivery run',
        description: 'A completed job for history coverage.',
        origin: 'Mekelle',
        destination: 'Addis Ababa',
        price: 2400,
        postType: 'Delivery',
        expiresAt: '2026-04-25T12:00:00.000Z',
        productImage: '',
        user: clone(bob),
        contracts: [
          {
            id: 'contract-4',
            status: 'COMPLETED',
            preferredPaymentMethod: 'TELEBIRR',
            preferredChapaBank: null,
            poster: clone(bob),
            acceptor: clone(alice),
            jobPost: { id: 'job-4', title: 'Completed delivery run' },
            escrowPayments: [
              {
                id: 'escrow-4',
                status: 'RELEASED',
                paymentMethod: 'TELEBIRR',
                amount: 2400,
                receiptUrl: `${TELEBIRR_RECEIPT_PREFIX}completed-4`,
                verificationNote: 'Released successfully',
              },
            ],
          },
        ],
      },
      {
        id: 'job-5',
        title: 'Open job for application',
        description: 'Used to exercise the frontend apply/cancel flow.',
        origin: 'Awassa',
        destination: 'Shashamane',
        price: 1000,
        postType: 'Delivery',
        expiresAt: '2026-04-24T12:00:00.000Z',
        productImage: '',
        user: clone(clara),
        contracts: [],
      },
    ],
    notifications: [
      {
        id: 'notif-1',
        title: 'Application accepted',
        message: 'A job owner accepted your application.',
        isRead: false,
        createdAt: '2026-04-20T08:00:00.000Z',
        type: 'JOB_UPDATE',
      },
      {
        id: 'notif-2',
        title: 'Escrow reminder',
        message: 'Please fund escrow before work starts.',
        isRead: true,
        createdAt: '2026-04-20T09:00:00.000Z',
        type: 'PAYMENT',
      },
    ],
    supportTickets: [
      {
        id: 'ticket-1',
        subject: 'Receipt parsing help',
        message: 'I need support for a receipt link.',
        status: 'OPEN',
        createdAt: '2026-04-20T10:00:00.000Z',
        contract: {
          id: 'contract-2',
          jobPost: { id: 'job-2', title: 'Telebirr escrow run' },
        },
      },
    ],
    transactionSummary: {
      totalPaid: 4200,
      totalReceived: 2400,
      totalTransacted: 6600,
    },
    counters: {
      user: 4,
      job: 8,
      contract: 8,
      ticket: 2,
      notification: 3,
      escrow: 5,
    },
  };
};

const reply = (req: any, data: Record<string, unknown>) => {
  req.reply({
    statusCode: 200,
    body: { data },
  });
};

const operationNameFrom = (req: any) => {
  const body = req.body as { operationName?: string; query?: string };
  if (body.operationName) {
    return body.operationName;
  }

  const query = body.query || '';
  const match = query.match(/(?:mutation|query)\s+([A-Za-z0-9_]+)/);
  return match?.[1] || '';
};

const jobResponse = (state: MockState) => ({
  availableJobs: clone(state.jobs),
  myJobs: clone(state.jobs),
  allJobs: clone(state.jobs),
});

const currentUserResponse = (state: MockState) => ({
  userById: clone(state.currentUser),
  myTransactionSummary: clone(state.transactionSummary),
});

const mutateJob = (state: MockState, jobId: string) => {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) {
    throw new Error(`Job not found: ${jobId}`);
  }
  return job;
};

const mutateContract = (state: MockState, contractId: string) => {
  const job = state.jobs.find((item) => item.contracts.some((contract) => contract.id === contractId));
  const contract = job?.contracts.find((item) => item.id === contractId);

  if (!job || !contract) {
    throw new Error(`Contract not found: ${contractId}`);
  }

  return { job, contract };
};

const interceptGraphQL = (state: MockState) => {
  cy.intercept('POST', '**/graphql*', (req) => {
    const operationName = operationNameFrom(req);
    req.alias = operationName;
    const variables = (req.body as { variables?: Record<string, unknown> }).variables || {};

    switch (operationName) {
      case 'RegisterUser': {
        const username = String(variables.username || 'new-user');
        const phoneNumber = String(variables.phoneNumber || '+251900000099');
        state.currentUser = createUser(String(state.counters.user++), username, `${username}@example.com`, phoneNumber, 'Registered from Cypress', '');
        state.authToken = `token-${username}`;
        reply(req, {
          RegisterUser: {
            token: state.authToken,
            user: clone(state.currentUser),
          },
        });
        return;
      }

      case 'Login': {
        state.authToken = `token-${state.currentUser.username}`;
        reply(req, {
          tokenAuth: {
            token: state.authToken,
            payload: {},
            user: clone(state.currentUser),
          },
        });
        return;
      }

      case 'JOB_QUERY':
      case 'JOB_QUERY_AUTHENTICATED': {
        reply(req, jobResponse(state));
        return;
      }

      case 'GetCurrentUser': {
        reply(req, currentUserResponse(state));
        return;
      }

      case 'MyNotifications':
      case 'MyNotificationsForBadge': {
        reply(req, { myNotifications: clone(state.notifications) });
        return;
      }

      case 'MySupportTickets': {
        reply(req, { mySupportTickets: clone(state.supportTickets) });
        return;
      }

      case 'MyActiveContractsForSupport': {
        reply(req, { allJobs: clone(state.jobs) });
        return;
      }

      case 'createJobPost': {
        const newJob: MockJob = {
          id: `job-${state.counters.job++}`,
          title: String(variables.title),
          description: String(variables.description),
          origin: String(variables.origin),
          destination: String(variables.destination),
          price: Number(variables.price || 0),
          postType: String(variables.postType),
          expiresAt: String(variables.expiresAt),
          productImage: String(variables.productImage || ''),
          user: clone(state.currentUser),
          contracts: [],
        };
        state.jobs.unshift(newJob);
        reply(req, {
          createJobPost: {
            jobPost: clone(newJob),
          },
        });
        return;
      }

      case 'acceptJobPost': {
        const job = mutateJob(state, String(variables.jobPostId));
        const contract: MockContract = {
          id: `contract-${state.counters.contract++}`,
          status: String(variables.status || 'PENDING'),
          preferredPaymentMethod: String(variables.preferredPaymentMethod || 'TELEBIRR'),
          preferredChapaBank: variables.preferredChapaBank ? String(variables.preferredChapaBank) : null,
          poster: clone(job.user),
          acceptor: clone(state.currentUser),
          jobPost: { id: job.id, title: job.title },
          escrowPayments: [],
        };
        job.contracts.push(contract);
        reply(req, {
          acceptJobPost: {
            contract: clone(contract),
          },
        });
        return;
      }

      case 'confirmJobContract': {
        const { contract } = mutateContract(state, String(variables.contractId));
        contract.status = 'ACCEPTED';
        reply(req, {
          confirmJobContract: { success: true },
        });
        return;
      }

      case 'rejectJobApplication': {
        const { job } = mutateContract(state, String(variables.contractId));
        job.contracts = job.contracts.filter((contract) => contract.id !== String(variables.contractId));
        reply(req, {
          rejectJobApplication: { success: true },
        });
        return;
      }

      case 'deleteJobPost': {
        const jobId = String(variables.jobPostId);
        state.jobs = state.jobs.filter((job) => job.id !== jobId);
        reply(req, {
          deleteJobPost: { success: true },
        });
        return;
      }

      case 'InitiateEscrowPayment': {
        const receiptUrl = String(variables.receiptUrl || '');
        const { job, contract } = mutateContract(state, String(variables.contractId));
        contract.escrowPayments = [
          {
            id: `escrow-${state.counters.escrow++}`,
            status: 'PAID',
            paymentMethod: 'TELEBIRR',
            amount: job.price,
            receiptUrl,
            verificationNote: 'Verified via Cypress frontend test',
          },
        ];
        reply(req, {
          initiateEscrowPayment: {
            verified: true,
            message: 'Receipt verified and escrow funded.',
            payment: clone(contract.escrowPayments[0]),
          },
        });
        return;
      }

      case 'confirmJobCompleted': {
        const { job, contract } = mutateContract(state, String(variables.contractId));
        const currentUserIsPoster = String(job.user.id) === String(state.currentUser.id);

        if (contract.status === 'ACCEPTED') {
          contract.status = currentUserIsPoster ? 'COMPLETED_BY_POSTER' : 'COMPLETED_BY_ACCEPTOR';
        } else if (contract.status === 'COMPLETED_BY_POSTER' || contract.status === 'COMPLETED_BY_ACCEPTOR') {
          contract.status = 'COMPLETED';
        } else {
          contract.status = 'COMPLETED';
        }

        reply(req, {
          confirmJobCompleted: { success: true },
        });
        return;
      }

      case 'CreateComplaint': {
        reply(req, {
          createComplaint: {
            complaint: {
              id: `complaint-${Date.now()}`,
            },
          },
        });
        return;
      }

      case 'EditProfile': {
        state.currentUser = {
          ...state.currentUser,
          email: String(variables.email || state.currentUser.email),
          phoneNumber: String(variables.phoneNumber || state.currentUser.phoneNumber),
          bio: String(variables.bio || state.currentUser.bio),
          profilePicture: String(variables.profilePicture || state.currentUser.profilePicture),
        };
        reply(req, {
          editProfile: {
            user: clone(state.currentUser),
          },
        });
        return;
      }

      case 'MarkNotificationRead': {
        const notification = state.notifications.find((item) => item.id === String(variables.notificationId));
        if (notification) {
          notification.isRead = true;
        }
        reply(req, {
          markNotificationRead: {
            notification: notification ? clone(notification) : null,
          },
        });
        return;
      }

      case 'CreateSupportTicket': {
        const contractId = variables.contractId ? String(variables.contractId) : null;
        const related = contractId ? state.jobs.find((job) => job.contracts.some((contract) => contract.id === contractId)) : undefined;
        const contract = contractId && related
          ? {
              id: contractId,
              jobPost: {
                id: related.id,
                title: related.title,
              },
            }
          : null;

        state.supportTickets.unshift({
          id: `ticket-${state.counters.ticket++}`,
          subject: String(variables.subject || ''),
          message: String(variables.message || ''),
          status: 'OPEN',
          createdAt: new Date().toISOString(),
          contract,
        });

        reply(req, {
          createSupportTicket: {
            ticket: clone(state.supportTickets[0]),
          },
        });
        return;
      }

      default: {
        throw new Error(`Unhandled GraphQL operation: ${operationName}`);
      }
    }
  });
};

const visitApp = (path: string, authenticated = true) => {
  cy.visit(`/index.html${path}`, {
    onBeforeLoad(win) {
      win.localStorage.setItem('onboardingCompleted', 'true');
      win.localStorage.setItem('app_language', 'en');
      if (authenticated) {
        win.localStorage.setItem('authToken', 'token-alice');
        win.localStorage.setItem('user', JSON.stringify(createState().currentUser));
      } else {
        win.localStorage.removeItem('authToken');
        win.localStorage.removeItem('user');
      }
    },
  });
};

const setIonValue = ($element: JQuery<HTMLElement>, value: string) => {
  const element = $element[0] as any;
  element.value = value;
  element.dispatchEvent(new CustomEvent('ionInput', {
    detail: { value },
    bubbles: true,
    composed: true,
  }));
  element.dispatchEvent(new CustomEvent('ionChange', {
    detail: { value },
    bubbles: true,
    composed: true,
  }));
};

const fillInputInItem = (label: string, value: string) => {
  cy.contains('ion-item', label).find('ion-input').first().then(($elements) => {
    setIonValue($elements as JQuery<HTMLElement>, value);
  });
};

const fillTextareaInItem = (label: string, value: string) => {
  cy.contains('ion-item', label).find('ion-textarea').first().then(($elements) => {
    setIonValue($elements as JQuery<HTMLElement>, value);
  });
};

describe('Frontend CRUD and transaction journey', () => {
  let state: MockState;

  beforeEach(() => {
    cy.on('uncaught:exception', (err) => {
      if (err.message.includes("Cannot read properties of undefined (reading 'classList')")) {
        return false;
      }
      return true;
    });

    state = createState();
    interceptGraphQL(state);
  });

  it('covers register, login, and apply/cancel from the home feed', () => {
    visitApp('#/signup', false);

    fillInputInItem('Username', 'newtraveler');
    fillInputInItem('Phone Number', '+251900000099');
    fillInputInItem('Password', 'secret123');
    fillInputInItem('Confirm Password', 'secret123');
    cy.contains('ion-button', 'Sign Up').click();

    cy.wait('@RegisterUser').its('request.body.variables').should((variables) => {
      expect(variables.username).to.eq('newtraveler');
      expect(variables.phoneNumber).to.eq('+251900000099');
    });
    cy.hash().should('include', '/profile');

    cy.visit('/index.html#/home');
    cy.contains('Welcome to Guzo Jobs').should('be.visible');

    cy.contains('ion-card', 'Open job for application').within(() => {
      cy.contains('ion-button', 'Accept Job').click();
    });

    cy.wait('@acceptJobPost').its('request.body.variables').should((variables) => {
      expect(variables.status).to.eq('PENDING');
      expect(variables.preferredPaymentMethod).to.eq('TELEBIRR');
    });

    cy.contains('ion-card', 'Open job for application').within(() => {
      cy.contains('ion-button', 'Cancel Request').scrollIntoView().click({ force: true });
    });

    cy.wait('@rejectJobApplication');

    visitApp('#/login', false);
    fillInputInItem('Username', 'alice');
    fillInputInItem('Password', 'password123');
    cy.contains('ion-button', 'Login').click();

    cy.wait('@Login');
    cy.hash().should('include', '/home');
    cy.contains('Welcome to Guzo Jobs').should('be.visible');
  });

  it('covers create, accept, reject, escrow, completion, complaint, and delete', () => {
    visitApp('#/postJob', true);

    fillInputInItem('የሥራ ርዕስ', 'Cypress created job');
    fillInputInItem('From (Origin)', 'Addis Ababa');
    fillInputInItem('To (Destination)', 'Hawassa');
    fillTextareaInItem('Description', 'Created from the frontend test script.');
    fillInputInItem('Price', '30');
    cy.contains('ion-button', 'Post Job').click();

    cy.wait('@createJobPost').its('request.body.variables').should((variables) => {
      expect(variables.title).to.eq('Cypress created job');
      expect(variables.price).to.eq(30);
    });
    cy.hash().should('include', '/home');
    cy.contains('Cypress created job').should('be.visible');

    visitApp('#/myJobs', true);

    cy.contains('ion-segment-button', 'Pending').click();
    cy.contains('ion-card', 'Owner approval needed').within(() => {
      cy.contains('ion-button', 'Accept').click();
    });

    cy.wait('@confirmJobContract');

    cy.contains('ion-segment-button', 'Posted').click();

    cy.contains('ion-button', 'Delete Post').first().click();

    cy.wait('@deleteJobPost');

    cy.contains('ion-segment-button', 'Accepted').click();
    cy.contains('ion-card', 'Poster escrow target').within(() => {
      cy.contains('ion-button', 'Verify Telebirr Receipt and Fund Escrow').should('exist');
      cy.get('ion-input').first().then(($elements) => {
        setIonValue($elements as JQuery<HTMLElement>, USER_RECEIPT_URL);
      });
      cy.contains('ion-button', 'Verify Telebirr Receipt and Fund Escrow').click();
    });

    cy.wait('@InitiateEscrowPayment').its('request.body.variables').should((variables) => {
      expect(variables.receiptUrl).to.eq(USER_RECEIPT_URL);
    });

    cy.contains('ion-card', 'Poster escrow target').within(() => {
      cy.contains('Escrow funded. Waiting for').should('be.visible');
      cy.contains('ion-button', 'Mark as Completed').click();
    });

    cy.wait('@confirmJobCompleted');

    cy.contains('ion-card', 'Poster escrow target').within(() => {
      cy.contains('ion-button', 'Raise Complaint').click();
    });

    cy.wait('@CreateComplaint');

    cy.contains('ion-segment-button', 'Pending').click();
    cy.contains('ion-card', 'Pending cancellation run').within(() => {
      cy.contains('ion-button', 'Cancel Application').click();
    });

    cy.wait('@rejectJobApplication');

    cy.contains('ion-segment-button', 'Completed').click();
    cy.contains('Completed delivery run').should('be.visible');
  });

  it('covers profile editing, language switching, notifications, support, and logout', () => {
    visitApp('#/profile', true);

    cy.get('ion-toolbar ion-button').first().click();
    fillInputInItem('Email', 'updated@example.com');
    fillInputInItem('Phone Number', '+251911111111');
    fillTextareaInItem('Bio', 'Updated from the Cypress frontend test.');
    fillInputInItem('Profile Picture URL', 'https://example.com/avatar.jpg');
    cy.contains('ion-button', 'Switch to Amharic').click();
    cy.contains('ion-button', 'ወደ እንግሊዝኛ ቀይር').should('be.visible');
    cy.contains('ion-button', 'Save Changes').scrollIntoView().click({ force: true });

    cy.wait('@EditProfile').its('request.body.variables').should((variables) => {
      expect(variables.email).to.eq('updated@example.com');
      expect(variables.phoneNumber).to.eq('+251911111111');
      expect(variables.bio).to.eq('Updated from the Cypress frontend test.');
      expect(variables.profilePicture).to.eq('https://example.com/avatar.jpg');
    });

    cy.hash().should('include', '/home');

    visitApp('#/notifications', true);
    cy.contains('ion-button', 'Mark read').first().click();
    cy.wait('@MarkNotificationRead');
    cy.contains('Read').should('be.visible');

    visitApp('#/support', true);
    fillInputInItem('Subject', 'Receipt verification question');
    fillTextareaInItem('Message', 'The receipt link needs a quick manual review.');
    cy.contains('ion-button', 'Submit Ticket').click();

    cy.wait('@CreateSupportTicket').its('request.body.variables').should((variables) => {
      expect(variables.subject).to.eq('Receipt verification question');
      expect(variables.message).to.include('manual review');
    });

    cy.contains('Receipt verification question').should('be.visible');

    visitApp('#/logout', true);
    cy.contains('ion-button', 'Confirm Logout').click();
    cy.window().then((win) => {
      expect(win.localStorage.getItem('authToken')).to.eq(null);
      expect(win.localStorage.getItem('user')).to.eq(null);
    });
    cy.hash().should('include', '/home');
  });

  it('smoke checks the note page shell', () => {
    visitApp('#/add', true);

    cy.contains('h1', 'Add Note').should('be.visible');
    cy.get('ion-input').should('have.length.at.least', 1);
    cy.get('ion-input').first().then(($elements) => {
      setIonValue($elements as JQuery<HTMLElement>, 'Frontend smoke note');
    });
  });
});
