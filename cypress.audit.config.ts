import { defineConfig } from 'cypress';
import { mkdirSync, writeFileSync } from 'node:fs';

export default defineConfig({
  video: false,
  screenshotOnRunFailure: true,
  screenshotsFolder: 'docs/audit/results/screenshots',
  e2e: {
    baseUrl: 'http://127.0.0.1:4175',
    specPattern: 'tests/e2e/audit/**/*.cy.ts',
    supportFile: false,
    setupNodeEvents(on) {
      on('after:run', results => {
        mkdirSync('docs/audit/results', { recursive: true });
        writeFileSync('docs/audit/results/browser.json', JSON.stringify(results, null, 2));
      });
    },
  },
});
