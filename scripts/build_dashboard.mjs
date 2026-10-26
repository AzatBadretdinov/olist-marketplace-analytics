// Rebuild the Excel dashboard from exports/workbook_source.json.
// Requires Node.js and @oai/artifact-tool; external modules can use ARTIFACT_NODE_MODULES.
import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";
import {createRequire} from "node:module";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const moduleRoot=process.env.ARTIFACT_NODE_MODULES;
const resolvePackage=moduleRoot
  ? createRequire(pathToFileURL(path.join(moduleRoot,"_resolve.cjs")))
  : createRequire(import.meta.url);
const {Workbook,SpreadsheetFile}=await import(pathToFileURL(resolvePackage.resolve("@oai/artifact-tool")));
const data=JSON.parse(await fs.readFile(path.join(root,"exports/workbook_source.json"),"utf8"));
const output=process.env.OLIST_WORKBOOK_OUTPUT || path.join(root,"reports/marketplace_dashboard.xlsx");
const previewDir=process.env.OLIST_PREVIEW_DIR || path.join(root,"reports/workbook_previews");
await fs.mkdir(path.dirname(output),{recursive:true});
await fs.mkdir(previewDir,{recursive:true});
const wb=Workbook.create();
const dash=wb.worksheets.add("Dashboard");
const monthly=wb.worksheets.add("Monthly");
const regions=wb.worksheets.add("Regions");
const categories=wb.worksheets.add("Categories");
const source=wb.worksheets.add("Data");
const sheets=[dash,monthly,regions,categories,source];
const navy="#245A81", dark="#193B55", pale="#EAF1F6", amber="#FFF0C2", accent="#DB7650";
function date(m){return new Date(m+"-01T00:00:00Z");}
function set(sh,cell,value){sh.getRange(cell).values=[[value]];}
function form(sh,cell,value){sh.getRange(cell).formulas=[[value]];}
function title(sh,text,last="L"){set(sh,"A2",text);sh.getRange("A2:"+last+"2").format.font={size:16,bold:true,color:dark};}
function header(sh,range){sh.getRange(range).format={fill:navy,font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},rowHeight:30,wrapText:true,verticalAlignment:"center",horizontalAlignment:"center"};}
function base(sh,range){sh.showGridLines=false;sh.getRange(range).format.font={name:"Arial",size:10,color:"#263238"};sh.getRange(range).format.rowHeight=22;sh.getRange(range).format.columnWidth=15;sh.getRange(range).format.verticalAlignment="center";}
base(dash,"A1:L43");base(monthly,"A1:Q24");base(regions,"A1:Q35");base(categories,"A1:P80");base(source,"A1:N520");
dash.tabColor=navy;
title(dash,"Olist: продажи и доставка");
set(dash,"A3","Когорты покупок. Суммы товаров в BRL, только delivered.");
set(dash,"A5","Штат");set(dash,"B5","ALL");
set(dash,"D5","С месяца");set(dash,"E5",date(data.months[0]));
set(dash,"G5","По месяц");set(dash,"H5",date(data.months.at(-1)));
dash.getRange("E5").setNumberFormat("yyyy-mm");dash.getRange("H5").setNumberFormat("yyyy-mm");
for(const cell of ["B5","E5","H5"])dash.getRange(cell).format.fill=amber;
form(dash,"A6",'=IF(E5>H5,"Проверьте: начало позже конца","")');
dash.getRange("A6:L6").format.font={color:"#B42318",size:10};
dash.getRange("A1:A43").format.columnWidth=32;
dash.getRange("B1:B43").format.columnWidth=18;
dash.getRange("C1:C43").format.columnWidth=3;
dash.getRange("D1:L43").format.columnWidth=11;
source.getRange("A1:K1").values=[["Месяц","Штат","Все заказы","Доставлено","GMV BRL","Доставка BRL","Пригодно","Опоздало","Сумма дней","С отзывом","Низких оценок"]];
const inputRows=data.monthly_state.map(r=>[date(r.purchase_month),r.customer_state,r.all_orders,r.delivered_orders,r.delivered_gmv,r.delivered_freight,r.delivery_eligible,r.late_orders,r.delivery_days_sum,r.reviewed_orders,r.low_reviews]);
const last=inputRows.length+1;
source.getRange("A2:K"+last).values=inputRows;
source.getRange("A2:A"+last).setNumberFormat("yyyy-mm");
source.getRange("C2:K"+last).setNumberFormat("#,##0");
source.getRange("E2:F"+last).setNumberFormat('#,##0.00');
source.tables.add("A1:K"+last,true,"MonthlyStateSource");
header(source,"A1:K1");
source.freezePanes.freezeRows(1);
set(source,"M1","Штаты");
source.getRange("M2:M"+(data.states.length+2)).values=["ALL",...data.states].map(x=>[x]);
set(source,"N1","Месяцы");
source.getRange("N2:N"+(data.months.length+1)).values=data.months.map(m=>[date(m)]);
source.getRange("N2:N"+(data.months.length+1)).setNumberFormat("yyyy-mm");
set(source,"M33","Источник: Olist / Kaggle.");
set(source,"M34","SQL: analytics.monthly_state.");
set(source,"M35","2017-01–2018-07. Не выручка Olist.");

set(source,"M36","https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce");
source.getRange("M33:N36").format.font={size:10,color:"#596773"};
dash.getRange("B5").dataValidation={rule:{type:"list",formula1:'INDIRECT("Data!$M$2:$M$'+(data.states.length+2)+'")'}};
for(const cell of ["E5","H5"])dash.getRange(cell).dataValidation={rule:{type:"list",formula1:'INDIRECT("Data!$N$2:$N$'+(data.months.length+1)+'")'}};

title(monthly,"Помесячные показатели");
set(monthly,"A3","Штат и границы периода задаются на Dashboard. Пустые месяцы вне выбора не равны нулю.");
monthly.getRange("A5:P5").values=[["Месяц","Все заказы","Доставлено","GMV BRL","Доставка BRL","Пригодно","Опоздало","Сумма дней","С отзывом","Низких оценок","Чек BRL","Опоздания","Средний срок","Низкие оценки","Покрытие отзывами","GMV MoM"]];
header(monthly,"A5:P5");
monthly.freezePanes.freezeRows(5);
const end=5+data.months.length;
const src=(c)=>"Data!$"+c+"$2:$"+c+"$"+last;
for(let i=0;i<data.months.length;i++){
 const r=i+6;set(monthly,"A"+r,date(data.months[i]));
 const valid='AND($A'+r+'>=Dashboard!$E$5,$A'+r+'<=Dashboard!$H$5,Dashboard!$E$5<=Dashboard!$H$5)';
 const map=[["B","C"],["C","D"],["D","E"],["E","F"],["F","G"],["G","H"],["H","I"],["I","J"],["J","K"]];
 for(const [dest,sc]of map){
  const all='SUMIFS('+src(sc)+','+src("A")+',$A'+r+')';
  const state='SUMIFS('+src(sc)+','+src("A")+',$A'+r+','+src("B")+',Dashboard!$B$5)';
  form(monthly,dest+r,'=IF('+valid+',IF(Dashboard!$B$5="ALL",'+all+','+state+'),"")');
 }
 for(const [dest,num,den] of [["K","D","C"],["L","G","F"],["M","H","F"],["N","J","I"],["O","I","C"]])
  form(monthly,dest+r,'=IF(OR('+den+r+'="",'+den+r+'=0),"",'+num+r+'/'+den+r+')');
 form(monthly,"P"+r,i===0?'=""':'=IF(OR(D'+r+'="",D'+(r-1)+'="",D'+(r-1)+'=0),"",D'+r+'/D'+(r-1)+'-1)');
 set(monthly,"Q"+r,data.months[i].slice(5)+"/"+data.months[i].slice(2,4)); // Explicit text labels for chart categories.
}
monthly.getRange("A6:A"+end).setNumberFormat("yyyy-mm");
monthly.getRange("B6:J"+end).setNumberFormat("#,##0");
monthly.getRange("D6:E"+end).setNumberFormat('#,##0.00');
monthly.getRange("K6:K"+end).setNumberFormat('#,##0.00');
monthly.getRange("M6:M"+end).setNumberFormat('0.0');
for(const col of ["L","N","O","P"])monthly.getRange(col+"6:"+col+end).setNumberFormat("0.0%");
set(monthly,"Q5","Подпись месяца");

dash.getRange("A8:B8").values=[["Показатель","Значение"]];header(dash,"A8:B8");
const labels=["Все заказы","Доставленные заказы","Стоимость товаров, BRL","Средний чек товаров, BRL","Пригодные доставки","Опоздавшие заказы","Доля опозданий","Средний срок, дней","Покрытие отзывами","Низкие оценки"];
labels.forEach((x,i)=>set(dash,"A"+(9+i),x));
for(const [r,col]of [[9,"B"],[10,"C"],[11,"D"],[13,"F"],[14,"G"]])
 form(dash,"B"+r,'=IF($E$5>$H$5,"n.a.",SUM(Monthly!'+col+'6:'+col+end+'))');
form(dash,"B12",'=IF(OR(B10="n.a.",B10=0),"n.a.",B11/B10)');
form(dash,"B15",'=IF(OR(B13="n.a.",B13=0),"n.a.",B14/B13)');
form(dash,"B16",'=IF(OR(B13="n.a.",B13=0),"n.a.",SUM(Monthly!H6:H'+end+')/B13)');
form(dash,"B17",'=IF(OR(B10="n.a.",B10=0),"n.a.",SUM(Monthly!I6:I'+end+')/B10)');
form(dash,"B18",'=IF(OR($E$5>$H$5,SUM(Monthly!I6:I'+end+')=0),"n.a.",SUM(Monthly!J6:J'+end+')/SUM(Monthly!I6:I'+end+'))');
dash.getRange("B9:B14").setNumberFormat("#,##0");
dash.getRange("B12").setNumberFormat("#,##0.00");
for(const c of ["B15","B17","B18"])dash.getRange(c).setNumberFormat("0.0%");
dash.getRange("B16").setNumberFormat("0.0");
dash.getRange("A15:B15").format.fill=pale;
set(dash,"A21","Фильтры: жёлтые ячейки.");
set(dash,"A24","Как читать");
const notes=["Опоздание: позже обещанного дня.","Доля: опоздало / пригодно.","Неизвестная дата не равна сроку.","GMV не равно прибыли платформы.","Отзывы 1–2 считаются низкими.","Отзывы выбраны по последнему ответу.","Регионы: сравнение всех штатов.","Категории: весь базовый период.","Связь оценок с задержками —","наблюдение, не причинный эффект."];
notes.forEach((s,i)=>set(dash,"A"+(25+i),s));
dash.getRange("A24:B24").format.font={bold:true,color:dark};
dash.getRange("A25:B34").format.font={size:10,color:"#596773"};
function chart(sh,type,ranges,title,from,to,format,color=navy){
 const c=sh.charts.add(type,ranges); c.title=title;c.titleTextStyle.typeface="Arial";c.titleTextStyle.fontSize=13;
 c.hasLegend=false;c.xAxis={axisType:"textAxis",textStyle:{typeface:"Arial",fontSize:10}};
 c.yAxis={numberFormatCode:format,numberFormatSourceLinked:false,textStyle:{typeface:"Arial",fontSize:10}};
 c.setPosition(from,to);

 for(const s of c.series.items){s.fill=color;if(type==="line")s.line={fill:color,style:"solid",width:2};}
 return c;
}
chart(dash,"line",[monthly.getRange("Q5:Q"+end),monthly.getRange("D5:D"+end)],"Стоимость товаров, BRL","D8","L22",'0.0,," млн"');
chart(dash,"line",[monthly.getRange("Q5:Q"+end),monthly.getRange("L5:L"+end)],"Доля опозданий","D25","L40","0%",accent);

title(regions,"Доставка по штатам");
set(regions,"A3","Выбранный период Dashboard. Сравниваются все штаты; выбор штата здесь не ограничивает таблицу.");
regions.getRange("A5:H5").values=[["Штат","Доставлено","GMV BRL","Пригодно","Опоздало","Доля опозданий","Средний срок","Чек BRL"]];
header(regions,"A5:H5");regions.freezePanes.freezeRows(5);
const order=data.states.slice().sort((a,b)=>{
 const sum=s=>data.monthly_state.filter(x=>x.customer_state===s).reduce((v,x)=>v+x.late_orders,0);
 return sum(b)-sum(a);
});
for(let i=0;i<order.length;i++){
 const r=6+i;set(regions,"A"+r,order[i]);
 for(const [dest,sc]of [["B","D"],["C","E"],["D","G"],["E","H"]]){
  form(regions,dest+r,'=IF(Dashboard!$E$5>Dashboard!$H$5,"",SUMIFS('+src(sc)+','+src("B")+',$A'+r+','+src("A")+',">="&Dashboard!$E$5,'+src("A")+',"<="&Dashboard!$H$5))');
 }
 form(regions,"F"+r,'=IF(OR(D'+r+'="",D'+r+'=0),"",E'+r+'/D'+r+')');
 form(regions,"G"+r,'=IF(OR(D'+r+'="",D'+r+'=0),"",SUMIFS('+src("I")+','+src("B")+',$A'+r+','+src("A")+',">="&Dashboard!$E$5,'+src("A")+',"<="&Dashboard!$H$5)/D'+r+')');
 form(regions,"H"+r,'=IF(OR(B'+r+'="",B'+r+'=0),"",C'+r+'/B'+r+')');
}
regions.getRange("B6:E32").setNumberFormat("#,##0");regions.getRange("F6:F32").setNumberFormat("0.0%");
regions.getRange("G6:G32").setNumberFormat("0.0");regions.getRange("H6:H32").setNumberFormat("#,##0.00");
regions.getRange("F6:F32").conditionalFormats.add("colorScale",{colors:["#EDF3F7","#F8E1D4","#DB7650"],thresholds:["min",{type:"percentile",value:50},"max"]});
chart(regions,"bar",[regions.getRange("A5:A15"),regions.getRange("E5:E15")],"Опоздания в выбранных штатах","J5","Q23","#,##0");
set(regions,"J26","Порядок штатов: объём опозданий за весь базовый период.");
set(regions,"J27","Сравнивайте долю вместе с числом пригодных заказов.");

title(categories,"Категории товаров");
set(categories,"A3","Весь базовый период: январь 2017–июль 2018. Фильтры Dashboard не применяются.");
categories.getRange("A5:G5").values=[["Категория","Позиций","Заказов с категорией","GMV BRL","Доставка BRL","Доля GMV","Накопленная доля"]];
header(categories,"A5:G5");categories.freezePanes.freezeRows(5);
const cend=5+data.categories.length;
categories.getRange("A6:E"+cend).values=data.categories.map(c=>[c.category,c.item_count,c.orders_with_category,c.delivered_gmv,c.delivered_freight]);
for(let r=6;r<=cend;r++){
 form(categories,"F"+r,'=D'+r+'/SUM($D$6:$D$'+cend+')');
 form(categories,"G"+r,'=SUM($F$6:F'+r+')');
}
categories.getRange("A1:A"+cend).format.columnWidth=42;
categories.getRange("B6:E"+cend).setNumberFormat("#,##0");categories.getRange("F6:G"+cend).setNumberFormat("0.0%");
chart(categories,"bar",[categories.getRange("A5:A15"),categories.getRange("D5:D15")],"Крупнейшие категории по GMV","I5","P24",'0.0,," млн"');
set(categories,"I27","Заказы по категориям не складываются.");
set(categories,"I28","Один заказ может содержать несколько категорий.");

wb.recalculate();
// Behavioral checks against independent JSON aggregates, then restore the delivered state.
function value(sh,cell){return sh.getRange(cell).values[0][0];}
function near(actual,expected,label){if(typeof actual!=="number"||Math.abs(actual-expected)>Math.max(1e-6,Math.abs(expected)*1e-10))throw new Error(label+": "+actual+" vs "+expected);}
near(value(dash,"B11"),data.kpis.delivered_gmv,"All-state GMV");
near(value(dash,"B10"),data.kpis.delivered_orders,"Delivered orders");
near(value(dash,"B15"),data.kpis.late_rate,"Late rate");
set(dash,"B5","SP");wb.recalculate();
const sp=data.monthly_state.filter(x=>x.customer_state==="SP");
near(value(dash,"B11"),sp.reduce((s,x)=>s+x.delivered_gmv,0),"SP GMV");
set(dash,"E5",date("2018-01"));set(dash,"H5",date("2018-01"));wb.recalculate();
near(value(dash,"B11"),sp.filter(x=>x.purchase_month==="2018-01").reduce((s,x)=>s+x.delivered_gmv,0),"SP January GMV");
set(dash,"E5",date("2018-07"));set(dash,"H5",date("2017-01"));wb.recalculate();
if(value(dash,"B11")!=="n.a.")throw new Error("Invalid period not surfaced");
set(dash,"B5","ALL");set(dash,"E5",date(data.months[0]));set(dash,"H5",date(data.months.at(-1)));wb.recalculate();

const info=await wb.inspect({kind:"table",range:"Dashboard!A8:B18",include:"values,formulas",tableMaxRows:12,tableMaxCols:2,maxChars:4000});
await fs.writeFile(path.join(previewDir,"dashboard_inspection.json"),info.ndjson);
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:30},maxChars:3000});
await fs.writeFile(path.join(previewDir,"formula_scan.json"),errors.ndjson);
for(const [sh,range]of [[dash,"A1:L41"],[monthly,"A1:P15"],[regions,"A1:Q33"],[categories,"A1:P28"],[source,"A1:N12"]]){
 const image=await wb.render({sheetName:sh.name,range,scale:1.3,format:"png"});
 await fs.writeFile(path.join(previewDir,sh.name+".png"),new Uint8Array(await image.arrayBuffer()));
}
const exported=await SpreadsheetFile.exportXlsx(wb);await exported.save(output);
console.log(JSON.stringify({output,behavioralChecks:["all-state totals","state filter","month bounds","invalid date range"],formulaScan:errors.ndjson,sheets:sheets.map(s=>s.name)},null,2));


