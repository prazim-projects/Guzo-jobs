# Account recovery

The frontend and backend must be deployed together: registration now requires
`confirmPassword`, and reset/deletion use new GraphQL mutations.

Configure the backend environment for email delivery:

```dotenv
PASSWORD_RESET_URL=https://your-app.example/#/reset-password
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.example
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=noreply@your-domain.example
```

For local testing, use `django.core.mail.backends.console.EmailBackend` to print
reset links to the backend terminal. Production requires a working mail server.
Existing users must add their recovery email in Edit Profile. New users can add
it when registering. Phone-only accounts need support to recover access; the
app does not currently have an SMS provider.

Reset links use Django's expiring, single-use password reset tokens. Account
deletion requires the current password and blocks unfinished contracts or held
escrow. Successful deletion clears the local login and Apollo cache.
