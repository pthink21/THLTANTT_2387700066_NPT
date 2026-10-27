"""Render ảnh báo cáo từ stdout/API capture thực tế; không mô phỏng terminal."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT=Path(__file__).parents[1]; OUT=ROOT/"screenshots"; OUT.mkdir(parents=True,exist_ok=True)
FONT=Path("C:/Windows/Fonts/consola.ttf"); TITLE=Path("C:/Windows/Fonts/arial.ttf")
def wrap(text, limit=92):
    result=[]
    for line in text.splitlines() or [""]:
        while len(line)>limit:
            split=line.rfind(" ",0,limit)
            if split<1: split=limit
            result.append(line[:split]); line=line[split:].lstrip()
        result.append(line)
    return result
def render(name,title,source,max_lines=28):
    raw=Path(source).read_bytes()
    encoding="utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig"
    text=raw.decode(encoding,errors="replace")
    lines=wrap(text)[:max_lines]
    font=ImageFont.truetype(str(TITLE),18); title_font=ImageFont.truetype(str(TITLE),24)
    width=1280; line_h=27; height=105+line_h*len(lines)+45
    image=Image.new("RGB",(width,height),(248,250,252)); draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,width,70),fill=(20,39,65)); draw.text((32,21),title,font=title_font,fill=(255,255,255))
    draw.text((32,82),f"Nguồn output thực tế: {Path(source).relative_to(ROOT).as_posix()}",font=font,fill=(55,75,100))
    y=120
    for line in lines:
        draw.text((32,y),line,font=font,fill=(20,30,42)); y+=line_h
    draw.text((32,height-35),"Bản ảnh báo cáo được render từ log/response đã lưu; không phải ảnh chụp giao diện desktop.",font=ImageFont.truetype(str(TITLE),15),fill=(80,90,105))
    path=OUT/name; image.save(path); check=Image.open(path); check.verify(); return path

render("01-environment.png","Môi trường và đề bài đã xác minh",ROOT/"evidence"/"environment.txt")
render("02-project-structure.png","Cấu trúc SAST và DAST",ROOT/"evidence"/"project-structure.txt")
render("03-sast-vulnerabilities.png","SAST: phát hiện mẫu nguy hiểm",ROOT/"evidence"/"sast-vulnerable.txt")
render("04-sast-safe.png","SAST: đối chiếu mẫu an toàn",ROOT/"evidence"/"sast-safe.txt")
render("05-sarif-verified.png","SARIF 2.1.0: xác minh định dạng",ROOT/"evidence"/"sarif-validation.txt")
render("06-sast-tests.png","Unit tests SAST",ROOT/"evidence"/"sast-tests.txt",20)
render("07-dast-runtime-demo.png","DAST: runtime, memory và sandbox",ROOT/"evidence"/"dast-demo.json",28)
render("09-api-smoke.png","DAST: Flask API loopback",ROOT/"evidence"/"api-smoke.json",28)
render("10-dast-tests.png","Unit tests DAST",ROOT/"evidence"/"dast-tests.txt",20)
render("11-integration-summary.png","Tích hợp: 14 test đạt; API/SARIF được kiểm tra",ROOT/"evidence"/"integration-summary.txt",15)
print("Rendered and verified",len(list(OUT.glob("*.png"))),"output evidence images")
