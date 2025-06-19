# NBN Debugger: OpenShift TCPDump/Ncat UI

## Overview
This project provides a secure, OpenShift-native web UI for running `tcpdump` and `ncat` (netcat) on worker nodes for troubleshooting and log collection. It is designed for application teams to capture network traffic without SSH or direct pod access, using OpenShift RBAC and SCC for security.

## Components
- **tcpdump-ui-backend**: FastAPI backend that securely runs `tcpdump` and `ncat` in a privileged debug pod via Kubernetes API.
- **tcpdump-ui-frontend**: Minimal HTML/JS frontend served by nginx, providing a web UI for live tcpdump/ncat output, stop, and export features.
- **node-debug-pod.yaml**: YAML for deploying the privileged debug pod, service account, RBAC, and required ClusterRole/ClusterRoleBinding.
- **Custom SCC**: (See `scc-tcpdump-debug.yaml`) for pod security context.

## Prerequisites
- OpenShift cluster admin access
- `oc` CLI
- Permissions to create pods, roles, and SCCs in your target namespace (e.g., `debugger`)

## Quick Start

### 1. Deploy the Debug Pod and RBAC
```sh
oc apply -f node-debug-pod.yaml
```
This creates:
- The `node-debug` privileged pod (used to run tcpdump/ncat)
- Service account and all required RBAC (including ClusterRole to get node IP)

### 2. Deploy the Backend
```sh
cd tcpdump-ui-backend
oc apply -f deployment.yaml
```
- The backend will run as a service in the same namespace (e.g., `debugger`).
- It must have access to the debug pod and permission to exec into it.

### 3. Deploy the Frontend
```sh
cd ../tcpdump-ui-frontend
oc apply -f configmap.yaml
oc apply -f nginx-conf-configmap.yaml
oc apply -f deployment.yaml
```
- The frontend is served by nginx and proxies API/WebSocket calls to the backend.

### 4. Expose the UI
- A Route is included in the frontend deployment. Access the UI via the OpenShift route URL.

## Usage
- Enter tcpdump or ncat arguments in the UI and click **Run**.
- Live output will stream in the browser.
- Use **Stop** to end capture, **Export** to download logs, and **Clear** to reset the output.
- The node IP where the debug pod is running is displayed at the top of the output.

## Security
- Only the allowed arguments for `tcpdump` and `ncat` are permitted (see backend code).
- The backend runs with a service account and custom SCC for least privilege.
- No SSH or direct pod access is required.

## Troubleshooting
- If the node IP does not appear, ensure the ClusterRole/ClusterRoleBinding for `nodes` is applied and the service account is correct.
- If WebSocket errors appear, check nginx config and backend pod logs.

## Cleanup
To remove all resources:
```sh
oc delete -f node-debug-pod.yaml
cd tcpdump-ui-backend && oc delete -f deployment.yaml
cd ../tcpdump-ui-frontend && oc delete -f deployment.yaml && oc delete -f configmap.yaml && oc delete -f nginx-conf-configmap.yaml
```

## Customization
- You can further restrict allowed arguments or add authentication in the backend as needed.
- See the backend and frontend README files for more details.

---
For questions or improvements, please open an issue or PR.
