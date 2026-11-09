# Frontend development on Windows 11

Prerequisites: Node.js 20+ and npm. Start the FastAPI backend separately as documented in WINDOWS_SETUP.md.

From the repository root in PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The Vite development server proxies /api to FastAPI on port 8000. Run `npm run build` to check TypeScript and produce a production bundle.

The first interface intentionally shows a **deterministic analytical estimate**, not live network telemetry. Its topology is a fixed five-node demonstration. Future milestones add topology editing, packet emulation, ns-3 integration, fault localization, and bounded remediation.
