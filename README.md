# AegisNet AI - AI-Powered Cloud Security Platform

AegisNet AI is a comprehensive cloud security platform that leverages Machine Learning (Isolation Forests + Random Forests) to detect, correlate, and visualize adversarial attacks in real-time. It features an automated end-to-end simulation framework to validate correlation logic, MITRE ATT&CK tactic mappings, and dynamic threat topologies.

## Architecture

*   **Frontend**: React + TypeScript + Vite + TailwindCSS. Uses WebSockets for real-time live threat map updates.
*   **Backend API**: FastAPI (Python). Handles ML correlation, topology generation, and WebSocket broadcasting.
*   **Machine Learning Consumer**: Async Python worker reading telemetry from Redis streams, performing ML inference, and passing alerts to the Correlation Engine.
*   **Telemetry Worker**: Zeek log consumer pushing raw network flows to Redis.
*   **Databases**: 
    *   **MongoDB**: Persistent storage for alerts, incidents, and topology snapshots.
    *   **Redis**: High-speed message broker for telemetry streams and ML alerts.
*   **Adversarial Simulator**: Automated mock attack generator replicating realistic Kill Chains (Reconnaissance -> Brute Force -> Web Exploit -> Lateral Movement -> Honeypot).

---

## Prerequisites

Before running the project, ensure you have the following installed:
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
*   [Node.js (v18+)](https://nodejs.org/) (for running the frontend locally)
*   Python 3.10+ (if you wish to run backend scripts locally without Docker)

---

## 🚀 Getting Started

### 1. Environment Configuration

Clone the repository and set up your environment variables. A template is provided in `.env.example`.

```bash
# Copy the example environment file
cp .env.example .env
```
*(Ensure that `MONGO_USER` and `MONGO_PASSWORD` in your `.env` are set correctly, as the workers rely on these to authenticate.)*

### 2. Start the Backend Infrastructure (Docker)

The entire backend (API, ML Consumer, Telemetry, MongoDB, Redis) is containerized and orchestrated via Docker Compose.

```bash
# Build and start all backend services in detached mode
docker compose up --build -d

# Verify all services are running and healthy
docker compose ps
```

*The FastAPI Swagger UI will be available at: http://localhost:8000/docs*

### 3. Start the Frontend Application

The frontend is a React application that needs to be run separately using `npm`.

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

*The frontend dashboard will be available at: http://localhost:5173*

---

## ⚔️ Running the Adversarial Simulator

To test the system and watch the live threat map populate, you can run the built-in Adversarial Attack Simulator. 

**IMPORTANT:** The simulator interacts heavily with the internal Redis streams and ML consumer logic. Therefore, it **must be executed from inside the `aegis-api` Docker container**, rather than on your local host machine (to avoid `ModuleNotFoundError` or Redis connection issues).

Run the following command from your terminal:

```bash
docker exec aegis-api python -m app.simulator.run_simulator
```

**What this does:**
1. Generates benign background traffic.
2. Injects a 5-stage MITRE attack chain from an external IP:
   * **Discovery** (Port Scanning)
   * **Credential Access** (SSH Brute Force)
   * **Initial Access** (Web Exploitation)
   * **Lateral Movement** (Internal SMB/RDP Probing)
   * **Execution** (Honeypot Interaction)
3. The ML Consumer flags these flows and passes them to the Correlation Engine.
4. The Correlation Engine groups them into a single `CRITICAL` Incident.
5. The `SimulatorValidator` asserts that the Incident, MITRE tactics, and Topology nodes were successfully created in MongoDB.
6. The Frontend dashboard updates in real-time via WebSockets.

---

## Troubleshooting

*   **ModuleNotFoundError: No module named 'app' or 'redis'**
    *   *Cause:* You tried to run `python -m app.simulator...` on your host machine without installing the requirements or setting the `PYTHONPATH`.
    *   *Fix:* Always use `docker exec aegis-api ...` to run backend scripts.

*   **Database Authentication Errors (`pymongo.errors.InvalidURI`)**
    *   *Cause:* Special characters in your `.env` MongoDB password.
    *   *Fix:* The backend handles `urllib.parse.quote_plus` internally now, but ensure your `.env` is loaded correctly by Docker Compose. Rebuild the containers if you change the `.env` file (`docker compose up --build -d`).

*   **No Alerts Showing on Dashboard**
    *   *Fix:* Check the ML consumer logs to ensure it isn't crashing: `docker compose logs aegis-ml-consumer --tail 50`. Also ensure the frontend WebSocket is connecting successfully to `ws://localhost:8000`.