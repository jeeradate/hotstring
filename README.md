## Hotstring

hotstring คือ app ที่ ทำงานโดยการสั่งงานด้วย hot string

hot string จะมี ".." หรือ "ใใ" นำหน้า เป็น activate / scrape sequence
แล้วตามต้วยตัวอักษร 1-8 ตัว ที่เรียกว่า hot string หากเป็นภาษาไทย หรือ อักษรอังกฤษตัวใหญ้ ให้แปลงเป็นภาษาอังกฤษตัวเล็ก ก่อนทำงานตามที่กำหนด
จบด้วย spacebar
เมื่อผู้ใช้ป้อน hot string ไม่ว่าจะอยู่ใน สภาวะที่รับ keyboard สภาวะที่ไม่รับ Keyboard
hotstring app หากมีการรับ keyboard จะทำการ Clear scape sequence , hot string และ space bar เพื่ออยู่ในสภาวะเหมือนก่อนการ สั่งงาน

ระบบจะทำงานตามคำสั่งสองแบบคือ

hot message จะพิมพ์ข้อความใน content
hot run จะ Run app ใน content
hotstring app ใช้ Python และ NiceGUI ส่วนข้อมูลทั้งหมดจะเก็บใน hotstring_data.jason
ระบบใช้ uv project management/dependent management

การ run app จะต้อง run ฝ่าน Powershell ที่มีสิทธิ administrator เพราะมีการใช้การดักจับพิมพ์ด้วย keyboard ด้วยคำสั่งต่อไปนี้

PS C:\> d:
PS D:\> cd hotstring
PS D:\hotstring> uv run python src/hotstring/app2.py
NiceGUI ready to go on http://127.0.0.1:8080
ปัญหาที่ยังมี
ภายใต้ sre/hotstring ตอนนี้มี File โปรแกรม 3 ตัว ที่กำลังทดสอบ ปัญหาตอนนี้คือ หลังจาก hotstring ทำงาน message แล้วมักจะพิมพ์ข้อความเกิน เมื่อกด space bar แต่หากกด enter ก่อนจะแก้ได้

โปรดตรวจดูว่า app.py , hotstring_data.json และ tree.txt แล้วนำเสนอการแก้ไขเป็นข้อมูลที่พร้อม Copy/Past ลงใน File ที่ต้องการแก้ไขด้วย

ขั้นตอนการติดตั้งและรันโปรเจกต์
โปรแจกต์ฺนี้อยู่ที่ https://github.com/jeeradate/hotstring.git

Clone หรือดาวน์โหลดโปรเจกต์ลงเครื่อง เปิด Terminal หรือ Command Prompt แล้วใช้คำสั่ง Clone ผ่าน Git:

git clone https://github.com/jeeradate/hotstring.git
cd hotstring
(หรือดาวน์โหลดไฟล์ ZIP จากหน้า GitHub มาแตกไฟล์ แล้วใช้ Terminal เปิดเข้าไปที่โฟลเดอร์โปรเจกต์)

ติดตั้ง Dependencies โดยใช้ uv โปรเจกต์นี้จัดการแพ็กเกจด้วย uv ให้รันคำสั่งเพื่อสร้าง Virtual Environment และติดตั้งไลบรารีที่จำเป็นทั้งหมด (เช่น nicegui, keyboard) อัตโนมัติ:

Bash

uv sync
รันโปรแกรม หลังจากติดตั้ง dependencies เรียบร้อยแล้ว สามารถสั่งรันแอปพลิเคชันผ่าน uv ได้ทันที (ระบุ path ไปยังไฟล์หลักของโปรเจกต์ เช่น src/hotstring/app.py):

Bash

uv run python src/hotstring/app.py
ข้อควรระวังเพิ่มเติมบน Windows:
โปรแกรมนี้ใช้งานไลบรารี keyboard ซึ่งในระบบปฏิบัติการ Windows อาจต้องใช้สิทธิ์ Administrator ในการรัน Terminal หากพบปัญหาการดักจับปุ่มคีย์บอร์ด (Key Hook) ให้ลองคลิกขวาที่เปิด Terminal (Command Prompt / VS Code) ด้วยคำสั่ง Run as Administrator ก่อนรันคำสั่งครับ