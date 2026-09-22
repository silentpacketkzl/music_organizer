import express from "express";
import path from "path";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";
import fs from "fs";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // Check system status & tools
  app.get("/api/status", (req, res) => {
    const testLibraryExists = fs.existsSync("/tmp/music_test");
    let testFileCount = 0;
    if (testLibraryExists) {
      try {
        const countFiles = (dir: string): number => {
          let count = 0;
          const entries = fs.readdirSync(dir, { withFileTypes: true });
          for (const entry of entries) {
            const full = path.join(dir, entry.name);
            if (entry.isDirectory()) {
              count += countFiles(full);
            } else {
              count++;
            }
          }
          return count;
        };
        testFileCount = countFiles("/tmp/music_test");
      } catch (err) {
        testFileCount = 0;
      }
    }

    res.json({
      tools: {
        fpcalc: fs.existsSync("/usr/bin/fpcalc"),
        ffmpeg: fs.existsSync("/usr/bin/ffmpeg"),
        python: fs.existsSync("/usr/bin/python3"),
        openaiKeyConfigured: Boolean(process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY.trim().length > 5)
      },
      testLibrary: {
        path: "/tmp/music_test",
        exists: testLibraryExists,
        fileCount: testFileCount
      }
    });
  });

  // Generate synthetic test library
  app.post("/api/generate-mock", (req, res) => {
    const proc = spawn("python3", ["scripts/generate_test_library.py"], {
      cwd: process.cwd(),
      env: process.env
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => { stdout += data.toString(); });
    proc.stderr.on("data", (data) => { stderr += data.toString(); });

    proc.on("close", (code) => {
      if (code === 0) {
        res.json({ success: true, message: "Generated synthetic library in /tmp/music_test", output: stdout });
      } else {
        res.status(500).json({ success: false, error: stderr || stdout });
      }
    });
  });

  // Execute scan / apply via main.py --json
  app.post("/api/scan", (req, res) => {
    const { scanPath = "/tmp/music_test", apply = false, trashDir = "" } = req.body;

    const args = ["main.py", "--scan", scanPath, "--json"];
    if (apply) {
      args.push("--apply");
    }
    if (trashDir && trashDir.trim()) {
      args.push("--trash-dir", trashDir.trim());
    }

    const proc = spawn("python3", args, {
      cwd: process.cwd(),
      env: process.env
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => { stdout += data.toString(); });
    proc.stderr.on("data", (data) => { stderr += data.toString(); });

    proc.on("close", (code) => {
      try {
        const jsonResponse = JSON.parse(stdout.trim());
        res.json(jsonResponse);
      } catch (e) {
        res.status(500).json({
          error: "Failed to parse JSON response from scanner",
          rawStdout: stdout,
          rawStderr: stderr,
          exitCode: code
        });
      }
    });
  });

  // Undo last organization session
  app.post("/api/undo", (req, res) => {
    const proc = spawn("python3", ["main.py", "--undo", "--json"], {
      cwd: process.cwd(),
      env: process.env
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => { stdout += data.toString(); });
    proc.stderr.on("data", (data) => { stderr += data.toString(); });

    proc.on("close", (code) => {
      try {
        const jsonResponse = JSON.parse(stdout.trim());
        res.json(jsonResponse);
      } catch (e) {
        res.json({ success: code === 0, rawOutput: stdout, error: stderr });
      }
    });
  });

  // Quick live transliteration test
  app.post("/api/transliterate", (req, res) => {
    const { text } = req.body;
    if (!text) {
      return res.status(400).json({ error: "Text is required" });
    }

    const pyCode = `
import json
from music_cleaner.transliterate import TransliterationEngine
from music_cleaner.db import Database
db = Database("cache.db")
engine = TransliterationEngine(db=db)
result = engine.transliterate_text(${JSON.stringify(text)})
print(json.dumps({"input": ${JSON.stringify(text)}, "output": result}))
`;

    const proc = spawn("python3", ["-c", pyCode], {
      cwd: process.cwd(),
      env: process.env
    });

    let stdout = "";
    proc.stdout.on("data", (data) => { stdout += data.toString(); });
    proc.on("close", (code) => {
      try {
        res.json(JSON.parse(stdout.trim()));
      } catch (e) {
        res.status(500).json({ error: "Transliteration failed", output: stdout });
      }
    });
  });

  // Vite Middleware Setup
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
    console.log(`🎵 Burmese Music Cleaner Server listening at http://0.0.0.0:${PORT}`);
  });
}

startServer();
