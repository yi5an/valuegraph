module.exports = {
  testDir: '.',
  timeout: 30000,
  use: {
    headless: true,
    screenshot: 'on',
    trace: 'on-first-retry',
  },
  retries: 0,
  reporter: 'list',
};
