# Guzo Jobs Mobile Runtime and Escrow Flow Report

Date: 2026-04-08
Project: travelNotes / guzo-jobs-back

## 1. Progress Summary

### Completed in this iteration
- Fixed frontend TypeScript build blockers in create job and profile screens.
- Switched Ionic routing to hash history for safer Capacitor mobile routing.
- Hardened Android network default to secure transport (`usesCleartextTraffic=false`).
- Updated Apollo client endpoint resolution:
  - Uses `VITE_GRAPHQL_ENDPOINT` in production.
  - Uses emulator/dev fallback only in development (`10.0.2.2`).
- Added backend domain models for:
  - Escrow payments
  - In-app notifications
  - Complaints
  - Support tickets
- Added backend GraphQL support for:
  - Escrow funding
  - Complaint creation
  - Support ticket creation
  - Notification read-state updates
  - User-specific notification/support/complaint queries
- Added frontend pages:
  - Notifications page
  - Support page
- Added tab routes for Notifications and Support.
- Updated job-acceptance UX:
  - Bottom-position acceptance notification anchored above tab bar.
  - Removed direct phone-number-first flow in accepted jobs.
  - Added escrow-first actions (Chapa/Telebirr) for job posters.
  - Added complaint action for both parties from accepted job flow.

### Additional fixes after review
- Applied migration `api.0014_escrow_notification_complaint_supportticket` to remove runtime error `no such table: api_notification`.
- Reduced authenticated bottom navigation to core actions only (Home, Jobs, Post, Me) to prevent mobile overflow/crowding.
- Added Profile quick-action entry points to Notifications, Support, Map, and Logout.
- Implemented hard refresh behavior for pull-to-refresh (Apollo store reset + network refetch).
- Added regular auto-refresh polling (30s) on Home and My Jobs.
- Added pulsing visual indicator on pending acceptance items.
- Added frontend ownership guards before attempting contract confirmation to reduce accidental non-owner confirm requests.
- Normalized user-id comparisons to avoid stale/mixed-type mismatch cases.
- Forced network-only query strategy on live job boards to remove stale pending cards after cancel/reject.
- Added unread badge indicator for Notifications in Profile quick actions.
- Added back buttons for pages reached from Profile quick actions (Notifications, Support, Map, Logout).
- Changed Home applied-state CTA from passive badge to active red `Cancel Request` button.
- Added support ticket one-to-one job-contract linking (dropdown on Support page).
- Applied migration `api.0015_supportticket_contract` for support-to-contract relation.
- Updated backend ownership checks to compare IDs, preventing false denials due to object equality edge cases.
- Added provider credential validation for escrow initiation by method (Chapa vs Telebirr).

### Remaining verification steps
- Run Django migrations and verify GraphQL schema introspection after migration.
- End-to-end acceptance flow test on physical Android device:
  1. Poster confirms applicant
  2. Poster deposits escrow
  3. Both mark completed
  4. Escrow release status confirmed
- Optionally add push notifications (FCM) if background/native notifications are required.

## 2. Why `10.0.2.2` Exists

`10.0.2.2` is a special alias used by the Android emulator.

- Emulator `localhost` points to the emulator itself.
- `10.0.2.2` points from emulator to your host machine loopback (`127.0.0.1`).
- It is useful for local backend testing only.

Production builds should not depend on `10.0.2.2`. They should use `VITE_GRAPHQL_ENDPOINT` with your real HTTPS backend URL.

## 3. Why Cleartext Was Discussed

Cleartext HTTP (`http://`) is often blocked by Android in release contexts.

- If backend is local HTTP during testing, enabling cleartext can help debugging.
- For production security, HTTPS is preferred and cleartext should stay disabled.

Current state in project:
- `AndroidManifest.xml` uses `android:usesCleartextTraffic="false"`.

## 4. Mobile + CORS/CSRF Reality

Even in Capacitor, the app runs a WebView for this frontend, so CORS rules still apply to browser requests.

Common origins used by Capacitor/web testing:
- `capacitor://localhost`
- `http://localhost`
- `http://localhost:8100`

If your production server handles requests in a way that bypasses browser CORS (for example native HTTP plugin), this can differ. For the current Apollo/browser GraphQL path, server CORS/CSRF config still matters.

## 5. Data Model Additions

Added in backend models:
- `EscrowPayment`
  - Fields: `contract`, `payer`, `amount`, `payment_method`, `tx_ref`, `status`, timestamps
  - Status: `INITIATED`, `PAID`, `RELEASED`, `REFUNDED`
  - Methods: `CHAPA`, `TELEBIRR`
- `Notification`
  - Fields: `recipient`, `actor`, `contract`, `type`, `title`, `message`, `is_read`, `created_at`
- `Complaint`
  - Fields: `contract`, `filed_by`, `against`, `reason`, `status`, timestamps
  - Status: `OPEN`, `UNDER_REVIEW`, `RESOLVED`, `REJECTED`
- `SupportTicket`
  - Fields: `user`, `subject`, `message`, `status`, timestamps
  - Status: `OPEN`, `IN_PROGRESS`, `RESOLVED`

Migration file added:
- `guzo-jobs-back/api/migrations/0014_escrow_notification_complaint_supportticket.py`

## 6. GraphQL Schema Reference (Queries/Mutations)

### Queries

#### `myNotifications`
Returns current user notifications.

Example:
```graphql
query MyNotifications {
  myNotifications {
    id
    type
    title
    message
    isRead
    createdAt
    contract { id }
  }
}
```

#### `myComplaints`
Returns complaints filed by current user.

```graphql
query MyComplaints {
  myComplaints {
    id
    reason
    status
    createdAt
    contract { id }
    against { id username }
  }
}
```

#### `mySupportTickets`
Returns support tickets created by current user.

```graphql
query MySupportTickets {
  mySupportTickets {
    id
    subject
    message
    status
    createdAt
  }
}
```

#### Existing queries still used
- `allJobs`
- `availableJobs`
- `userById`
- `jobsByContractStatus(status: String!)`

### Mutations

#### `initiateEscrowPayment`
Poster funds escrow after accepting applicant.

```graphql
mutation InitiateEscrowPayment($contractId: ID!, $paymentMethod: String!, $txRef: String!) {
  initiateEscrowPayment(contractId: $contractId, paymentMethod: $paymentMethod, txRef: $txRef) {
    payment {
      id
      paymentMethod
      status
      amount
    }
  }
}
```

#### `createComplaint`
Either party raises a complaint on a contract.

```graphql
mutation CreateComplaint($contractId: ID!, $reason: String!) {
  createComplaint(contractId: $contractId, reason: $reason) {
    complaint {
      id
      status
      reason
    }
  }
}
```

#### `createSupportTicket`
User creates a support ticket.

```graphql
mutation CreateSupportTicket($subject: String!, $message: String!) {
  createSupportTicket(subject: $subject, message: $message) {
    ticket {
      id
      status
    }
  }
}
```

#### `markNotificationRead`
Marks a notification as read.

```graphql
mutation MarkNotificationRead($notificationId: ID!) {
  markNotificationRead(notificationId: $notificationId) {
    notification {
      id
      isRead
    }
  }
}
```

#### Existing lifecycle mutations (still active)
- `acceptJobPost`
- `confirmJobContract`
- `confirmJobCompleted`
- `rejectJobApplication`

Completion rule update:
- `confirmJobCompleted` now enforces that escrow is `PAID` before completion flow can proceed.
- When both parties complete, escrow status is moved to `RELEASED`.

## 7. Frontend UX Changes

### Accepted-job flow (`myJobs`)
- No direct phone reveal as first action.
- Poster sees escrow funding actions (`CHAPA`, `TELEBIRR`).
- Acceptor sees waiting state until escrow is funded.
- Both sides can file complaint from accepted-job card.

### Bottom notification for acceptance
- Acceptance toast now appears at bottom and is anchored to tab bar id `main-tab-bar`, so it does not overlap tab navigation.

## 8. Deployment/Config Checklist

For production APK:
- Set `VITE_GRAPHQL_ENDPOINT` to HTTPS GraphQL URL before building web assets.
- Keep Android cleartext disabled unless explicitly debugging local HTTP.
- Ensure Django host/origin settings match actual app request origins.
- Run backend migration:
  - `python manage.py migrate`

## 10. Payment Credentials Setup (Chapa/Telebirr)

Escrow initiation now validates provider-specific credentials.

### Backend `.env` keys required for Chapa
- `CHAPA_PUBLIC_KEY`
- `CHAPA_SECRET_KEY`
- `CHAPA_RETURN_URL`
- `CHAPA_CALLBACK_URL`

### Backend `.env` keys required for Telebirr
- `TELEBIRR_APP_ID`
- `TELEBIRR_APP_KEY`
- `TELEBIRR_MERCHANT_ID`
- `TELEBIRR_NOTIFY_URL`

### Where to set them
- Copy `guzo-jobs-back/.env.example` to `guzo-jobs-back/.env`.

## 11. Telebirr-Only Escrow Verification (New)

The payment flow is now Telebirr-only and user-driven by receipt URL submission.

### What changed
- Removed Chapa usage from active escrow funding flow in app screens.
- Poster now sees platform Telebirr phone number in accepted jobs.
- Poster submits Telebirr receipt URL in this format:
  - `https://transactioninfo.ethiotelecom.et/receipt/<TX_REF>`
- Backend verifies receipt details before marking escrow as paid.

### Verification behavior
- Receipt URL domain is restricted to `transactioninfo.ethiotelecom.et/receipt/`.
- Backend fetches receipt content and parses key fields:
  - transaction reference (`DDJ...`)
  - credited party name
  - credited party account
  - transaction status
  - settled amount
  - payment date (when available)
- Verification checks:
  - status must be `Completed`
  - settled amount must be at least contract amount
  - credited party name must match configured platform receiver name
  - credited party account must match configured platform receiver phone (last digits check)
- If checks pass:
  - payment is marked `PAID`
  - `verifiedAt` and `verificationNote` are stored
- If checks fail:
  - payment remains `INITIATED`
  - failure reason is saved in `verificationNote`

### PDF handling note
- Current implementation uses receipt page parsing directly from the provided URL.
- No PDF file is persisted on disk by this flow.
- This satisfies the requirement to avoid unnecessary download/storage when a direct verification workaround exists.

### Required backend env vars for verification
- `TELEBIRR_RECEIVER_NAME`
- `TELEBIRR_RECEIVER_PHONE`

### Env source of truth
- Receiver name/phone and other Telebirr credentials are read from Django settings,
  which load from backend environment variables (`guzo-jobs-back/.env` in local setup).
- `InitiateEscrowPayment` now uses settings-backed values instead of direct process lookups to avoid runtime mismatch.

## 14. Query Minimization and Leakage Reduction

To reduce unnecessary data exposure and lower MITM impact surface:
- `myJobs` page now uses `myJobs` GraphQL query (server-side scoped to current user) instead of broad `allJobs`.
- Removed unused phone-number fields from job queries in `myJobs` and `HomePage`.
- Telebirr escrow mutation now accepts only receipt URL and returns verification status/message plus payment metadata required by UI.

## 15. File Responsibilities (Current)

Backend:
- `guzo-jobs-back/guzo_jobs_backend/settings.py`
  - Loads environment variables and exposes Telebirr config values.
- `guzo-jobs-back/api/utils.py`
  - Shared helpers, including Telebirr receipt parsing and verification logic.
- `guzo-jobs-back/api/mutation.py`
  - Business mutations (`acceptJobPost`, `confirmJobContract`, `initiateEscrowPayment`, etc.).
  - Telebirr receipt verification is triggered here.
- `guzo-jobs-back/api/query.py`
  - Read APIs (`myJobs`, `myTransactionSummary`, notifications/support/complaints).
- `guzo-jobs-back/api/models.py`
  - Domain models for jobs/contracts/escrow/notifications/support and verification fields.
- `guzo-jobs-back/api/types.py`
  - GraphQL output types and serialization fields.

Frontend:
- `src/views/HomePage.vue`
  - Public/authorized job feed and job application entry.
- `src/views/myJobs.vue`
  - Poster/acceptor lifecycle actions and Telebirr receipt submission.
- `src/views/ProfilePage.vue`
  - Profile editing, language switch UI, and platform transaction totals.
- `src/views/NotificationsPage.vue`, `src/views/SupportPage.vue`, `src/views/MapPage.vue`
  - Feature pages with pull-to-refresh + refresh notice toasts.
- `src/utils/i18n.ts`
  - App language state and EN/AM translation helper.

## 16. CORS Strategy for Mobile and Multiple Devices

Mobile devices do not need individual allowlist entries. The browser/webview origin is what matters.

Current approach in Django:
- `corsheaders` is enabled again.
- Allowed origins are expressed with safe regex patterns for:
  - `http://localhost`
  - `http://127.0.0.1`
  - `http://10.0.2.2`
  - LAN development hosts like `http://192.168.x.x`
  - Capacitor webview origins `capacitor://localhost` and `ionic://localhost`

Why this works:
- An Android/iPhone device running the app still sends requests from the webview origin, not from a unique device identity.
- That means you allow the app origin pattern once, not each physical phone.
- For production, keep the real deployed frontend origin in `CORS_ALLOWED_ORIGINS` and do not widen the regex beyond development patterns.

If you are testing on a phone browser against a machine running `vite dev`, add the machine’s LAN host in the dev URL, not the phone itself.

## 12. Refresh Notice and Language Switch

### Refresh behavior
- Pull-to-refresh is now enabled on major pages:
  - Home
  - My Jobs
  - Profile
  - Notifications
  - Support
  - Map
- On successful refresh, toast now includes notice:
  - "Pull down to refresh is available on every page."

### Amharic switch utility
- Added `src/utils/i18n.ts` with persistent app language toggle (`en` / `am`).
- Added language switch button on Profile quick actions.
- Refresh notice strings are translated through utility keys.

## 13. Platform Amounts on Profile

Added backend query:
- `myTransactionSummary`

Returns:
- `totalPaid`: amount user has paid into escrow (PAID/RELEASED)
- `totalReceived`: amount user has received when escrow is RELEASED
- `totalTransacted`: sum of paid and received totals

Profile page now displays these values in Birr.
- Fill in your real merchant credentials and callback/notify URLs.
- Restart backend server after changes.

### Credential validation behavior
- If poster selects `CHAPA` without required Chapa env keys, mutation fails with missing-key list.
- If poster selects `TELEBIRR` without required Telebirr env keys, mutation fails with missing-key list.

## 9. Files Changed (this iteration)

- `src/apollo-client.ts`
- `src/views/createJobPost.vue`
- `src/views/ProfilePage.vue`
- `src/views/HomePage.vue`
- `src/views/myJobs.vue`
- `src/views/NotificationsPage.vue`
- `src/views/SupportPage.vue`
- `src/router/index.ts`
- `src/components/bottomTabs.vue`
- `src/main.ts`
- `android/app/src/main/AndroidManifest.xml`
- `guzo-jobs-back/guzo_jobs_backend/settings.py`
- `guzo-jobs-back/api/models.py`
- `guzo-jobs-back/api/types.py`
- `guzo-jobs-back/api/query.py`
- `guzo-jobs-back/api/mutation.py`
- `guzo-jobs-back/api/admin.py`
- `guzo-jobs-back/api/migrations/0014_escrow_notification_complaint_supportticket.py`
