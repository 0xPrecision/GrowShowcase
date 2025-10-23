from urllib.parse import quote

from fastapi.responses import HTMLResponse


def _tg_redirect_html(bot_username: str, payload: str) -> HTMLResponse:
    payload_q = quote(payload or "")
    tg_deeplink = f"tg://resolve?domain={bot_username}&start={payload_q}"
    https_fallback = f"https://t.me/{bot_username}?start={payload_q}"
    html = f"""<!doctype html><html><head>
<meta charset="utf-8"><title>Redirecting…</title>
<meta http-equiv="refresh" content="0; url={tg_deeplink}">
<script>
  window.location = "{tg_deeplink}";
  setTimeout(function(){{ window.location = "{https_fallback}"; }}, 800);
</script>
<style>body{{font-family:system-ui,Arial,sans-serif;padding:24px;}}</style>
</head>
<body>
  <p>Opening Telegram… If nothing happens, <a href="{https_fallback}">tap here</a>.</p>
</body></html>"""
    return HTMLResponse(html)
