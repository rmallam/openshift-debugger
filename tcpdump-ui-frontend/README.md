# TCPDump/Ncat UI Frontend

This is a minimal static HTML/JS frontend for the TCPDump/Ncat UI solution.

## Usage

1. **Serve the UI:**
   - You can serve `index.html` with any static web server (nginx, httpd, etc).
   - Or, use the provided deployment.yaml to serve via nginx in OpenShift (see below).

2. **ConfigMap for OpenShift:**
   - To serve the UI from a pod, create a ConfigMap with the base64-encoded `index.html` and mount it to `/usr/share/nginx/html` in the nginx container.
   - The provided `deployment.yaml` shows how to do this.

3. **Access:**
   - The UI will call the backend API endpoints (e.g., `/tcpdump`, `/ncat`).
   - Make sure the backend is accessible from the frontend pod (same namespace or via Route).

4. **Security:**
   - Protect the Route with OpenShift OAuth or network policies as needed.

---

**Edit `index.html` to customize the UI or add more validation.**
