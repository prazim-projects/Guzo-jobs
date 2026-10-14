export function isStrongPassword(password: string): boolean {
  return password.length >= 12 && /[a-z]/.test(password) && /[A-Z]/.test(password)
    && /[0-9]/.test(password) && /[^A-Za-z0-9\s]/.test(password)
}

export function suggestPassword(): string {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*';
  let password = '';
  do {
    password = Array.from(crypto.getRandomValues(new Uint32Array(20)), n => alphabet[n % alphabet.length]).join('');
  } while (!isStrongPassword(password));
  return password;
}
