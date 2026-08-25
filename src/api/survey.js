// FOC27 planning survey intake.
// Lives at https://www.flyovercon.ink/api/survey so the form POSTs same origin.
// No CORS, no third party form vendor, no branding that is not ours.
//
// Env vars, set in the Vercel project (Settings, Environment Variables):
//   SHEETS_WEBHOOK_URL   required. Apps Script /exec URL bound to the response Sheet.
//   SHEETS_WEBHOOK_TOKEN required. Shared secret, must match the Apps Script.
//   RESEND_API_KEY       optional. If set, a copy of every submission is emailed.
//   SURVEY_NOTIFY_TO     optional. Defaults to ryan@flyovercon.ink.
//
// If the Sheet write fails and Resend is configured, the email still goes out,
// the response is still counted as accepted, and the failure is logged. Losing a
// five minute survey response is worse than a duplicate.

const MAX_BODY_BYTES = 64 * 1024;
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

function flatten(payload) {
  const out = {};
  Object.keys(payload).forEach((key) => {
    const value = payload[key];
    out[key] = Array.isArray(value) ? value.join(" | ") : String(value == null ? "" : value);
  });
  return out;
}

async function appendToSheet(row) {
  const url = process.env.SHEETS_WEBHOOK_URL;
  const token = process.env.SHEETS_WEBHOOK_TOKEN;
  if (!url || !token) throw new Error("SHEETS_WEBHOOK_URL or SHEETS_WEBHOOK_TOKEN is not set");

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, row }),
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
      subject: "FOC27 survey response",
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

  // Honeypot. The page strips this before sending, so anything here is a bot.
  // Return 200 so the bot sees success and does not retry.
  if (payload._gotcha) return res.status(200).json({ ok: true });
  delete payload._gotcha;

  if (!Object.keys(payload).length) {
    return res.status(400).json({ ok: false, error: "empty submission" });
  }

  const row = flatten(payload);
  if (!row.submitted_at) row.submitted_at = new Date().toISOString();

  let sheetError = null;
  try {
    await appendToSheet(row);
  } catch (err) {
    sheetError = err;
    console.error("survey: sheet append failed:", err.message);
  }

  try {
    await emailCopy(row);
  } catch (err) {
    console.error("survey: email copy failed:", err.message);
    if (sheetError) {
      return res.status(500).json({ ok: false, error: "could not record submission" });
    }
  }

  if (sheetError && !process.env.RESEND_API_KEY) {
    return res.status(500).json({ ok: false, error: "could not record submission" });
  }

  return res.status(200).json({ ok: true });
}
