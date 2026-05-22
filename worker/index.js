function encodeBase64(str) {
 return btoa(String.fromCharCode(...new TextEncoder().encode(str)));
}

function addCorsHeaders(response) {
 response.headers.set('Access-Control-Allow-Origin', '*');
 response.headers.set('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
 response.headers.set('Access-Control-Allow-Headers', 'Content-Type');
 return response;
}

export default {
 async fetch(request, env) {
 if (request.method === 'OPTIONS') {
 return addCorsHeaders(new Response(null, { status: 204 }));
 }

 const url = new URL(request.url);
 const path = url.pathname;

 if (request.method === 'GET' && path === '/config') {
 const token = env.GH_TOKEN;
 if (!token) {
 return addCorsHeaders(new Response('GH_TOKEN not found', { status: 500 }));
 }
 try {
 const downloadUrl = 'https://raw.githubusercontent.com/charlescome1995-prog/crossmart-monitor/main/backend/data/user_config.json';
 const resp = await fetch(downloadUrl, {
 headers: { 'Authorization': `Bearer ${token}` }
 });
 if (!resp.ok) {
 return addCorsHeaders(new Response('Config file not found', { status: 404 }));
 }
 const content = await resp.json();
 return addCorsHeaders(new Response(JSON.stringify(content), { status: 200, headers: { 'Content-Type': 'application/json' } }));
 } catch(e) {
 return addCorsHeaders(new Response('Error: ' + e.message, { status: 500 }));
 }
 }

 if (request.method !== 'POST') {
 return addCorsHeaders(new Response('Only POST allowed', { status: 405 }));
 }

 try {
 const body = await request.json();
 const { asins, keywords } = body;
 if (!asins || !keywords) {
 return addCorsHeaders(new Response('Missing asins or keywords', { status: 400 }));
 }

 const token = env.GH_TOKEN;
 if (!token) {
 return addCorsHeaders(new Response('GH_TOKEN not found', { status: 500 }));
 }

 const GITHUB_REPO = 'charlescome1995-prog/crossmart-monitor';
 const filePath = 'backend/data/user_config.json';
 const content = encodeBase64(JSON.stringify({ asins, keywords }));

 const headers = {
 'Authorization': `Bearer ${token}`,
 'Accept': 'application/vnd.github+json',
 'User-Agent': 'crossmart-worker',
 'X-GitHub-Api-Version': '2022-11-28'
 };

 let sha = null;
 const getResp = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/contents/${filePath}`, { headers });
 if (getResp.ok) {
 const data = await getResp.json();
 sha = data.sha;
 }

 const putBody = {
 message: `feat: update config ${new Date().toISOString()}`,
 content,
 branch: 'main'
 };
 if (sha) putBody.sha = sha;

 const putResp = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/contents/${filePath}`, {
 method: 'PUT',
 headers: { ...headers, 'Content-Type': 'application/json' },
 body: JSON.stringify(putBody)
 });

 if (putResp.ok) {
 return addCorsHeaders(new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
 } else {
 const err = await putResp.text();
 return addCorsHeaders(new Response(`GitHub error: ${err}`, { status: 500 }));
 }
 } catch(e) {
 return addCorsHeaders(new Response(`Error: ${e.message}`, { status: 500 }));
 }
 }
};
