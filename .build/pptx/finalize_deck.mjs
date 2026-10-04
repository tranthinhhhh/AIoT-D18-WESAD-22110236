import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const workspaceDir = "D:/TriTueNhanTaoIOT/Cuối Kỳ";
const skillDir = "C:/Users/THINH 9A9/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const buildDir = path.join(workspaceDir, ".build/pptx");
const candidatePath = path.join(buildDir, "candidate.pptx");
const finalPath = process.env.FINAL_PPTX
  ? path.resolve(process.env.FINAL_PPTX)
  : path.join(workspaceDir, "submission", "TranTienThinh_final.pptx");
const pythonExecutable = "C:/Users/THINH 9A9/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const stagingDir = path.join(buildDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });

const requirements = {
  workspaceDir,
  candidatePath,
  finalPath,
  explicitTotalSlideCount: 11,
  requiredNativeTableOwnerSlides: [5, 9],
  requiredNativeChartOwnerSlides: [6, 7, 10],
  requiredEmbeddedWorkbookChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
};
const result = await finalizePresentation({
  ...requirements,
  pythonExecutable,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide", "5",
    "--require-native-table-slide", "9",
  ],
  fontPolicy: { basis: "design", families: ["Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "TranTienThinh_final.pptx.validation.json"),
});
console.log(JSON.stringify(result, null, 2));
