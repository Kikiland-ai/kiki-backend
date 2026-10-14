"""Authenticated Site reverse-proxy boundary for HTTP and WebSocket traffic."""

import hmac
from starlette.responses import JSONResponse


class SiteProxyGuard:
    def __init__(self, app, secret):
        self.app = app
        self.secret = secret.encode()

    async def __call__(self, scope, receive, send):
        if scope['type'] not in ('http', 'websocket'):
            return await self.app(scope, receive, send)
        # A cloud host health probe gets no user/session data.
        if scope['type'] == 'http' and scope['path'] == '/health' and scope['method'] == 'GET':
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        supplied = headers.get(b'x-kiki-proxy-key', b'')
        owner = headers.get(b'x-kiki-owner', b'')
        valid = len(supplied) <= 256 and hmac.compare_digest(supplied, self.secret)
        # MCP discovery can be ownerless; tool execution checks its owner separately.
        valid = valid and (scope['path'] == '/mcp' or 1 <= len(owner) <= 256)
        if not valid:
            if scope['type'] == 'websocket':
                await send({'type': 'websocket.close', 'code': 1008})
            else:
                await JSONResponse({'detail': 'Authenticated Site proxy required'}, status_code=401)(scope, receive, send)
            return
        return await self.app(scope, receive, send)
