// Netlify Function v2 — chatbot di SOS Patto (proxy verso l'API Anthropic).
// La logica (prompt, strumenti, ciclo) sta in netlify/chat/core.mjs; qui solo HTTP e protezioni,
// sul modello del chatbot di SOSpermesso.
//
// Variabili d'ambiente:
//   ANTHROPIC_API_KEY    obbligatoria (scope Functions)
//   CHATBOT_DISABLED=1   spegne il chatbot (503)
//   CHATBOT_MODEL        modello (default in core.mjs)
//   CHATBOT_EFFORT       low | medium | high (default low)

import Anthropic from "@anthropic-ai/sdk";
import { getStore } from "@netlify/blobs";
import { rispondi } from "../chat/core.mjs";

const MAX_MESSAGES = 20; // 10 turni utente
const MAX_USER_CHARS = 2000;
const MAX_ASSISTANT_CHARS = 6000;
const MAX_BODY_BYTES = 60_000;
const PAGE_RE = /^\/[a-zA-Z0-9\-_.\/]{0,300}$/;

const IP_DAILY_LIMIT = 30; // messaggi per IP al giorno
const GLOBAL_DAILY_LIMIT = 600; // messaggi al giorno su tutto il sito (tetto di spesa)

const JSON_HEADERS = { "Content-Type": "application/json; charset=utf-8" };

const ERRORS = {
  badRequest: "Richiesta non valida.",
  tooLong: "Il messaggio è troppo lungo (massimo 2000 caratteri).",
  tooManyTurns: "Questa conversazione è troppo lunga. Inizia una nuova conversazione.",
  rateLimited: "Hai raggiunto il limite giornaliero di messaggi. Riprova domani.",
  overloaded: "Il servizio è momentaneamente sovraccarico. Riprova tra qualche minuto.",
  generic: "Si è verificato un errore. Riprova più tardi.",
};

const jsonError = (message, status) =>
  new Response(JSON.stringify({ error: message }), { status, headers: JSON_HEADERS });

function isAllowedOrigin(req) {
  const value = req.headers.get("origin") || req.headers.get("referer");
  if (!value) return false;
  let hostname, protocol;
  try {
    ({ hostname, protocol } = new URL(value));
  } catch {
    return false;
  }
  if (hostname === "localhost" || hostname === "127.0.0.1") return true;
  if (protocol !== "https:") return false;
  return hostname === "sospatto.it" || hostname === "www.sospatto.it" || hostname.endsWith(".netlify.app");
}

function validate(payload) {
  const messages = payload?.messages;
  if (!Array.isArray(messages) || messages.length === 0) return jsonError(ERRORS.badRequest, 400);
  if (messages.length > MAX_MESSAGES) return jsonError(ERRORS.tooManyTurns, 400);
  for (let i = 0; i < messages.length; i++) {
    const m = messages[i];
    if (!m || typeof m.content !== "string" || m.content.trim() === "") return jsonError(ERRORS.badRequest, 400);
    if (m.role !== (i % 2 === 0 ? "user" : "assistant")) return jsonError(ERRORS.badRequest, 400);
    if (m.content.length > (m.role === "user" ? MAX_USER_CHARS : MAX_ASSISTANT_CHARS)) return jsonError(ERRORS.tooLong, 400);
  }
  if (messages[messages.length - 1].role !== "user") return jsonError(ERRORS.badRequest, 400);
  return null;
}

// Contatori giornalieri in Netlify Blobs. Read-modify-write non atomico: piccoli sforamenti possibili.
// Se Blobs non risponde lascia passare (un guasto di Blobs non deve spegnere il chatbot).
async function checkRateLimits(ip) {
  try {
    const store = getStore("chatbot-limits");
    const day = new Date().toISOString().slice(0, 10);
    const ipKey = `ip:${day}:${ip}`;
    const globalKey = `global:${day}`;
    const [ipCount, globalCount] = await Promise.all([
      store.get(ipKey).then((v) => parseInt(v, 10) || 0),
      store.get(globalKey).then((v) => parseInt(v, 10) || 0),
    ]);
    if (ipCount >= IP_DAILY_LIMIT || globalCount >= GLOBAL_DAILY_LIMIT) return false;
    await Promise.all([store.set(ipKey, String(ipCount + 1)), store.set(globalKey, String(globalCount + 1))]);
    return true;
  } catch (error) {
    console.error("[chat] rate limiter non disponibile:", error.message);
    return true;
  }
}

export default async (req, context) => {
  if (req.method !== "POST") return jsonError("Method not allowed", 405);
  if (process.env.CHATBOT_DISABLED === "1") return jsonError(ERRORS.overloaded, 503);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("[chat] ANTHROPIC_API_KEY mancante");
    return jsonError(ERRORS.generic, 500);
  }
  if (!isAllowedOrigin(req)) return jsonError("Forbidden", 403);

  let payload;
  try {
    const raw = await req.text();
    if (raw.length > MAX_BODY_BYTES) return jsonError(ERRORS.badRequest, 400);
    payload = JSON.parse(raw);
  } catch {
    return jsonError(ERRORS.badRequest, 400);
  }
  const invalid = validate(payload);
  if (invalid) return invalid;

  const ip = context.ip || req.headers.get("x-nf-client-connection-ip") || "unknown";
  if (!(await checkRateLimits(ip))) return jsonError(ERRORS.rateLimited, 429);

  const pagina = typeof payload.page === "string" && PAGE_RE.test(payload.page) ? payload.page : undefined;
  const encoder = new TextEncoder();
  const abort = new AbortController();

  const body = new ReadableStream({
    async start(controller) {
      let sentAny = false;
      try {
        const { usage, strumenti } = await rispondi(payload.messages, {
          pagina,
          signal: abort.signal,
          onText: (t) => { sentAny = true; controller.enqueue(encoder.encode(t)); },
        });
        // Nessun contenuto delle conversazioni nei log: solo token e strumenti usati.
        console.log("[chat] usage:", JSON.stringify(usage), "tools:", JSON.stringify(strumenti.map((s) => s.nome)));
        if (!sentAny) controller.enqueue(encoder.encode(ERRORS.generic));
      } catch (error) {
        const overloaded = error instanceof Anthropic.RateLimitError ||
          (error instanceof Anthropic.APIError && error.status === 529);
        console.error("[chat] errore:", error?.status, error?.message);
        controller.enqueue(encoder.encode(sentAny ? "\n\n(Risposta interrotta, riprova.)" : overloaded ? ERRORS.overloaded : ERRORS.generic));
      } finally {
        controller.close();
      }
    },
    cancel() {
      abort.abort();
    },
  });

  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" },
  });
};
