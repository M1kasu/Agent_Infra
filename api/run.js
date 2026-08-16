import { runOfficeOpsDemo } from "../demo/lib/runner.mjs";

export default function handler(request, response) {
  if (request.method !== "POST") {
    response.setHeader("Allow", "POST");
    return response.status(405).json({ ok: false, error: "METHOD_NOT_ALLOWED" });
  }

  try {
    const input = typeof request.body === "string" ? JSON.parse(request.body) : request.body ?? {};
    const run = runOfficeOpsDemo({ message: input.message, mode: input.mode });
    return response.status(200).json({
      ok: true,
      deployment: "vercel-stateless",
      note: "The full evidence package is returned in this response; Vercel does not persist local artifacts.",
      ...run
    });
  } catch (error) {
    return response.status(400).json({
      ok: false,
      error: "INVALID_DEMO_INPUT",
      message: error.message
    });
  }
}

