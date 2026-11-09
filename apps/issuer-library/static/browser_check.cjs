'use strict';
// Real-browser check of a generated library page opened from disk (file://), every other request
// blocked. Prints one JSON report; tests/test_library_page_browser.py asserts on it.
// Usage: node browser_check.cjs <library/index.html> [screenshot.png]
const {chromium} = require('playwright');
const fs = require('fs');
const {pathToFileURL, fileURLToPath} = require('url');

(async () => {
  const [pagePath, shot] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const blocked = [], errors = [], dialogs = [];
  await context.route(/^(?!file:)/, route => {blocked.push(route.request().url()); route.abort();});
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
  page.on('dialog', dialog => {dialogs.push(dialog.message()); dialog.dismiss();});
  await page.goto(pathToFileURL(pagePath).href);
  const report = {blocked, errors, dialogs};
  report.rows = await page.locator('#run-rows tr').count();
  report.issuers = await page.locator('#issuer-nav .issuer-choice').allTextContents();
  report.scripts = await page.locator('script').count();
  report.emptyHeading = await page.locator('#empty-state:visible h2').allTextContents();
  const links = await page.$$eval('a[href]', anchors => anchors.map(a => a.href));
  report.missingLinks = links.filter(h => h.startsWith('file:')).map(h => fileURLToPath(h.split('#')[0]))
    .filter(p => !fs.existsSync(p));
  report.remoteLinks = links.filter(h => !h.startsWith('file:'));
  if (report.rows) {
    await page.locator('#run-rows .issuer-title').last().click();
    report.selected = await page.locator('#run-detail h2').textContent();
    report.bottomLines = await page.locator('#run-detail .bottom-line').allTextContents();
    await page.fill('#search', 'no run has this text');
    report.rowsAfterSearch = await page.locator('#run-rows tr').count();
    await page.click('#clear');
    await page.selectOption('#latest', 'latest');
    report.rowsLatest = await page.locator('#run-rows tr').count();
    await page.click('#clear');
    const [popup] = await Promise.all([page.waitForEvent('popup'), page.locator('.report-link').first().click()]);
    await popup.waitForLoadState();
    report.reportOpened = popup.url().startsWith('file:') && (await popup.content()).length > 0;
  }
  if (shot) await page.screenshot({path: shot, fullPage: true});
  console.log(JSON.stringify(report));
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});
