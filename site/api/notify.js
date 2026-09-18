// FOC27 notify list intake.
// Lives at https://www.flyovercon.ink/api/notify so the form POSTs same origin
// and the highest intent click on the site never leaves the domain.
//
// Writes to ConControl, the internal event tracker. No Google Sheet. The
// survey still uses the Sheet; this form does not.
//
// Env vars:
//   CONCONTROL_URL       required, e.g. https://app.pmapparel.com (or the
//                        vercel.app host until that DNS is pointed)
//   CONCONTROL_SECRET    strongly recommended, shared with
//                        CONCONTROL_INTAKE_SECRET on the other side. Every
//                        submission reaches ConControl from one Vercel
//                        address, so without it the per-IP rate limit meant
//                        for one abuser would cap the whole event.
//   RESEND_API_KEY       optional, but it is the only backup. If ConControl
//                        has a bad day and this is set, the signup still
//                        reaches you by email and the visitor sees success.
//   SURVEY_NOTIFY_TO     optional, defaults to ryan@flyovercon.ink
//
// This deliberately duplicates a little logic from survey.js rather than
// importing a shared module. The bundler handles relative imports fine, but
// this is the highest value form on the site and it is not worth a new
// failure mode to save forty lines.

const MAX_BODY_BYTES = 8 * 1024;
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

async function sendToConControl(path, payload) {
  const base = process.env.CONCONTROL_URL;
  if (!base) throw new Error("CONCONTROL_URL is not set");

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

// Returns true only if Resend actually accepted the email, so it can be
// trusted as the backup when ConControl fails.
async function emailCopy(row) {
  const key = process.env.RESEND_API_KEY;
  if (!key) return false;
  const to = process.env.SURVEY_NOTIFY_TO || "ryan@flyovercon.ink";
  const lines = Object.keys(row).map((k) => k + ": " + row[k]).join("\n");
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: NOTIFY_FROM,
      to: [to],
      subject: "FOC27 list signup",
      text: lines,
    }),
  });
  if (!res.ok) throw new Error("resend returned " + res.status);
  return true;
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

  let recorded = false;

  try {
    await sendToConControl("/api/concontrol/signup", row);
    recorded = true;
  } catch (err) {
    console.error("notify: concontrol failed:", err.message);
  }

  try {
    if (await emailCopy(row)) recorded = true;
  } catch (err) {
    console.error("notify: email copy failed:", err.message);
  }

  if (!recorded) return res.status(500).json({ ok: false, error: "could not record signup" });
  return res.status(200).json({ ok: true });
}
