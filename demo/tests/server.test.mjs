import assert from "node:assert/strict";
import test from "node:test";

import { createDemoServer } from "../server.mjs";

async function withServer(callback) {
  const server = createDemoServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  try {
    await callback(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
}

test("local API returns a complete auditable run", async () => {
  await withServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "normal", message: "Docs 文档打不开，页面提示没有权限。" })
    });
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.ok, true);
    assert.equal(payload.result.status, "COMPLETED");
    assert.ok(payload.artifacts.trace.length > 10);
  });
});

test("AgentTeams-style HTTP gateway enforces role allowlists", async () => {
  await withServer(async (baseUrl) => {
    const reset = await fetch(`${baseUrl}/tools/agentteams-test/sandbox.reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "normal" })
    });
    assert.equal(reset.status, 200);

    const denied = await fetch(`${baseUrl}/tools/agentteams-test/iam.unlock_account`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Agent-Role": "context-agent"
      },
      body: JSON.stringify({ target_ref: "iam://corp/alice" })
    });
    assert.equal(denied.status, 403);
    const payload = await denied.json();
    assert.equal(payload.error, "TOOL_FORBIDDEN");
  });
});

