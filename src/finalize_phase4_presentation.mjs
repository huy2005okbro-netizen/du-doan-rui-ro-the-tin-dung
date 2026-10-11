import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { finalizePresentation } from "file:///C:/Users/trand/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations/container_tools/artifact_tool_utils.mjs";

const root = process.cwd();
const out = path.join(root, "deliverables");
const staging = path.join(root, ".codex-finalizer");
await fs.mkdir(staging, {recursive:true});
const finalPath = path.join(out, "Project_08_trinh_bay.pptx");
const result = await finalizePresentation({
  explicitTotalSlideCount: 11,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir: root,
  candidatePath: path.join(out, "Project_08_trinh_bay_draft.pptx"),
  finalPath,
  pythonExecutable: "C:\\Users\\trand\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe",
  integrityValidatorPath: "C:\\Users\\trand\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1007.11041\\skills\\presentations\\container_tools\\inspect_presentation_package_integrity.py",
  layoutValidatorPath: "C:\\Users\\trand\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1007.11041\\skills\\presentations\\container_tools\\inspect_presentation_layout_geometry.py",
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"],
  fontPolicy: {basis:"design", families:["Arial"], scriptFonts:["Arial"]},
  verifyArtifactToolImport: true,
  receiptPath: path.join(staging, "Project_08_trinh_bay.validation.json"),
});
console.log(JSON.stringify(result));
