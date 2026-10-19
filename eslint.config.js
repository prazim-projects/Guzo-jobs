import pluginVue from 'eslint-plugin-vue';
import tseslint from 'typescript-eslint';
import vueParser from 'vue-eslint-parser';

export default [
  { ignores: ['dist/**', 'node_modules/**', '.tmp/**', '.test-deps/**', 'android/**', 'ios/**'] },
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  { files: ['src/**/*.vue'], languageOptions: { parser: vueParser, parserOptions: { parser: tseslint.parser } } },
  {
    files: ['src/**/*.{ts,vue}'],
    rules: {
      'vue/no-deprecated-slot-attribute': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
];
