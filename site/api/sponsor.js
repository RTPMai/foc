// FOC27 sponsor inquiry intake.
// Lives at https://www.flyovercon.ink/api/sponsor so the form POSTs same origin.
//
// Writes to a "Sponsors" tab in the same Sheet as the survey and notify list,
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
// module, same reasoning as that file: this is money coming in the door and it
// is not worth a new failure mode to save forty lines.

const MAX_BODY_BYTES = 16 * 1024;
const SHEET_TAB = "Sponsors";
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

// ConControl, the internal event tracker. A second home for the same
// submission, alongside the Sheet, so an inquiry becomes a record with a clock
// on it instead of a row somebody has to notice and re-key.
//
// DELIBERATELY A THIRD SINK, NOT A REPLACEMENT. The Sheet keeps running. Two
// places holding the same handful of rows costs nothing, and a sponsor inquiry
// that vanishes because a new endpoint had a bad day is the one failure worth
// engineering around. Drop the Sheet once this has caught real submissions for
// a few weeks, or keep it as a backup.
//
// NEVER FAILS THE SUBMISSION. Its errors are logged and nothing else: the
// person on the page has done their part, and telling them it failed when the
// Sheet and the email both worked would be a lie that costs a sponsor.
//
// Env vars:
//   CONCONTROL_URL     e.g. https://app.pmapparel.com  (or the vercel.app host
//                      until that DNS is pointed). Unset means "not wired up
//                      yet" and this quietly does nothing.
//   CONCONTROL_SECRET  shared with CONCONTROL_INTAKE_SECRET on the other side.
//                      Every submission reaches ConControl from one Vercel
//                      address, so without this the per-IP rate limit meant for
//                      one abuser would cap the whole event.
async function forwardToConControl(path, payload) {
  const base = process.env.CONCONTROL_URL;
  if (!base) return;

  const headers = { "Content-Type": "application/json" };
  if (process.env.CONCONTROL_SECRET) headers["x-intake-secret"] = process.env.CONCONTROL_SECRET;

  // A slow or hanging ConControl must not hold the form open. Five seconds is
  // far longer than a healthy write and far shorter than a person waits.
  const stop = AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined;

  const res = await fetch(base.replace(/\/+$/, "") + path, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal: stop,
  });
  if (!res.ok) throw new Error("concontrol returned " + res.status);
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
      subject: "FOC27 sponsor inquiry: " + (row.company || row.name),
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
    company: clean(payload.company),
    name: clean(payload.name),
    email: clean(payload.email),
    phone: clean(payload.phone, 40),
    level: clean(payload.level, 60),
    notes: clean(payload.notes, 4000),
    status: "New",
    submitted_at: new Date().toISOString(),
  };

  if (!row.company) return res.status(400).json({ ok: false, error: "company is required" });
  if (!row.name) return res.status(400).json({ ok: false, error: "name is required" });
  if (!looksLikeEmail(row.email)) {
    return res.status(400).json({ ok: false, error: "that email address does not look right" });
  }

  let sheetError = null;
  try {
    await appendToSheet(row);
  } catch (err) {
    sheetError = err;
    console.error("sponsor: sheet append failed:", err.message);
  }

  try {
    await forwardToConControl("/api/concontrol/inquiry", {
      company: row.company,
      name: row.name,
      email: row.email,
      phone: row.phone,
      level: row.level,
      notes: row.notes,
    });
  } catch (err) {
    // Logged and swallowed on purpose. See forwardToConControl.
    console.error("sponsor: concontrol forward failed:", err.message);
  }

  try {
    await emailCopy(row);
  } catch (err) {
    console.error("sponsor: email copy failed:", err.message);
    if (sheetError) return res.status(500).json({ ok: false, error: "could not record inquiry" });
  }

  if (sheetError && !process.env.RESEND_API_KEY) {
    return res.status(500).json({ ok: false, error: "could not record inquiry" });
  }

  return res.status(200).json({ ok: true });
}
