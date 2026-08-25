/**
 * FOC27 survey, Sheet side.
 *
 * Setup, about five minutes:
 *  1. Create a Google Sheet. Name the first tab "Responses".
 *  2. Extensions, Apps Script. Delete the sample code, paste this file in.
 *  3. Edit TOKEN below to a long random string. Keep a copy.
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
 */

var TOKEN = 'CHANGE-ME-TO-A-LONG-RANDOM-STRING';
var TAB = 'Responses';

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var body = JSON.parse(e.postData.contents);
    if (body.token !== TOKEN) {
      return json({ ok: false, error: 'bad token' });
    }

    var row = body.row || {};
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(TAB);
    if (!sheet) sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet(TAB);

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
