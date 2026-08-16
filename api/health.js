export default function handler(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return response.status(405).json({ ok: false, error: "METHOD_NOT_ALLOWED" });
  }
  return response.status(200).json({
    ok: true,
    service: "officeops-demo",
    deployment: "vercel"
  });
}

