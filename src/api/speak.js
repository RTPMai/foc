// FOC27 speaker proposal intake.
// Lives at https://www.flyovercon.ink/api/speak so the form POSTs same origin.
//
// Writes to a "Speakers" tab in the same Sheet as the survey and notify list,
// through the same Apps Script webhook, so there is still only one backend to
// keep alive. The tab name must also be listed in ALLOWED_TABS inside
// SHEET-APPS-SCRIPT.gs, or the webhook refuses the row.
//
// Env vars, shared with the survey and notify functions:
//   SHEETS_WEBHOOK_URL   required
//   SHEETS_WEBHOOK_TOKEN required
//   RESEND_API_KEY       optional
//   SURVEY_NOTIFY_TO     optional, defaults to ryan@flyovercon.ink
//
// Deliberately duplicates logic from notify.js rather than importing a shared
// module, same reasoning as that file. Proposals arrive in a narrow window and
// a lost one is not recoverable, so this path stays boring and independent.

const MAX_BODY_BYTES = 16 * 1024;
const SHEET_TAB = "Speakers";
const NOTIFY_FROM = "Flyover Con <survey@flyovercon.ink>";

function readJsonBody(req) {
  if (req.body && typeof req.body === "object") return Promise.resolve(req.body);
  return new Promise((resolve, reject) => {
    let raw = "";
    let bytes = 0;
    req.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > MAX_BODY_BYTES) {
        reject(new Error("body too large"));
        req.destroy();
        return;
      }
      raw += chunk;
    });
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (err) {
        reject(new Error("body was not valid JSON"));
      }
    });
    req.on("error", reject);
  });
}

function clean(value, max) {
  return String(value == null ? "" : value).trim().slice(0, max || 300);
}

// Deliberately permissive. The job is to catch typos, not to police addresses.
function looksLikeEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value);
}

async function appendToSheet(row) {
  const url = process.env.SHEETS_WEBHOOK_URL;
  const token = process.env.SHEETS_WEBHOOK_TOKEN;
  if (!url || !token) throw new Error("SHEETS_WEBHOOK_URL or SHEETS_WEBHOOK_TOKEN is not set");

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, tab: SHEET_TAB, row }),
    redirect: "follow",
  });
  if (!res.ok) throw new Error("sheet webhook returned " + res.status);
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch (err) {
    throw new Error("sheet webhook returned non JSON: " + text.slice(0, 200));
  }
  if (body.ok !== true) throw new Error("sheet webhook refused: " + (body.error || text.slice(0, 200)));
}

async function emailCopy(row) {
  const key = process.env.RESEND_API_KEY;
  if (!key) return;
  const to = process.env.SURVEY_NOTIFY_TO || "ryan@flyovercon.ink";
  const lines = Object.keys(row).map((k) => k + ": " + row[k]).join("\n");
  await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: NOTIFY_FROM,
      to: [to],
      subject: "FOC27 speaker proposal: " + (row.session_title || row.name),
      text: lines,
    }),
  });
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ ok: false, error: "method not allowed" });
  }

  let payload;
  try {
    payload = await readJsonBody(req);
  } catch (err) {
    return res.status(400).json({ ok: false, error: err.message });
  }

  // Honeypot. Return 200 so the bot sees success and does not retry.
  if (payload._gotcha) return res.status(200).json({ ok: true });

  const row = {
    name: clean(payload.name),
    shop: clean(payload.shop),
    role: clean(payload.role),
    email: clean(payload.email),
    phone: clean(payload.phone, 40),
    session_title: clean(payload.session_title),
    takeaway: clean(payload.takeaway, 4000),
    format: clean(payload.format, 60),
    equipment: clean(payload.equipment, 600),
    sample: clean(payload.sample, 600),
    notes: clean(payload.notes, 4000),
    status: "New",
    submitted_at: new Date().toISOString(),
  };

  if (!row.name) return res.status(400).json({ ok: false, error: "name is required" });
  if (!row.session_title) return res.status(400).json({ ok: false, error: "a working session title is required" });
  if (!row.takeaway) return res.status(400).json({ ok: false, error: "tell us what an attendee walks out able to do" });
  if (!looksLikeEmail(row.email)) {
    return res.status(400).json({ ok: false, error: "that email address does not look right" });
  }

  let sheetError = null;
  try {
    await appendToSheet(row);
  } catch (err) {
    sheetError = err;
    console.error("speak: sheet append failed:", err.message);
  }

  try {
    await emailCopy(row);
  } catch (err) {
    console.error("speak: email copy failed:", err.message);
    if (sheetError) return res.status(500).json({ ok: false, error: "could not record proposal" });
  }

  if (sheetError && !process.env.RESEND_API_KEY) {
    return res.status(500).json({ ok: false, error: "could not record proposal" });
  }

  return res.status(200).json({ ok: true });
}
