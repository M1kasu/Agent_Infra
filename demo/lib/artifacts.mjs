import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

export async function writeRunArtifacts(run, outputRoot = "artifacts/runs") {
  const runDirectory = path.resolve(outputRoot, run.result.run_id);
  await mkdir(runDirectory, { recursive: true });

  const writes = Object.entries({
    ...run.artifacts,
    result: run.result
  }).map(([name, value]) =>
    writeFile(
      path.join(runDirectory, `${name}.json`),
      `${JSON.stringify(value, null, 2)}\n`,
      "utf8"
    )
  );
  await Promise.all(writes);
  return runDirectory;
}

