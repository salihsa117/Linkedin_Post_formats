/**
 * Free glue that runs as YOU inside Google (no hosting).
 * Script Properties required:
 *   GH_TOKEN        fine-grained PAT, repo "Linkedin_Post_formats", permission Actions: read & write
 *   GH_REPO         salihsa117/Linkedin_Post_formats
 *   INBOX_FOLDER_ID Drive folder you drop raw videos into
 *   WORK_FOLDER_ID  Drive folder where picked-up videos are moved
 *   SHEET_ID        the Posts spreadsheet (tabs: Posts, Links)
 *   PUBLISH_WEBHOOK optional URL of whichever publisher you choose (see docs/SETUP_AR.md)
 * Add time-driven triggers: scanInbox every 5 min, publishDue every 15 min.
 */
function P_(k) { return PropertiesService.getScriptProperties().getProperty(k); }

function dispatch_(inputs) {
  var res = UrlFetchApp.fetch(
    'https://api.github.com/repos/' + P_('GH_REPO') + '/actions/workflows/process-video.yml/dispatches', {
      method: 'post', muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + P_('GH_TOKEN'), Accept: 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28' },
      contentType: 'application/json',
      payload: JSON.stringify({ ref: 'main', inputs: inputs })
    });
  if (res.getResponseCode() !== 204) throw new Error('dispatch failed: ' + res.getContentText());
}

function scanInbox() {
  var inbox = DriveApp.getFolderById(P_('INBOX_FOLDER_ID'));
  var work = DriveApp.getFolderById(P_('WORK_FOLDER_ID'));
  var files = inbox.getFiles();
  while (files.hasNext()) {
    var f = files.next();
    if (f.getMimeType().indexOf('video/') !== 0) continue;
    dispatch_({ file_id: f.getId(), mode: 'auto', clips: '5', youtube_url: '' });
    f.moveTo(work);                       // moved only after a successful dispatch
  }
  var tab = SpreadsheetApp.openById(P_('SHEET_ID')).getSheetByName('Links');
  if (!tab) return;
  var rows = tab.getDataRange().getValues();   // A: url, B: status (blank = new)
  for (var i = 0; i < rows.length; i++) {
    var url = String(rows[i][0] || '').trim();
    if (/^https?:\/\//.test(url) && !rows[i][1]) {
      dispatch_({ youtube_url: url, file_id: '', mode: 'auto', clips: '5' });
      tab.getRange(i + 1, 2).setValue('sent ' + new Date().toISOString());
    }
  }
}

/** Sends every row whose status is ready and time has come to PUBLISH_WEBHOOK. */
function publishDue() {
  var hook = P_('PUBLISH_WEBHOOK');
  if (!hook) return;
  var tab = SpreadsheetApp.openById(P_('SHEET_ID')).getSheetByName('Posts');
  var v = tab.getDataRange().getValues();
  var h = v[0], c = {};
  h.forEach(function (n, i) { c[n] = i; });
  var now = new Date();
  for (var r = 1; r < v.length; r++) {
    var row = v[r];
    if (row[c.status] !== 'approved') continue;           // you flip ready -> approved from your phone
    if (new Date(row[c.scheduled_at]) > now) continue;
    var obj = {};
    h.forEach(function (n, i) { obj[n] = row[i]; });
    var res = UrlFetchApp.fetch(hook, { method: 'post', contentType: 'application/json',
                                        payload: JSON.stringify(obj), muteHttpExceptions: true });
    tab.getRange(r + 1, c.status + 1).setValue(res.getResponseCode() < 300 ? 'sent' : 'failed');
  }
}
