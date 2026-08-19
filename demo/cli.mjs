import { parseArgs } from "node:util";

import { writeRunArtifacts } from "./lib/artifacts.mjs";
import { DEFAULT_MESSAGE, runOfficeOpsDemo } from "./lib/runner.mjs";

const { values } = parseArgs({
  options: {
    mode: { type: "string", default: "normal" },
    message: { type: "string", default: DEFAULT_MESSAGE },
    output: { type: "string", default: "artifacts/runs" },
    "no-write": { type: "boolean", default: false }
  }
});

const run = runOfficeOpsDemo({ message: values.message, mode: values.mode });
let artifactDirectory = null;
if (!values["no-write"]) {
  artifactDirectory = await writeRunArtifacts(run, values.output);
}

console.log(JSON.stringify({
  ...run.result,
  artifact_directory: artifactDirectory
}, null, 2));

