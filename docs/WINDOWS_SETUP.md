# Windows 11 setup — first runnable milestone

Prerequisites: Git, Python 3.11+ on Windows. WSL2/Ubuntu and Node.js are **not required for this analytical baseline**; they will be needed for future simulator/frontend milestones.

In **PowerShell**:

```powershell
git clone https://github.com/aliahmedsleem/Intelligent-Network-Fault-Diagnosis.git
cd Intelligent-Network-Fault-Diagnosis\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs (interactive REST UI) and http://127.0.0.1:8000/api/health. Use `examples/three-site.json` as the request body for `POST /api/experiments/link-fault`.

If PowerShell prevents activation, use `.\.venv\Scripts\python.exe -m pytest -q` and `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` without activation.

## Interpretation
All results in this milestone are **analytical estimates**, not measurements from virtual traffic. Mininet, ns-3, physical link models, intelligent diagnosis and remediation are forthcoming, and must be independently validated before they can be called operational.
