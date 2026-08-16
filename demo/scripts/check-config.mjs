import { access, readFile } from "node:fs/promises";
import path from "node:path";

import goldenCases from "../../scenarios/access-incident/golden-cases.json" with { type: "json" };
import manifest from "../../scenarios/access-incident/manifest.json" with { type: "json" };
import { runOfficeOpsDemo } from "../lib/runner.mjs";

const repositoryRoot = path.resolve(import.meta.dirname, "../..");

async function requireFile(relativePath) {
  await access(path.join(repositoryRoot, relativePath));
  return relativePath;
}

const requiredJson = [
  "package.json",
  "vercel.json",
  "contracts/domain/work-item.schema.json",
  "contracts/messages/handoff-envelope.schema.json",
  "contracts/tools/tool-call.schema.json",
  "scenarios/access-incident/manifest.json",
  "scenarios/access-incident/fixture.json",
  "scenarios/access-incident/policy.json",
  "scenarios/access-incident/verification-spec.json",
  "scenarios/access-incident/golden-cases.json",
  "examples/evidence/g01-run-report.json",
  "examples/evidence/g07-fake-success-run-report.json"
];

for (const relativePath of requiredJson) {
  const content = await readFile(path.join(repositoryRoot, relativePath), "utf8");
  JSON.parse(content);
}

for (const skill of manifest.skills) {
  await requireFile(`skills/${skill}/SKILL.md`);
}

const teamYaml = await readFile(path.join(repositoryRoot, "agentteams/officeops-demo.yaml"), "utf8");
for (const agent of [
  "officeops-lead",
  "officeops-context",
  "officeops-diagnosis",
  "officeops-execution",
  "officeops-verification"
]) {
  if (!teamYaml.includes(`name: ${agent}`)) {
    throw new Error(`AgentTeams resource is missing ${agent}`);
  }
}
if (!teamYaml.includes("role: team_leader")) {
  throw new Error("AgentTeams Team must declare exactly one team leader");
}

for (const goldenCase of goldenCases.cases) {
  const run = runOfficeOpsDemo({ mode: goldenCase.mode, runId: goldenCase.case_id.toLowerCase() });
  if (run.result.status !== goldenCase.expected_status) {
    throw new Error(`${goldenCase.case_id}: expected ${goldenCase.expected_status}, got ${run.result.status}`);
  }
  if (run.result.root_cause !== goldenCase.expected_root_cause) {
    throw new Error(`${goldenCase.case_id}: unexpected root cause ${run.result.root_cause}`);
  }
  if (run.result.verification_status !== goldenCase.expected_verification) {
    throw new Error(`${goldenCase.case_id}: unexpected verification ${run.result.verification_status}`);
  }
}

console.log(`config-check: OK (${requiredJson.length} JSON files, ${manifest.skills.length} Skills, ${goldenCases.cases.length} Golden Cases)`);
