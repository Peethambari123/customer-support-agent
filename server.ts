import express from "express";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";

const app = express();
const PORT = 3000;

app.use(express.json());

// Spawn background Python agent daemon if not running
let pythonProcess: any = null;
function ensurePythonServer() {
  fetch("http://127.0.0.1:8001/health")
    .then((res) => res.json())
    .then((data) => {
      console.log("Python daemon verified healthy:", data);
    })
    .catch(() => {
      console.log("Starting Python API server on 127.0.0.1:8001...");
      pythonProcess = spawn("python3", ["-m", "src.api_server"], {
        cwd: process.cwd(),
        stdio: "inherit",
      });
      pythonProcess.on("exit", (code: number) => {
        console.log(`Python API server exited with code ${code}`);
      });
    });
}
ensurePythonServer();

// --- API Endpoints ---

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    brand: "AppleSupport",
    timestamp: new Date().toISOString(),
  });
});

app.get("/api/metrics", (req, res) => {
  const metricsPath = path.join(process.cwd(), "results", "metrics.json");
  if (fs.existsSync(metricsPath)) {
    const data = JSON.parse(fs.readFileSync(metricsPath, "utf-8"));
    res.json(data);
  } else {
    res.status(404).json({ error: "Metrics not found. Run evaluation first." });
  }
});

app.get("/api/failures", (req, res) => {
  const failurePath = path.join(process.cwd(), "results", "failure_analysis.json");
  if (fs.existsSync(failurePath)) {
    const data = JSON.parse(fs.readFileSync(failurePath, "utf-8"));
    res.json(data);
  } else {
    res.status(404).json({ error: "Failure analysis not found." });
  }
});

app.get("/api/intents", (req, res) => {
  const intentsPath = path.join(process.cwd(), "config", "intents.json");
  if (fs.existsSync(intentsPath)) {
    const data = JSON.parse(fs.readFileSync(intentsPath, "utf-8"));
    res.json(data);
  } else {
    res.status(404).json({ error: "Intents configuration not found." });
  }
});

app.get("/api/report", (req, res) => {
  const reportPath = path.join(process.cwd(), "report", "REPORT.md");
  if (fs.existsSync(reportPath)) {
    const content = fs.readFileSync(reportPath, "utf-8");
    res.json({ markdown: content });
  } else {
    res.status(404).json({ error: "Report not found." });
  }
});

app.get("/api/golden_samples", (req, res) => {
  const goldenPath = path.join(process.cwd(), "data", "golden_set.csv");
  if (!fs.existsSync(goldenPath)) {
    return res.status(404).json({ error: "Golden set not found." });
  }

  // Parse sample rows from CSV
  const content = fs.readFileSync(goldenPath, "utf-8");
  const lines = content.split("\n").filter((l) => l.trim().length > 0);
  const headers = lines[0].split(",");
  const samples = [];

  for (let i = 1; i < Math.min(lines.length, 35); i++) {
    const row = lines[i];
    // CSV parser for simple quoted values
    const parts: string[] = [];
    let inQuote = false;
    let current = "";
    for (const char of row) {
      if (char === '"') {
        inQuote = !inQuote;
      } else if (char === "," && !inQuote) {
        parts.push(current);
        current = "";
      } else {
        current += char;
      }
    }
    parts.push(current);

    if (parts.length >= 4) {
      samples.push({
        id: parts[0]?.trim(),
        customer_message: parts[1]?.trim().replace(/^"|"$/g, ""),
        ground_truth_intent: parts[2]?.trim(),
        historical_agent_reply: parts[3]?.trim().replace(/^"|"$/g, ""),
        ground_truth_escalate: parts[4]?.trim() === "1",
      });
    }
  }

  res.json(samples);
});

app.post("/api/support/process", async (req, res) => {
  const { message } = req.body;
  if (!message || typeof message !== "string") {
    return res.status(400).json({ error: "Parameter 'message' is required." });
  }

  // Try Python HTTP Daemon
  try {
    const pyResp = await fetch("http://127.0.0.1:8001/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (pyResp.ok) {
      const data = await pyResp.json();
      return res.json(data);
    }
  } catch (err) {
    console.warn("Python HTTP daemon unreachable, falling back to process CLI:", err);
  }

  // Fallback to direct Python subprocess
  const child = spawn("python3", ["-m", "src.agent", "--message", message, "--json"], {
    cwd: process.cwd(),
  });

  let stdout = "";
  let stderr = "";

  child.stdout.on("data", (d) => {
    stdout += d.toString();
  });
  child.stderr.on("data", (d) => {
    stderr += d.toString();
  });

  child.on("close", (code) => {
    if (code === 0 && stdout.trim()) {
      try {
        const parsed = JSON.parse(stdout.trim());
        return res.json(parsed);
      } catch (e) {
        return res.status(500).json({ error: "Failed to parse Python JSON output", raw: stdout });
      }
    }
    return res.status(500).json({ error: "Agent process failed", stderr, code });
  });
});

// Vite Middleware & Static Serving
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Support Agent application running at http://0.0.0.0:${PORT}`);
  });
}

startServer();
