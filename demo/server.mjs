import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { writeRunArtifacts } from "./lib/artifacts.mjs";
import { createLogicalClock } from "./lib/clock.mjs";
import { GatewayError, MockToolGateway } from "./lib/mock-gateway.mjs";
import { runOfficeOpsDemo } from "./lib/runner.mjs";

const sourceDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(sourceDirectory, "..");
const publicRoot = path.join(repositoryRoot, "public");
const completedRuns = new Map();
const sandboxes = new Map();

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

function json(response, statusCode, payload) {
  const body = JSON.stringify(payload, null, 2);
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, X-Agent-Role"
  });
  response.end(body);
}

async function readJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 64 * 1024) {
      throw new GatewayError("PAYLOAD_TOO_LARGE", "request body exceeds 64 KiB", 413);
    }
    chunks.push(chunk);
  }
  if (chunks.length === 0) {
    return {};
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

async function serveStatic(pathname, response) {
  const requested = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  const filePath = path.resolve(publicRoot, requested);
  if (!filePath.startsWith(`${publicRoot}${path.sep}`) && filePath !== publicRoot) {
    json(response, 403, { ok: false, error: "invalid static path" });
    return;
  }
  try {
    const content = await readFile(filePath);
    const contentType = contentTypes[path.extname(filePath)] ?? "application/octet-stream";
    response.writeHead(200, {
      "Content-Type": contentType,
      "Content-Length": content.length,
      "Cache-Control": filePath.endsWith("index.html") ? "no-cache" : "public, max-age=3600",
      "X-Content-Type-Options": "nosniff"
    });
    response.end(content);
  } catch (error) {
    if (error.code === "ENOENT") {
      json(response, 404, { ok: false, error: "not found" });
      return;
    }
    throw error;
  }
}

async function handleToolRequest({ request, response, pathname }) {
  const [, prefix, encodedRunId, ...operationParts] = pathname.split("/");
  if (prefix !== "tools" || !encodedRunId || operationParts.length === 0) {
    return false;
  }
  const runId = decodeURIComponent(encodedRunId);
  const operation = operationParts.map(decodeURIComponent).join("/");
  const payload = await readJson(request);

  if (operation === "sandbox.reset") {
    const mode = payload.mode ?? "normal";
    sandboxes.set(runId, new MockToolGateway({
      runId,
      mode,
      now: createLogicalClock(payload.clock_start)
    }));
    json(response, 200, { ok: true, run_id: runId, mode, status: "RESET" });
    return true;
  }

  const gateway = sandboxes.get(runId);
  if (!gateway) {
    throw new GatewayError(
      "SANDBOX_NOT_FOUND",
      `reset sandbox ${runId} before calling tools`,
      404
    );
  }
  const actor = request.headers["x-agent-role"] ?? payload.actor;
  const result = gateway.call({
    actor,
    operation,
    targetRef: payload.target_ref ?? null,
    parameters: payload.parameters ?? {},
    authorization: payload.authorization ?? {}
  });
  json(response, 200, { ok: true, result });
  return true;
}

export function createDemoServer() {
  return http.createServer(async (request, response) => {
    const url = new URL(request.url, "http://localhost");
    try {
      if (request.method === "OPTIONS") {
        response.writeHead(204, {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "Content-Type, X-Agent-Role",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        });
        response.end();
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/health") {
        json(response, 200, {
          ok: true,
          service: "officeops-demo",
          runtime: process.version,
          active_sandboxes: sandboxes.size
        });
        return;
      }

      if (request.method === "POST" && ["/api/run", "/api/runs"].includes(url.pathname)) {
        const input = await readJson(request);
        const run = runOfficeOpsDemo({ message: input.message, mode: input.mode });
        const artifactDirectory = await writeRunArtifacts(run);
        completedRuns.set(run.result.run_id, run);
        json(response, 200, {
          ok: true,
          deployment: "local-stateful",
          artifact_directory: artifactDirectory,
          ...run
        });
        return;
      }

      const runMatch = url.pathname.match(/^\/api\/runs\/([^/]+)$/);
      if (request.method === "GET" && runMatch) {
        const run = completedRuns.get(decodeURIComponent(runMatch[1]));
        if (!run) {
          json(response, 404, { ok: false, error: "run not found" });
          return;
        }
        json(response, 200, { ok: true, ...run });
        return;
      }

      if (request.method === "POST" && url.pathname.startsWith("/tools/")) {
        await handleToolRequest({ request, response, pathname: url.pathname });
        return;
      }

      if (request.method === "GET") {
        await serveStatic(url.pathname, response);
        return;
      }

      json(response, 404, { ok: false, error: "route not found" });
    } catch (error) {
      const statusCode = error.statusCode ?? 500;
      json(response, statusCode, {
        ok: false,
        error: error.code ?? "INTERNAL_ERROR",
        message: error.message
      });
    }
  });
}

const executedDirectly = process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (executedDirectly) {
  const port = Number(process.env.PORT ?? 18110);
  const host = process.env.HOST ?? "0.0.0.0";
  const server = createDemoServer();
  server.listen(port, host, () => {
    console.log(`OfficeOps demo listening on http://localhost:${port}`);
    console.log(`AgentTeams tool gateway: http://host.docker.internal:${port}/tools/{run_id}/{operation}`);
  });
}

