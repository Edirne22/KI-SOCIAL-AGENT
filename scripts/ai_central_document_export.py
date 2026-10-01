"""Generate PDF, DOCX and XLSX from a reviewed structured report.

No arbitrary macro, shell execution, remote fetch, or hidden model calls.
For transforming a real uploaded Excel workbook, separate reviewed editing workflow required.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ALLOWED={"pdf","docx","xlsx"}
def validate(data):
    if not isinstance(data,dict) or set(data)!={"title","paragraphs","table"}:
        raise ValueError("expected title, paragraphs, table")
    if not isinstance(data["title"],str) or not 1<=len(data["title"])<=120:
        raise ValueError("invalid title")
    if not isinstance(data["paragraphs"],list) or len(data["paragraphs"])>80 or any(
        not isinstance(p,str) or len(p)>3000 for p in data["paragraphs"]):
        raise ValueError("invalid paragraphs")
    rows=data["table"]
    if not isinstance(rows,list) or len(rows)>300 or not rows or not isinstance(rows[0],list) or not 1<=len(rows[0])<=18:
        raise ValueError("invalid table")
    width=len(rows[0])
    for row in rows:
        if not isinstance(row,list) or len(row)!=width:
            raise ValueError("uneven table")
        for value in row:
            if value is not None and (not isinstance(value,(str,int,float,bool)) or len(str(value))>500):
                raise ValueError("invalid table cell")
    return data

def text(s):
    # Spreadsheet formula injection must never be accidental when model proposes cell values.
    return str(s).replace("\x00","").strip()
def spreadsheet_cell(v):
    if not isinstance(v,str):return v
    return ("'"+v) if re.match(r"^\s*[=+@-]",v) else v

def export(data, output):
    data=validate(data)
    path=Path(output)
    ext=path.suffix.lower().lstrip(".")
    if ext not in ALLOWED:raise ValueError("unsupported extension")
    path.parent.mkdir(parents=True,exist_ok=True)
    if ext=="docx":
        from docx import Document
        document=Document()
        document.add_heading(text(data["title"]),0)
        for p in data["paragraphs"]:document.add_paragraph(text(p))
        table=document.add_table(rows=1,cols=len(data["table"][0]))
        table.style="Light Shading Accent 1"
        for i,cell in enumerate(data["table"][0]):table.rows[0].cells[i].text=text(cell)
        for row in data["table"][1:]:
            cells=table.add_row().cells
            for i,val in enumerate(row):cells[i].text=text(val)
        document.save(path)
    elif ext=="pdf":
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
        from xml.sax.saxutils import escape
        styles=getSampleStyleSheet()
        story=[Paragraph(escape(text(data["title"])),styles["Title"]),Spacer(1,12)]
        for p in data["paragraphs"]:story.extend([Paragraph(escape(text(p)),styles["BodyText"]),Spacer(1,7)])
        cells=[[Paragraph(escape(text(v)),styles["BodyText"]) for v in row] for row in data["table"]]
        table=LongTable(cells,repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D7E6F7")),
                                  ("GRID",(0,0),(-1,-1),0.3,colors.grey),
                                  ("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(table)
        SimpleDocTemplate(str(path),pagesize=A4,title=text(data["title"])).build(story)
    else:
        # Public hosted GitHub runner uses XlsxWriter for safe *new* workbook exports.
        # Original uploaded Excel edits require a separate fidelity-tested editing lane.
        import xlsxwriter
        wb=xlsxwriter.Workbook(str(path),{"constant_memory":True,"strings_to_formulas":False,
                                          "strings_to_urls":False})
        ws=wb.add_worksheet("Bericht")
        heading=wb.add_format({"bold":True,"font_size":16,"font_color":"#1C3658"})
        header=wb.add_format({"bold":True,"font_color":"#FFFFFF","bg_color":"#234D74"})
        ws.write_string(0,0,text(data["title"]),heading)
        ws.freeze_panes(3,0)
        for j,v in enumerate(data["table"][0]):
            ws.write_string(2,j,text(v),header)
        for i,row in enumerate(data["table"][1:],3):
            for j,v in enumerate(row):
                v=spreadsheet_cell(v)
                if isinstance(v,str):ws.write_string(i,j,v)
                elif v is None:ws.write_blank(i,j,None)
                elif isinstance(v,bool):ws.write_boolean(i,j,v)
                else:ws.write_number(i,j,v)
        for j,col in enumerate(zip(*data["table"])):
            width=min(48,max(14,max(len(text(v)) for v in col)+3))
            ws.set_column(j,j,width)
        wb.close()
    if not path.is_file() or path.stat().st_size<500:raise RuntimeError("invalid export artifact")
    return {"output":str(path),"format":ext,"bytes":path.stat().st_size,"validated":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    print(json.dumps(export(data,args.output),ensure_ascii=False))
