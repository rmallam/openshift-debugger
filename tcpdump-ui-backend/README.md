# TCPDump/Ncat UI Backend

This FastAPI backend exposes `/tcpdump` and `/ncat` endpoints to securely run those commands in the `node-debug` pod in your namespace.

## Usage

1. **Build and deploy the backend:**
   ```sh
   podman build -t tcpdump-ui-backend:latest .
   podman run -e POD_NAMESPACE=<your-namespace> -e DEBUG_POD=node-debug -p 8080:8080 tcpdump-ui-backend:latest
   ```
   Or deploy as a pod/service in OpenShift (set env vars as needed).

2. **Frontend:**
   - Serve `../tcpdump-ui-frontend/index.html` via any static web server (or copy into a Route/ConfigMap for OpenShift).
   - The UI will call the backend endpoints.

3. **Security:**
   - Only allows specific tcpdump/ncat arguments.
   - Backend must run with a service account that can `pods/exec` in the namespace.

4. **Integration:**
   - Expose the backend via a Service/Route for your devs.
   - Optionally add OpenShift OAuth or other authentication.

---

**Edit `main.py` to further restrict or audit commands as needed.**
