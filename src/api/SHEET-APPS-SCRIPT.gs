/**
 * FOC27 survey, Sheet side.
 *
 * Setup, about five minutes:
 *  1. Create a Google Sheet. Rename the first tab to "Responses". A second
 *     tab named "Notify" is created automatically on the first signup.
 *  2. Extensions, Apps Script. Delete the sample code, paste this file in.
 *  3. Set TOKEN below to a long random string. Keep a copy.
 *  4. Deploy, New deployment, type Web app.
 *       Execute as: Me
 *       Who has access: Anyone
 *     Copy the /exec URL.
 *  5. In the Vercel project for flyovercon.ink, add:
 *       SHEETS_WEBHOOK_URL   = the /exec URL
 *       SHEETS_WEBHOOK_TOKEN = the same string as TOKEN
 *     Redeploy.
 *
 * Only the Vercel function ever calls this. The browser never sees the URL,
 * so "Anyone" access is gated by the token, not by obscurity alone.
 *
 * The header row builds itself from the first submission and grows as new
 * fields appear, so adding a question later does not break anything.
 *
 * This file is documentation and lives in the repo for reference. It runs
 * inside Google, not on Vercel. Editing it here changes nothing until you
 * paste the new version into the Apps Script editor and redeploy.
 */

var TOKEN = 'CHANGE-ME-TO-A-LONG-RANDOM-STRING';
var DEFAULT_TAB = 'Responses';
var ALLOWED_TABS = ['Responses', 'Notify'];

// Email a one-line nudge when a response lands. Set to false for quiet mode.
var NOTIFY = true;
var NOTIFY_TO = 'ryan@flyovercon.ink';

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var body = JSON.parse(e.postData.contents);
    if (body.token !== TOKEN) {
      return json({ ok: false, error: 'bad token' });
    }

    var row = body.row || {};

    // The survey writes to Responses, the notify form writes to Notify.
    // Anything else is rejected so a bad payload cannot spawn stray tabs.
    var tab = body.tab || DEFAULT_TAB;
    if (ALLOWED_TABS.indexOf(tab) === -1) {
      return json({ ok: false, error: 'unknown tab: ' + tab });
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(tab);
    if (!sheet) sheet = ss.insertSheet(tab);

    var lastCol = sheet.getLastColumn();
    var headers = lastCol ? sheet.getRange(1, 1, 1, lastCol).getValues()[0] : [];

    Object.keys(row).forEach(function (key) {
      if (headers.indexOf(key) === -1) headers.push(key);
    });
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);

    var line = headers.map(function (h) {
      return row[h] === undefined ? '' : row[h];
    });
    sheet.appendRow(line);

    if (NOTIFY) {
      // A failed email must never fail the submission. The row is already saved.
      try {
        var count = sheet.getLastRow() - 1;
        MailApp.sendEmail({
          to: NOTIFY_TO,
          subject: 'FOC27 ' + (tab === 'Notify' ? 'list signup' : 'survey response') + ' #' + count,
          body: 'A new response just landed.\n\n' + ss.getUrl()
        });
      } catch (mailErr) {
        Logger.log('notify failed: ' + mailErr);
      }
    }

    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return json({ ok: false, error: 'POST only' });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
