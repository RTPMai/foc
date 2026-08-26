// FOC27 notify list intake.
// Lives at https://www.flyovercon.ink/api/notify so the form POSTs same origin
// and the highest intent click on the site never leaves the domain.
//
// Writes to a separate "Notify" tab in the same Sheet as the survey, through
// the same Apps Script webhook, so there is only one backend to keep alive.
//
// Env vars, shared with the survey function:
//   SHEETS_WEBHOOK_URL   required
//   SHEETS_WEBHOOK_TOKEN required
//   RESEND_API_KEY       optional
//   SURVEY_NOTIFY_TO     optional, defaults to ryan@flyovercon.ink
//
// This deliberately duplicates a little logic from survey.js rather than
// importing a shared module. The bundler handles relative imports fine, but
// this is the highest value form on the site and it is not worth a new
// failure mode to save forty lines.

const MAX_BODY_BYTES = 8 * 1024;
const SHEET_TAB = "Notify";
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

function clean(value) {
  return String(value == null ? "" : value).trim().slice(0, 300);
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
      subject: "FOC27 list signup",
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
    email: clean(payload.email),
    city_state: clean(payload.city_state),
    submitted_at: new Date().toISOString(),
  };

  if (!row.name) return res.status(400).json({ ok: false, error: "name is required" });
  if (!looksLikeEmail(row.email)) {
    return res.status(400).json({ ok: false, error: "that email address does not look right" });
  }

  let sheetError = null;
  try {
    await appendToSheet(row);
  } catch (err) {
    sheetError = err;
    console.error("notify: sheet append failed:", err.message);
  }

  try {
    await emailCopy(row);
  } catch (err) {
    console.error("notify: email copy failed:", err.message);
    if (sheetError) return res.status(500).json({ ok: false, error: "could not record signup" });
  }

  if (sheetError && !process.env.RESEND_API_KEY) {
    return res.status(500).json({ ok: false, error: "could not record signup" });
  }

  return res.status(200).json({ ok: true });
}
