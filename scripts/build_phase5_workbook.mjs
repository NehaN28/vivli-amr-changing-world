import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/workspace/scratch/6f657a5e2035";
const repo = path.join(root, "amr-changing-world");
const inputDir = path.join(repo, "outputs", "phase5_analysis");
const outputDir = path.join(root, "outputs", "phase5");
const previewDir = path.join(root, "work", "phase5_workbook_previews");
await fs.mkdir(outputDir, { recursive: true }); await fs.mkdir(previewDir, { recursive: true });

function parseCsv(text) {
  const rows=[]; let row=[]; let field=""; let quoted=false;
  for(let i=0;i<text.length;i+=1){const ch=text[i]; if(quoted){if(ch==='"'&&text[i+1]==='"'){field+='"';i+=1;}else if(ch==='"')quoted=false;else field+=ch;}else if(ch==='"')quoted=true;else if(ch===','){row.push(field);field="";}else if(ch==='\n'){row.push(field.replace(/\r$/,""));rows.push(row);row=[];field="";}else field+=ch;}
  if(field.length||row.length){row.push(field.replace(/\r$/,""));rows.push(row);}
  return rows.map((r,ri)=>r.map(v=>{if(ri===0||v==="")return v;if(v==="True")return true;if(v==="False")return false;const n=Number(v);return Number.isFinite(n)?n:v;}));
}

const specs = [
  ["One Health Models","one_health_models.csv"], ["One Health Coverage","one_health_coverage.csv"],
  ["WOAH Models","woah_models.csv"], ["WOAH Coverage","woah_coverage.csv"],
  ["R&D Pathogens","rd_pathogen_alignment.csv"], ["R&D Sectors","rd_sector_portfolio.csv"],
  ["R&D Areas","rd_research_area_portfolio.csv"], ["R&D Cross-sector","rd_cross_sector_portfolio.csv"],
  ["R&D Geography","rd_recipient_geography.csv"], ["AMR Annual Context","rd_amr_annual_context.csv"],
  ["Country Context","country_context_profile.csv"],
];
const wb=Workbook.create(); const summary=wb.worksheets.add("Summary"); const loaded=new Map();
for(const [name,file] of specs){const rows=parseCsv(await fs.readFile(path.join(inputDir,file),"utf8"));loaded.set(name,rows);const sh=wb.worksheets.add(name);if(rows.length)sh.getRangeByIndexes(0,0,rows.length,rows[0].length).values=rows;}
const methods=wb.worksheets.add("Methods");
const C={navy:"#275D7A",dark:"#24323F",blue:"#DDEBF3",gray:"#F2F4F5",white:"#FFFFFF",green:"#D9EAD3",amber:"#FCE8B2",border:"#CCD4D9"};
for(const sh of wb.worksheets.items)sh.showGridLines=false;
function title(sh,range,text){sh.mergeCells(range);const r=sh.getRange(range);r.values=[[text]];r.format={fill:C.navy,font:{bold:true,color:C.white,size:16},verticalAlignment:"center",rowHeight:34};}
function header(r){r.format={fill:C.navy,font:{bold:true,color:C.white,size:9},wrapText:true,verticalAlignment:"center",borders:{preset:"all",style:"thin",color:C.border},rowHeight:32};}
function body(r){r.format.font={color:C.dark,size:9};r.format.verticalAlignment="center";r.format.borders={insideHorizontal:{style:"thin",color:C.border}};}

title(summary,"A1:M1","Phase 5: One Health Determinants and R&D Alignment");
summary.mergeCells("A3:M4");summary.getRange("A3").values=[["OVERALL CONCLUSION  |  No temperature, livestock-size, animal-AMU, or conflict-modification association survived FDR correction. Two inverse swine-share associations with K. pneumoniae outcomes remain exploratory and non-causal."]];
summary.getRange("A3:M4").format={fill:C.green,font:{bold:true,color:C.dark,size:11},wrapText:true,verticalAlignment:"center"};
summary.getRange("A6:F6").values=[["Outcome","Exposure","Adjusted OR","95% CI low","95% CI high","FDR p"]];header(summary.getRange("A6:F6"));
const ohRows=loaded.get("One Health Models"); const h=ohRows[0];
const sigRows=[]; for(let i=1;i<ohRows.length;i+=1){if(ohRows[i][h.indexOf("fdr_significant_005")]===true)sigRows.push(i+1);}
for(let i=0;i<sigRows.length;i+=1){const dest=7+i,src=sigRows[i];summary.getRange(`A${dest}:F${dest}`).formulas=[[
  `='One Health Models'!C${src}`,`='One Health Models'!A${src}`,`='One Health Models'!F${src}`,`='One Health Models'!G${src}`,`='One Health Models'!H${src}`,`='One Health Models'!R${src}`
]];}
body(summary.getRange(`A7:F${6+sigRows.length}`));summary.getRange(`C7:F${6+sigRows.length}`).format.numberFormat="0.000";
summary.mergeCells("A11:F11");summary.getRange("A11").values=[["Interpretation safeguards"]];summary.getRange("A11:F11").format={fill:C.blue,font:{bold:true,color:C.navy,size:11}};
const safeguards=[
  ["Analysis status","All Phase 5 models are secondary or exploratory"],
  ["Multiplicity","Benjamini–Hochberg FDR correction within each analysis family"],
  ["Livestock","Total livestock units are not density; shares are compositional"],
  ["WOAH","6–14 countries depending on endpoint; insufficient evidence is not evidence of no relationship"],
  ["Vulnerability","Components remain separate; no composite score was constructed"],
  ["R&D geography","Recipient institution country is not study location or beneficiary population"],
];
summary.getRange("A12:B17").values=safeguards;summary.getRange("A12:A17").format={fill:C.gray,font:{bold:true,color:C.dark}};body(summary.getRange("A12:B17"));summary.getRange("B12:B17").format.wrapText=true;

summary.getRange("H6:J6").values=[["Sector","Funding share","Fractional funding USD"]];header(summary.getRange("H6:J6"));
for(let i=0;i<5;i+=1){const d=7+i,s=2+i;summary.getRange(`H${d}:J${d}`).formulas=[[`='R&D Sectors'!A${s}`,`='R&D Sectors'!D${s}`,`='R&D Sectors'!C${s}`]];}
body(summary.getRange("H7:J11"));summary.getRange("I7:I11").format.numberFormat="0.0\"%\"";summary.getRange("J7:J11").format.numberFormat="$#,##0";
const chart=summary.charts.add("bar",summary.getRange("H6:I11"));chart.title="R&D funding by sector";chart.hasLegend=false;chart.yAxis={numberFormatCode:"0\"%\""};chart.setPosition("H13","M27");
summary.getRange("A:A").format.columnWidth=28;summary.getRange("B:B").format.columnWidth=38;summary.getRange("C:F").format.columnWidth=15;summary.getRange("G:G").format.columnWidth=3;summary.getRange("H:H").format.columnWidth=22;summary.getRange("I:J").format.columnWidth=18;summary.getRange("K:M").format.columnWidth=12;summary.freezePanes.freezeRows(1);

for(const [name] of specs){const sh=wb.worksheets.getItem(name);const used=sh.getUsedRange();body(used);header(sh.getRangeByIndexes(0,0,1,used.columnCount));used.format.wrapText=false;used.format.autofitColumns();for(let c=0;c<used.columnCount;c+=1){const col=sh.getRangeByIndexes(0,c,used.rowCount,1);if(col.format.columnWidth>42)col.format.columnWidth=42;}sh.freezePanes.freezeRows(1);if(["One Health Models","WOAH Models","R&D Geography","Country Context"].includes(name))sh.freezePanes.freezeColumns(2);}

title(methods,"A1:F1","Methods, Definitions and Interpretation");
const notes=[
  ["Item","Definition / decision",null,null,null,null],
  ["Temperature","Previous-year annual anomaly; effect per 1 °C",null,null,null,null],
  ["Livestock size","Previous-year total analytical livestock units; effect per doubling; not density",null,null,null,null],
  ["Livestock shares","Previous-year species-group livestock-unit share; effect per 10 percentage points",null,null,null,null],
  ["Animal AMU","WOAH adjusted mg/kg; log2(1 + mg/kg); complete-case subset",null,null,null,null],
  ["Class alignment","All-generation cephalosporin proxy for ceftazidime; no carbapenem-specific class",null,null,null,null],
  ["Models","Isolate logistic models with country/year fixed effects and patient/specimen adjustment",null,null,null,null],
  ["Interactions","Conflict × centred One Health component; exploratory",null,null,null,null],
  ["Multiplicity","FDR correction within determinant, interaction, WOAH main-effect and WOAH interaction families",null,null,null,null],
  ["R&D window","Projects starting 2015–2024; nominal reported USD commitments; fractional category allocation",null,null,null,null],
  ["Country profile","Separate evidence components with coverage indicators; composite score = FALSE",null,null,null,null],
];
methods.getRange("A3:F13").values=notes;for(let r=3;r<=13;r+=1)methods.mergeCells(`B${r}:F${r}`);header(methods.getRange("A3:F3"));body(methods.getRange("A4:F13"));methods.getRange("A4:A13").format={fill:C.gray,font:{bold:true,color:C.dark}};methods.getRange("A3:F13").format.wrapText=true;methods.getRange("A:A").format.columnWidth=24;methods.getRange("B:F").format.columnWidth=23;methods.freezePanes.freezeRows(3);

const inspect=await wb.inspect({kind:"table",range:"Summary!A1:M27",include:"values,formulas",tableMaxRows:27,tableMaxCols:13});await fs.writeFile(path.join(outputDir,"Phase5_workbook_inspect.ndjson"),inspect.ndjson);
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",options:{useRegex:true,maxResults:300},summary:"formula error scan"});await fs.writeFile(path.join(outputDir,"Phase5_workbook_formula_errors.ndjson"),errors.ndjson);
for(const name of ["Summary",...specs.map(x=>x[0]),"Methods"]){const image=await wb.render({sheetName:name,autoCrop:"all",scale:1,format:"png"});await fs.writeFile(path.join(previewDir,`${name.replaceAll(" ","_")}.png`),new Uint8Array(await image.arrayBuffer()));}
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(outputDir,"Phase5_One_Health_and_RD_Analysis_Results.xlsx"));
