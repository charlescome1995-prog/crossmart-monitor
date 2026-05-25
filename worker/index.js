/**
 * CrossMart Config API Worker
 * Pure API only - no HTML responses
 * Endpoints: GET/POST /config
 */

const GH_TOKEN = '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';
const REPO = 'charlescome1995-prog/crossmart-monitor';
const CONFIG_PATH = 'backend/data/user_config.json';

const UA = {
  'Authorization': `token ${GH_TOKEN}`,
  'Accept': 'application/vnd.github.v3+json',
  'User-Agent': 'crossmart-monitor/1.0'
};

async function handleRequest(request) {
  const url = new URL(request.url);

  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    });
  }

  if (url.pathname === '/config' && request.method === 'GET') {
    const h = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
    try {
      const resp = await fetch(`https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`, { headers: UA });
      if (!resp.ok) return new Response('{}', { headers: h });
      const data = await resp.json();
      return new Response(atob(data.content), { headers: h });
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), { headers: h, status: 500 });
    }
  }

  if (url.pathname === '/config' && request.method === 'POST') {
    const h = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: 'bad json' }), { headers: h, status: 400 });
    }

    try {
      const enc = btoa(unescape(encodeURIComponent(JSON.stringify(body, null, 2))));
      const getResp = await fetch(`https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`, { headers: UA });
      const existing = getResp.ok ? await getResp.json() : null;

      const putResp = await fetch(`https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`, {
        method: 'PUT',
        headers: { ...UA, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `feat: update user config ${new Date().toISOString()}`,
          content: enc,
          sha: existing ? existing.sha : undefined
        })
      });

      if (!putResp.ok) {
        const errData = await putResp.json();
        return new Response(JSON.stringify({ error: errData }), { headers: h, status: 502 });
      }

      return new Response(JSON.stringify({ ok: true }), { headers: h });
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), { headers: h, status: 500 });
    }
  }

  return new Response('Not Found', { status: 404 });
}

addEventListener('fetch', event => event.respondWith(handleRequest(event.request)));