import logging
import os
import ssl
import sys
import time

from aiohttp import web

import wls_frontend
from wls.api import RestApi

_LOGGER = logging.getLogger(__name__)


class HttpServer:
    def __init__(self, wls, host, port, port_s):
        """Initialize the HTTP server"""

        self.app = web.Application()
        self.api = RestApi(wls)

        self.register_routes()

        self._wls = wls
        self.host = host
        self.port = port
        self.port_s = port_s

    def register_routes(self):

        self.api.register_routes(self.app)
        self.app.router.add_static(
            "/favicon",
            path=wls_frontend.where() + "/favicon",
            name="favicon",
        )
        self.app.router.add_route("get", "/manifest.json", self.manifest)
        self.app.router.add_route(
            "get", "/serviceWorker.js", self.service_worker
        )
        self.app.router.add_route(
            "get", "/service-worker.js", self.service_worker_b
        )
        self.app.router.add_route("get", "/callback/", self.index)
        self.app.router.add_route("get", "/", self.index)

        self.app.router.add_static(
            "/static",
            path=wls_frontend.where() + "/static",
            name="static",
        )

    async def index(self, response):

        return web.FileResponse(
            path=wls_frontend.where() + "/index.html", status=200
        )

    async def manifest(self, response):
        return web.FileResponse(
            path=wls_frontend.where() + "/manifest.json", status=200
        )

    async def service_worker(self, response):
        return web.FileResponse(
            path=wls_frontend.where() + "/service-worker.js", status=200
        )

    async def service_worker_b(self, response):
        return web.FileResponse(
            path=wls_frontend.where() + "/service-worker.js", status=200
        )

    async def start(self, ssl_certs=None):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        try:
            await self.start_tcpsite()
            if ssl_certs:
                ssl_context = ssl.create_default_context(
                    ssl.Purpose.CLIENT_AUTH
                )
                ssl_context.load_cert_chain(*ssl_certs)
                await self.start_tcpsite(ssl_context)
        except OSError as error:
            self.handle_start_error(error)

    async def start_tcpsite(self, ssl_context=None):
        port = self.port_s if ssl_context else self.port
        site = web.TCPSite(
            self.runner, self.host, port, ssl_context=ssl_context
        )
        await site.start()
        self.base_url = ("http{}://{}:{}").format(
            "s" if ssl_context else "", self.host, port
        )
        if self.host == "0.0.0.0":
            self.base_url = ("http{}://localhost:{}").format(
                "s" if ssl_context else "", port
            )
        print(("Bắt đầu giao diện web tại {}").format(self.base_url))

    def handle_start_error(self, error):
        _LOGGER.error(
            "Đang tắt - Không tạo được máy chủ HTTP tại cổng %d: %s.",
            self.port,
            error,
        )
        _LOGGER.error(
            "WiFi Led Studio đã chạy chưa? Nếu không, hãy thử một cổng khác."
        )
        if self._wls.icon is not None:
            if self._wls.icon.HAS_NOTIFICATION:
                self._wls.icon.notify(
                    f"Không thể bắt đầu: một cái gì đó đang chạy trên cổng {self.port}\nWiFi Led Studio đã chạy chưa?",
                    "WiFi Led Studio",
                )
        time.sleep(2)
        self._wls.stop(1)

    async def stop(self):
        await self.app.shutdown()
        if self.runner:
            await self.runner.cleanup()
        await self.app.cleanup()
