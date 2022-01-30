import asyncio
import json
import logging
from concurrent import futures

from aiohttp import web

from wls.api import RestEndpoint
from wls.events import Event

_LOGGER = logging.getLogger(__name__)
LOG_HISTORY_MAXLEN = 30


class LogEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/log"

    def __init__(self, wls):
        self.logwebsocket = LogWebsocket(wls, wls.logqueue)

    async def get(self, request) -> web.Response:
        return await self.logwebsocket.handle(request)


class LogWebsocket:
    def __init__(self, wls, queue):
        self._wls = wls
        self._sender_queue = queue
        self._socket = None
        self._receiver_task = None
        self._sender_task = None
        self._log_history = []

    def close(self):
        """Closes the websocket connection"""
        if self._receiver_task:
            self._receiver_task.cancel()
        if self._sender_task:
            self._sender_task.cancel()

    def log_append(self, msg):
        self._log_history.append(msg)
        self._log_history = self._log_history[-LOG_HISTORY_MAXLEN:]

    async def send(self, msg):
        await self._socket.send_json(msg.__dict__, dumps=json.dumps)

    async def _sender(self):
        """Async write loop to pull from the queue and send"""

        _LOGGER.info("Bắt đầu gửi nhật ký")
        try:
            # send log history on socket open
            for msg in self._log_history:
                await self.send(msg)

            # keep sending and adding to history while socket open
            while not self._socket.closed:
                msg = await self._sender_queue.get()
                self.log_append(msg)
                await self.send(msg)

        except TypeError as e:
            if self._socket.closed:
                _LOGGER.info("Máy khách đã đóng kết nối ghi nhật ký.")
            else:
                _LOGGER.exception(f"Loại lỗi không mong muốn: {e}")

        except (asyncio.CancelledError, futures.CancelledError):
            _LOGGER.info("Kết nối ghi nhật ký bị hủy")
        # Hopefully get rid of the aiohttp connection reset errors
        except ConnectionResetError:
            _LOGGER.info("Đặt lại kết nối ghi nhật ký")

        except Exception as err:
            _LOGGER.exception("Ngoại lệ bất ngờ: %s", err)

        _LOGGER.info("Đang dừng người gửi nhật ký")

    async def handle(self, request):
        """Handle the websocket connection"""
        # close existing connection and sender if it exists
        self.close()
        if self._socket is not None:
            await self._socket.close()

        socket = self._socket = web.WebSocketResponse()
        await socket.prepare(request)
        _LOGGER.info("Đã mở websocket ghi nhật ký")

        self._receiver_task = asyncio.current_task(loop=self._wls.loop)
        self._sender_task = self._wls.loop.create_task(self._sender())

        def shutdown_handler(e):
            self.close()

        remove_listeners = self._wls.events.add_listener(
            shutdown_handler, Event.WLS_SHUTDOWN
        )

        try:
            while await socket.receive_json():
                # ignore any incoming messages
                pass

        except TypeError as e:
            if socket.closed:
                _LOGGER.info("Máy khách đã đóng kết nối ghi nhật ký.")
            else:
                _LOGGER.exception(f"Loại không mong muốnError: {e}")

        except (asyncio.CancelledError, futures.CancelledError):
            _LOGGER.info("Kết nối ghi nhật ký bị hủy")
        # Hopefully get rid of the aiohttp connection reset errors
        except ConnectionResetError:
            _LOGGER.info("Đặt lại kết nối ghi nhật ký")

        except Exception as err:
            _LOGGER.exception("Ngoại lệ bất ngờ: %s", err)

        finally:
            remove_listeners()

            # Close the connection
            await socket.close()
            await self._sender_task

            _LOGGER.info("Websocket ghi nhật ký đã đóng")

        return socket
