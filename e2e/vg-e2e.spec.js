const { test, expect } = require('@playwright/test');
const BASE = 'http://192.168.0.103:3003';
const API = 'http://192.168.0.103:8000';

test.describe('ValueGraph 前端 E2E 测试', () => {
  test.describe.configure({ timeout: 30000 });

  test('P0: 首页加载并显示核心元素', async ({ page }) => {
    const res = await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    expect(res.status()).toBe(200);
    // 验证标题
    const title = await page.title();
    expect(String(title)).toContain('ValueGraph');
    // 验证导航栏
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('价值推荐').first()).toBeVisible();
    await expect(page.getByText('财报分析').first()).toBeVisible();
    await expect(page.getByText('持股查询').first()).toBeVisible();
    // 验证 Hero 区
    await expect(page.getByText('聚焦高 ROE')).toBeVisible();
    // 验证市场切换按钮
    await expect(page.getByRole('button', { name: /A股/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /美股/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /港股/ })).toBeVisible();
    // 验证筛选器
    await expect(page.getByText('价值筛选器')).toBeVisible();
  });

  test('P0: 价值推荐 - 市场切换', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await page.getByRole('button', { name: /美股/ }).click();
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: /港股/ }).click();
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: /A股/ }).click();
    await page.waitForTimeout(2000);
  });

  test('P0: 价值推荐 - ROE/负债率筛选器', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    const roeSlider = page.getByLabel('ROE 下限');
    await roeSlider.fill('25');
    await page.waitForTimeout(1500);
    const debtSlider = page.getByLabel('负债率上限');
    await debtSlider.fill('30');
    await page.waitForTimeout(1500);
    await page.getByRole('button', { name: '重置' }).click();
    await page.waitForTimeout(1000);
  });

  test('P0: API 健康检查', async ({ request }) => {
    const res = await request.get(API + '/docs', { timeout: 10000 });
    expect(res.status()).toBe(200);
  });

  test('P1: 导航 - 财报分析', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '财报分析' }).first().click(),
    ]);
    expect(page.url()).toContain('/financial');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 导航 - 持股查询', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '持股查询' }).first().click(),
    ]);
    expect(page.url()).toContain('/shareholders');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 导航 - 每日早报', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '每日早报' }).first().click(),
    ]);
    expect(page.url()).toContain('/report');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 侧边栏 - 股票对比', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '股票对比' }).first().click(),
    ]);
    expect(page.url()).toContain('/compare');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 侧边栏 - 知识图谱', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '知识图谱' }).first().click(),
    ]);
    expect(page.url()).toContain('/graph');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 侧边栏 - 新闻', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '新闻' }).first().click(),
    ]);
    expect(page.url()).toContain('/news');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('P1: 侧边栏 - 智能问答', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.getByRole('link', { name: '智能问答' }).first().click(),
    ]);
    expect(page.url()).toContain('/qa');
    await expect(page.locator('h1, h2').first().first()).toBeVisible();
  });

  test('P1: 持股时间线', async ({ page }) => {
    await page.goto(BASE + '/shareholders/timeline', { waitUntil: 'networkidle', timeout: 20000 });
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });

  test('P2: 404 页面', async ({ page }) => {
    await page.goto(BASE + '/nonexistent-page-12345', { waitUntil: 'networkidle', timeout: 20000 });
    await expect(page.getByText('404')).toBeVisible({ timeout: 5000 });
  });

  test('P2: 移动端底部导航栏', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
    await expect(page.locator('nav.fixed.inset-x-4')).toBeVisible();
  });
});
