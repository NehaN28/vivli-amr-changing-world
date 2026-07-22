import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/workspace/scratch/6f657a5e2035";
const repo = path.join(root, "amr-changing-world");
const inputDir = path.join(repo, "outputs", "phase4_analysis");
const outputDir = path.join(root, "outputs", "phase4");
const previewDir = path.join(root, "work", "phase4_workbook_previews");
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

function parseCsv(text) {
  const rows = []; let row = []; let field = ""; let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += ch;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows.map((r, ri) => r.map((value) => {
    if (ri === 0 || value === "") return value;
    if (value === "True") return true;
    if (value === "False") return false;
    const number = Number(value);
    return Number.isFinite(number) ? number : value;
  }));
}

const sourceSpecs = [
  ["Main Models", "main_conflict_models.csv"],
  ["Standardised Trends", "standardised_trends.csv"],
  ["Standardised AMR", "standardised_amr.csv"],
  ["Sensitivity", "sensitivity_models.csv"],
  ["Diagnostics", "model_diagnostics.csv"],
  ["Standardisation QA", "standardisation_diagnostics.csv"],
  ["Calibration", "standardisation_calibration.csv"],
  ["MIC Models", "mic_models.csv"],
  ["MIC Country-Year", "mic_country_year.csv"],
  ["Event Trajectories", "exploratory_event_trajectories.csv"],
];

const wb = Workbook.create();
const summary = wb.worksheets.add("Summary");
const loaded = new Map();
for (const [sheetName, filename] of sourceSpecs) {
  const rows = parseCsv(await fs.readFile(path.join(inputDir, filename), "utf8"));
  loaded.set(sheetName, rows);
  const sheet = wb.worksheets.add(sheetName);
  if (rows.length) sheet.getRangeByIndexes(0, 0, rows.length, rows[0].length).values = rows;
}
const methods = wb.worksheets.add("Methods");

const C = { navy: "#275D7A", dark: "#24323F", paleBlue: "#DDEBF3", paleGray: "#F2F4F5",
  white: "#FFFFFF", green: "#D9EAD3", amber: "#FCE8B2", border: "#CCD4D9", muted: "#66727C" };

function title(sheet, range, text) {
  sheet.mergeCells(range); const r = sheet.getRange(range); r.values = [[text]];
  r.format.fill = C.navy; r.format.font = { bold: true, color: C.white, size: 16 };
  r.format.verticalAlignment = "center"; r.format.rowHeight = 34;
}
function header(range) {
  range.format.fill = C.navy; range.format.font = { bold: true, color: C.white, size: 9 };
  range.format.wrapText = true; range.format.verticalAlignment = "center";
  range.format.borders = { preset: "all", style: "thin", color: C.border }; range.format.rowHeight = 34;
}
function body(range) {
  range.format.font = { color: C.dark, size: 9 }; range.format.verticalAlignment = "center";
  range.format.borders = { insideHorizontal: { style: "thin", color: C.border } };
}
for (const sheet of wb.worksheets.items) sheet.showGridLines = false;

title(summary, "A1:M1", "Phase 4: Standardised AMR and Confirmatory Conflict Models");
summary.mergeCells("A3:M4");
summary.getRange("A3").values = [["CONFIRMATORY CONCLUSION  |  No prespecified endpoint showed a detectable preceding-year conflict association after Holm correction. Confidence intervals allow modest decreases or increases; this is not proof of zero effect."]];
summary.getRange("A3:M4").format = { fill: C.green, font: { bold: true, color: C.dark, size: 11 }, wrapText: true, verticalAlignment: "center" };

summary.getRange("A6:G6").values = [["Endpoint", "Isolates", "Countries", "OR per exposure doubling", "95% CI low", "95% CI high", "Holm p"]];
header(summary.getRange("A6:G6"));
for (let i = 0; i < 4; i += 1) {
  const dest = 7 + i; const src = 2 + i;
  summary.getRange(`A${dest}:G${dest}`).formulas = [[
    `='Main Models'!B${src}`, `='Main Models'!C${src}`, `='Main Models'!E${src}`,
    `='Main Models'!I${src}`, `='Main Models'!J${src}`, `='Main Models'!K${src}`, `='Main Models'!V${src}`,
  ]];
}
body(summary.getRange("A7:G10"));
summary.getRange("B7:C10").format.numberFormat = "#,##0";
summary.getRange("D7:F10").format.numberFormat = "0.000";
summary.getRange("G7:G10").format.numberFormat = "0.000";

summary.mergeCells("A13:G13"); summary.getRange("A13").values = [["Interpretation and locked decisions"]];
summary.getRange("A13:G13").format = { fill: C.paleBlue, font: { bold: true, color: C.navy, size: 11 } };
summary.getRange("A14:G20").values = [
  ["Exposure scale", "One unit = doubling of 1 + preceding-year political-violence events", null, null, null, null, null],
  ["Inference", "Country-clustered t inference; 9,999 wild-cluster score replications", null, null, null, null, null],
  ["Multiplicity", "Holm family-wise correction across four confirmatory coefficients", null, null, null, null, null],
  ["Standardisation", "Partially pooled country-year estimates at a common patient/specimen distribution", null, null, null, null, null],
  ["MIC analysis", "Boundary and one-dilution-outer substitutions; sensitivity only", null, null, null, null, null],
  ["Primary conclusion", "No detectable association; retain all null estimates and uncertainty", null, null, null, null, null],
  ["Next phase", "Proceed to prespecified secondary One Health and R&D analyses", null, null, null, null, null],
];
for (let row = 14; row <= 20; row += 1) summary.mergeCells(`B${row}:G${row}`);
summary.getRange("A14:A20").format = { fill: C.paleGray, font: { bold: true, color: C.dark } };
summary.getRange("A14:G20").format.wrapText = true; body(summary.getRange("A14:G20"));

summary.getRange("I6:J6").values = [["Endpoint", "Adjusted OR"]]; header(summary.getRange("I6:J6"));
for (let i = 0; i < 4; i += 1) summary.getRange(`I${7+i}:J${7+i}`).formulas = [[`=A${7+i}`, `=D${7+i}`]];
body(summary.getRange("I7:J10")); summary.getRange("J7:J10").format.numberFormat = "0.000";
const chart = summary.charts.add("bar", summary.getRange("I6:J10"));
chart.title = "Adjusted odds ratios"; chart.hasLegend = false;
chart.xAxis = { axisType: "textAxis", textStyle: { fontSize: 8 } };
chart.yAxis = { numberFormatCode: "0.00", min: 0.85, max: 1.25 };
chart.setPosition("I12", "M24");

summary.getRange("A:A").format.columnWidth = 24; summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:C").format.columnWidth = 14; summary.getRange("D:F").format.columnWidth = 19;
summary.getRange("G:G").format.columnWidth = 14; summary.getRange("H:H").format.columnWidth = 3;
summary.getRange("I:I").format.columnWidth = 24; summary.getRange("J:M").format.columnWidth = 14;
summary.freezePanes.freezeRows(1);

const widths = {
  "Main Models": [15, 28, 15, 17, 12, 20, 16, 15, 20, 14, 14, 14, 24, 14, 14, 17, 17, 17, 20, 20, 20, 14, 20],
  "Standardised Trends": [16, 10, 14, 16, 25, 28, 27],
  "Standardised AMR": [16, 10, 23, 10, 14, 16, 21, 25, 20, 20],
  "Sensitivity": [16, 40, 17, 14, 14, 14, 14, 18, 14, 20],
  "Diagnostics": [16, 12, 12, 14, 14, 18, 24, 24, 22, 22, 20, 22, 22],
  "Standardisation QA": [16, 13, 36, 25, 24, 20, 17],
  "Calibration": [16, 20, 25, 27, 28],
  "MIC Models": [16, 33, 29, 16, 16, 14, 14, 20, 17],
  "MIC Country-Year": [16, 10, 23, 10, 14, 25, 25, 17, 18, 16],
  "Event Trajectories": [10, 23, 16, 17, 20, 19, 19, 24, 20, 22, 20, 20],
};
for (const [sheetName] of sourceSpecs) {
  const sheet = wb.worksheets.getItem(sheetName); const used = sheet.getUsedRange();
  body(used); used.format.wrapText = false;
  header(sheet.getRangeByIndexes(0, 0, 1, used.columnCount));
  const cols = widths[sheetName];
  for (let i = 0; i < cols.length; i += 1) sheet.getRangeByIndexes(0, i, used.rowCount, 1).format.columnWidth = cols[i];
  sheet.freezePanes.freezeRows(1);
  if (["Standardised AMR", "MIC Country-Year", "Event Trajectories"].includes(sheetName)) sheet.freezePanes.freezeColumns(2);
}
wb.worksheets.getItem("Main Models").getRange("W2:W5").conditionalFormats.add("containsText", { text: "FALSE", format: { fill: C.paleGray } });

title(methods, "A1:F1", "Methods and Interpretation Notes");
methods.getRange("A3:F14").values = [
  ["Item", "Definition / rule", null, null, null, null],
  ["Outcome family", "Four WHO critical-priority pathogen–resistance phenotypes frozen in Phase 1", null, null, null, null],
  ["Outcome", "Resistant versus susceptible/intermediate among tested ATLAS isolates", null, null, null, null],
  ["Primary exposure", "log2(1 + annual ACLED political-violence events) in the preceding year", null, null, null, null],
  ["Main estimator", "Separate isolate-level logistic models with country and year fixed effects", null, null, null, null],
  ["Adjustment", "Age group, sex, specimen source, specialty and lagged temperature anomaly", null, null, null, null],
  ["Uncertainty", "Country-clustered t inference plus wild-cluster score sensitivity", null, null, null, null],
  ["Multiplicity", "Holm correction across four confirmatory conflict coefficients", null, null, null, null],
  ["Standardised AMR", "Mixed logistic model with partially pooled country-year intercepts; pooled composition target", null, null, null, null],
  ["MIC", "Outer-censored values retained; two bounded-substitution sensitivities", null, null, null, null],
  ["Public release", "Suppress country-year endpoint cells with fewer than 30 tested isolates", null, null, null, null],
  ["Terminology", "Standardised resistance among ATLAS surveillance isolates; not national prevalence", null, null, null, null],
];
methods.mergeCells("B3:F3");
for (let row = 4; row <= 14; row += 1) methods.mergeCells(`B${row}:F${row}`);
header(methods.getRange("A3:F3")); body(methods.getRange("A4:F14")); methods.getRange("A4:A14").format = { fill: C.paleGray, font: { bold: true, color: C.dark } };
methods.getRange("A3:F14").format.wrapText = true; methods.getRange("A:A").format.columnWidth = 24; methods.getRange("B:F").format.columnWidth = 23;
methods.freezePanes.freezeRows(3);

const inspect = await wb.inspect({ kind: "table", range: "Summary!A1:M24", include: "values,formulas", tableMaxRows: 24, tableMaxCols: 13 });
await fs.writeFile(path.join(outputDir, "Phase4_workbook_inspect.ndjson"), inspect.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "formula error scan" });
await fs.writeFile(path.join(outputDir, "Phase4_workbook_formula_errors.ndjson"), errors.ndjson);
for (const sheetName of ["Summary", ...sourceSpecs.map(x => x[0]), "Methods"]) {
  const image = await wb.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName.replaceAll(" ", "_")}.png`), new Uint8Array(await image.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(outputDir, "Phase4_Statistical_Analysis_Results.xlsx"));
