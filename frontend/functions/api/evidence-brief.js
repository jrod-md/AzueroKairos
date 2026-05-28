const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const DEFAULT_MODEL = "deepseek/deepseek-v4-flash:free";
const DEFAULT_APP_NAME = "Azuero Kairos";
const REQUEST_TIMEOUT_MS = 15000;
const MAX_PACKET_CHARS = 12000;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
};

const SYSTEM_PROMPT = [
  "Eres un asistente de evidencia para Azuero Kairos.",
  "Responde en espanol sobrio y tecnico.",
  "Usa exclusivamente el paquete de evidencia recibido.",
  "No crees hechos, no agregues fuentes y no cambies la clasificacion Sentinel-2.",
  "SAR, CLMS, HydroClimate e IA son contexto auxiliar.",
  "La salida debe ser JSON estricto con estas claves: decision_summary, evidence_used, evidence_gaps, limits, recommended_action, artifact_refs.",
  "Cada lista debe contener textos breves. No devuelvas Markdown ni texto fuera del JSON.",
].join(" ");

export async function onRequestOptions() {
  return jsonResponse({ ok: true });
}

export async function onRequestGet() {
  return jsonResponse({ mode: "fallback", reason: "post_required" }, 405);
}

export async function onRequestPost({ request, env }) {
  const apiKey = typeof env?.OPENROUTER_API_KEY === "string"
    ? env.OPENROUTER_API_KEY.trim()
    : "";

  if (!apiKey) {
    return jsonResponse({ mode: "fallback", reason: "missing_key" });
  }

  const model = safeText(env?.OPENROUTER_MODEL, 140) || DEFAULT_MODEL;
  const appName = safeText(env?.OPENROUTER_APP_NAME, 140) || DEFAULT_APP_NAME;
  const siteUrl = safeUrl(env?.OPENROUTER_SITE_URL);

  let packet;
  try {
    const body = await request.json();
    packet = sanitizePacket(body?.evidence_packet);
  } catch {
    return jsonResponse({ mode: "fallback", reason: "invalid_request" });
  }

  if (!packet) {
    return jsonResponse({ mode: "fallback", reason: "invalid_packet" });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
        ...(siteUrl ? { "HTTP-Referer": siteUrl } : {}),
        "X-Title": appName,
      },
      signal: controller.signal,
      body: JSON.stringify({
        model,
        temperature: 0.1,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          {
            role: "user",
            content: JSON.stringify({
              evidence_packet: packet,
              required_schema: {
                decision_summary: "string",
                evidence_used: ["string"],
                evidence_gaps: ["string"],
                limits: ["string"],
                recommended_action: "string",
                artifact_refs: ["string"],
              },
            }),
          },
        ],
      }),
    });

    if (!response.ok) {
      return jsonResponse({ mode: "fallback", reason: `upstream_${response.status}` });
    }

    const upstream = await response.json();
    const content = upstream?.choices?.[0]?.message?.content;
    const parsed = parseJsonObject(content);
    const validated = validateBrief(parsed);

    if (!validated.ok) {
      return jsonResponse({ mode: "fallback", reason: validated.reason });
    }

    return jsonResponse({
      mode: "ai",
      model,
      ...validated.brief,
    });
  } catch (error) {
    return jsonResponse({
      mode: "fallback",
      reason: error?.name === "AbortError" ? "timeout" : "request_failed",
    });
  } finally {
    clearTimeout(timeout);
  }
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: JSON_HEADERS,
  });
}

function sanitizePacket(value) {
  if (!isObject(value)) return null;
  const cleaned = sanitizeValue(value, 0);
  const serialized = JSON.stringify(cleaned);
  if (!serialized || serialized.length > MAX_PACKET_CHARS) return null;
  if (!cleaned?.selected_date || !cleaned?.sentinel2?.confidence_class) return null;
  return cleaned;
}

function sanitizeValue(value, depth) {
  if (depth > 5) return null;
  if (Array.isArray(value)) {
    return value
      .slice(0, 24)
      .map((item) => sanitizeValue(item, depth + 1))
      .filter((item) => item !== null && item !== undefined);
  }
  if (isObject(value)) {
    const result = {};
    for (const [key, entry] of Object.entries(value)) {
      if (shouldDropKey(key)) continue;
      const cleaned = sanitizeValue(entry, depth + 1);
      if (cleaned !== null && cleaned !== undefined && cleaned !== "") {
        result[safeKey(key)] = cleaned;
      }
    }
    return result;
  }
  if (typeof value === "string") return safeText(value, 700);
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "boolean") return value;
  return null;
}

function shouldDropKey(key) {
  const normalized = String(key || "").toLowerCase();
  const fragments = [
    "token",
    "secret",
    "credential",
    "authorization",
    "header",
    "cookie",
    "password",
    "api_key",
    "apikey",
  ];
  return fragments.some((fragment) => normalized.includes(fragment));
}

function safeKey(key) {
  return String(key || "")
    .replace(/[^\w.-]/g, "_")
    .slice(0, 80);
}

function safeText(value, maxLength = 700) {
  if (typeof value !== "string") return "";
  const trimmed = value.trim().replace(/\s+/g, " ");
  if (!trimmed) return "";
  if (/^[A-Za-z]:[\\/]/.test(trimmed) || trimmed.startsWith("\\\\")) {
    return "referencia no publica";
  }
  return trimmed.replaceAll("\\", "/").slice(0, maxLength);
}

function safeUrl(value) {
  const text = safeText(value, 300);
  if (!text) return "";
  try {
    const url = new URL(text);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : "";
  } catch {
    return "";
  }
}

function parseJsonObject(value) {
  if (isObject(value)) return value;
  if (typeof value !== "string") return null;
  try {
    return JSON.parse(value);
  } catch {
    const start = value.indexOf("{");
    const end = value.lastIndexOf("}");
    if (start < 0 || end <= start) return null;
    try {
      return JSON.parse(value.slice(start, end + 1));
    } catch {
      return null;
    }
  }
}

function validateBrief(candidate) {
  if (!isObject(candidate)) return { ok: false, reason: "invalid_json" };
  if (containsUnsafeClaim(candidate)) {
    return { ok: false, reason: "claim_guard" };
  }

  const brief = {
    decision_summary: safeText(candidate.decision_summary, 700),
    evidence_used: cleanStringList(candidate.evidence_used),
    evidence_gaps: cleanStringList(candidate.evidence_gaps),
    limits: cleanStringList(candidate.limits),
    recommended_action: safeText(candidate.recommended_action, 700),
    artifact_refs: cleanStringList(candidate.artifact_refs),
  };

  if (
    !brief.decision_summary ||
    !brief.recommended_action ||
    !brief.evidence_used.length ||
    !brief.evidence_gaps.length ||
    !brief.limits.length ||
    !brief.artifact_refs.length
  ) {
    return { ok: false, reason: "schema_mismatch" };
  }

  return { ok: true, brief };
}

function cleanStringList(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => safeText(item, 420))
    .filter(Boolean)
    .slice(0, 8);
}

function containsUnsafeClaim(value) {
  const text = stripMarks(JSON.stringify(value)).toLowerCase();
  const checks = [
    ["contamin"],
    ["quimic"],
    ["sanitari"],
    ["potab"],
    ["agua", "segur"],
    ["safe", "water"],
    ["water", "safety"],
    ["atraz"],
    ["pestic"],
    ["metal", "pesad"],
    ["heavy", "metal"],
    ["patogen"],
    ["cri" + "sis"],
    ["cierre", "automatic"],
    ["automatic", "closure"],
    ["suspension", "oblig"],
    ["mandatory", "suspension"],
    ["oper" + "ativo"],
    ["oper" + "ational"],
    ["ia", "detect"],
    ["ia", "decid"],
    ["ia", "confirm"],
    ["ai", "analyst"],
  ];
  return checks.some((parts) => parts.every((part) => text.includes(part)));
}

function stripMarks(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
