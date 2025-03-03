import React, { useEffect, useLayoutEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import useStore from './apiStore';
import Sockette from 'sockette';
import isElectron from 'is-electron';

function createSocket() {
  if (!window.localStorage.getItem('wls-newbase')) {
    const _ws = new Sockette(`${(window.localStorage.getItem('wls-host') || (isElectron() ? 'http://localhost:8090' : window.location.href.split('/#')[0])).replace('https://', 'wss://').replace('http://', 'ws://')}/api/websocket`, {
      timeout: 1e3,
      maxAttempts: Infinity,
      onopen: e => {
        document.dispatchEvent(
          new CustomEvent("disconnected", {
            detail: {
              isDisconnected: false
            }
          })
        );
        _ws.ws = e.target;

        // Cập nhật wsReady ngay khi kết nối được mở
        document.dispatchEvent(
          new CustomEvent("wsReady", {
            detail: true
          })
        );

        const req = {
          event_type: "devices_updated",
          id: 1,
          type: "subscribe_event",
        };
        ws.send(JSON.stringify(++req.id && req));
      },
      onmessage: (event) => {
        if (JSON.parse(event.data).event_type === "visualisation_update") {
          document.dispatchEvent(
            new CustomEvent("YZ", {
              detail: {
                id: JSON.parse(event.data).vis_id,
                pixels: JSON.parse(event.data).pixels,
              }
            })
          );
        }
        if (JSON.parse(event.data).event_type === "devices_updated") {
          document.dispatchEvent(
            new CustomEvent("YZold", {
              detail: "devices_updated"
            })
          );
        }
      },
      onclose: e => {
        window.localStorage.removeItem("core-init")
        if (window.localStorage.getItem('wls-newbase') !== '1') {
          document.dispatchEvent(
            new CustomEvent("disconnected", {
              detail: {
                isDisconnected: true
              }
            })
          );
        }
      },
    });
    return _ws;
  }
  return;
}
const ws = !window.localStorage.getItem('wls-newbase') && createSocket();
export default ws;
export const WsContext = React.createContext(ws);

export const HandleWs = () => {
  const { pathname } = useLocation();
  const virtuals = useStore((state) => state.virtuals);
  const pixelGraphs = useStore((state) => state.pixelGraphs);
  const setPixelGraphs = useStore((state) => state.setPixelGraphs);
  const graphs = useStore((state) => state.graphs);
  const [wsReady, setWsReady] = useState(false);
  const [wasDisconnected, setWasDisconnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  useLayoutEffect(() => {
    if (!(pathname.startsWith("/Devices") || pathname.startsWith("/device"))) {
      setPixelGraphs([]);
    }
  }, [pathname]);

  useLayoutEffect(() => {
    if (!graphs) {
      setPixelGraphs([]);
    }
  }, [graphs]);

  useEffect(() => {
    const handleWsReady = (e) => {
      setWsReady(e.detail); // Cập nhật wsReady khi kết nối WebSocket sẵn sàng
    };

    document.addEventListener('wsReady', handleWsReady);

    return () => {
      document.removeEventListener('wsReady', handleWsReady);
    };
  }, []);

  useEffect(() => {
    if (pixelGraphs.length > 0 && wsReady) {
      pixelGraphs.forEach((d, i) => {
        const request = {
          event_filter: {
            vis_id: d,
            is_device: !!virtuals[d]?.is_device,
          },
          event_type: "visualisation_update",
          id: i,
          type: "subscribe_event",
        };
        ws.send(JSON.stringify(++request.id && request));
      });

      return () => {
        pixelGraphs.forEach((d, i) => {
          const request = {
            id: i,
            type: "unsubscribe_event",
            event_type: "visualisation_update",
          };
          ws.send(JSON.stringify(++request.id && request));
        });
      };
    }
  }, [wsReady, pixelGraphs]);

  useEffect(() => {
    const handleDisconnected = (e) => {
      if (e.detail.isDisconnected) {
        setWasDisconnected(true);
        setIsReconnecting(true);
      } else if (wasDisconnected) {
        setIsReconnecting(false);
        window.location.reload();
      }
    };

    document.addEventListener('disconnected', handleDisconnected);

    return () => {
      document.removeEventListener('disconnected', handleDisconnected);
    };
  }, [wasDisconnected]);

  return (
    <>
      {isReconnecting && (
        <div style={{
          position: 'fixed',
          bottom: '100px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '10px 20px',
          backgroundColor: '#ffcc00',
          color: '#000',
          borderRadius: '5px',
          zIndex: 1000,
          textAlign: 'center',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
        }}>
          Đang kết nối lại...
        </div>
      )}
    </>
  );
};