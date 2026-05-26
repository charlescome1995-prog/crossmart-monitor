export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (url.pathname === '/config') {
      const h = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json',
      };

      const GH_TOKEN = env.GH_TOKEN;
      const REPO = env.GH_REPO;
      const CONFIG_PATH = env.GH_CONFIG_PATH;
      const UA = {
        'Authorization': `token ${GH_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'crossmart-monitor/1.0',
      };

      // GET — 读取 GitHub 上的配置
      if (request.method === 'GET') {
        try {
          const resp = await fetch(
            `https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`,
            { headers: UA }
          );
          if (!resp.ok) return new Response('{}', { headers: h });
          const data = await resp.json();
          return new Response(atob(data.content), { headers: h });
        } catch (e) {
          return new Response('{}', { headers: h });
        }
      }

      // POST — 写入 GitHub 上的配置
      if (request.method === 'POST') {
        let body;
        try {
          body = await request.json();
        } catch (e) {
          return new Response(JSON.stringify({ error: 'bad json' }), {
            headers: h,
            status: 400,
          });
        }

        try {
          // 1. 获取当前 sha（用于防冲突）
          const getResp = await fetch(
            `https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`,
            { headers: UA }
          );
          const existing = getResp.ok ? await getResp.json() : null;

          // 2. 写入文件
          const content = btoa(unescape(encodeURIComponent(JSON.stringify(body, null, 2))));
          const putResp = await fetch(
            `https://api.github.com/repos/${REPO}/contents/${CONFIG_PATH}`,
            {
              method: 'PUT',
              headers: { ...UA, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message: 'update user_config',
                content,
                sha: existing?.sha,
              }),
            }
          );

          const putData = putResp.ok ? await putResp.json() : { error: await putResp.text() };
          return new Response(JSON.stringify({ ok: putResp.ok, data: putData }), {
            headers: h,
            status: putResp.ok ? 200 : 502,
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: e.message }), {
            headers: h,
            status: 502,
          });
        }
      }
    }

    // 默认返回简单的 HTML 配置页（生产环境建议关闭）
    const HTML = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>CrossMart Worker</title></head>
<body><h2>Worker 在线</h2><p>GitHub: charlescome1995-prog/crossmart-monitor</p></body></html>`;
    return new Response(HTML, {
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  },
};