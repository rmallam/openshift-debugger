

from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config, stream
import os
import asyncio
import threading
import logging
from typing import List

NAMESPACE = os.environ.get("POD_NAMESPACE", "default")
DEBUG_POD = os.environ.get("DEBUG_POD", "node-debug")


# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tcpdump-ui-backend")

# FastAPI app must be defined before using it
app = FastAPI()

# Allow CORS for local UI testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions per client (in-memory, not persistent)
tcpdump_sessions = {}

class TcpdumpSession:
    def __init__(self):
        self.buffer = []
        self.process = None
        self.running = False
        self.node_ip = None

    def start(self, v1, pod, namespace, command):
        self.running = True
        def run():
            try:
                resp = stream.stream(
                    v1.connect_get_namespaced_pod_exec,
                    pod, namespace,
                    command=command,
                    stderr=True, stdin=False, stdout=True, tty=False,
                    _preload_content=False
                )
                while self.running:
                    if resp.is_open():
                        resp.update(timeout=1)
                        if resp.peek_stdout():
                            out = resp.read_stdout()
                            self.buffer.append(out)
                        if resp.peek_stderr():
                            err = resp.read_stderr()
                            self.buffer.append(err)
                    else:
                        break
                resp.close()
            except Exception as e:
                self.buffer.append(f"[ERROR] {e}\n")
        self.thread = threading.Thread(target=run)
        self.thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)

    def get_output(self):
        return ''.join(self.buffer)

@app.websocket("/ws/tcpdump")
async def websocket_tcpdump(ws: WebSocket):
    logger.info("WebSocket /ws/tcpdump connection attempt")
    await ws.accept()
    session = TcpdumpSession()
    tcpdump_sessions[id(ws)] = session
    try:
        logger.info("Waiting for args from client...")
        data = await ws.receive_json()
        args = data.get("args", "")
        logger.info(f"Received args: {args}")
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        # Get the node IP where the debug pod is running
        pod = v1.read_namespaced_pod(DEBUG_POD, NAMESPACE)
        node_name = pod.spec.node_name
        node_ip = None
        if node_name:
            node = v1.read_node(node_name)
            for addr in node.status.addresses:
                if addr.type == "InternalIP":
                    node_ip = addr.address
                    break
        session.node_ip = node_ip
        command = ["tcpdump"] + validate_tcpdump_args(args)
        logger.info(f"Starting tcpdump with command: {command}")
        session.start(v1, DEBUG_POD, NAMESPACE, command)
        sent = 0
        # Send node IP to client as soon as available
        await ws.send_text(f"[Node IP: {node_ip or 'unknown'}]\n")
        while session.running:
            await asyncio.sleep(1)
            output = session.get_output()
            if len(output) > sent:
                await ws.send_text(output[sent:])
                sent = len(output)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        session.stop()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws.send_text(f"[ERROR] {e}\n")
        session.stop()
    finally:
        logger.info("WebSocket session cleanup")
        tcpdump_sessions.pop(id(ws), None)

@app.get("/tcpdump/export")
def export_tcpdump(session_id: int):
    session = tcpdump_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"output": session.get_output()}

def validate_tcpdump_args(args: str):
    # Only allow safe tcpdump args (no shell, no file output, etc.)
    allowed = ["-i", "-c", "port", "host", "net", "tcp", "udp", "icmp"]
    tokens = args.split()
    for t in tokens:
        if t.startswith("-") and t not in allowed:
            raise HTTPException(status_code=400, detail=f"Disallowed tcpdump arg: {t}")
    return tokens

def validate_ncat_args(args: str):
    # Only allow safe ncat args (no shell, no exec, no file)
    allowed = ["-v", "-z", "-u", "-l", "-p", "-w", "--recv-only", "--send-only"]
    tokens = args.split()
    for t in tokens:
        if t.startswith("-") and t not in allowed:
            raise HTTPException(status_code=400, detail=f"Disallowed ncat arg: {t}")
    return tokens

# (Legacy /tcpdump endpoint remains for compatibility)

@app.get("/ncat")
def run_ncat(args: str = Query("")):
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    # Always add -v as the first argument for ncat
    command = ["ncat", "-v"] + validate_ncat_args(args)
    try:
        resp = stream.stream(
            v1.connect_get_namespaced_pod_exec,
            DEBUG_POD, NAMESPACE,
            command=command,
            stderr=True, stdin=False, stdout=True, tty=False
        )
        return {"output": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
