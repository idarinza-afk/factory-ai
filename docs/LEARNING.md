# factory-ai เก่งขึ้นได้อย่างไร

factory-ai **เก็บข้อมูลเพื่อเรียนรู้ แต่เก็บในเครื่องคุณ** และไม่แก้ "สมอง" (weights) ของตัวเองอัตโนมัติทุกครั้งที่ใช้
เพราะถ้าเรียนจากคำตอบที่ยังไม่มีใครตรวจ มันจะจำของผิดสะสมไปเรื่อยๆ

## ชั้นที่ 1 — Experience memory (เก่งขึ้นทันที)
ทุกงานที่จบ (ออกแบบไลน์, machine list, PLC, ROI) บันทึกเป็น *case* ใน SQLite (`~/.factory-ai/experience.db`)
ก่อนตอบทุกครั้ง agent จะค้นเคสที่คล้ายกันมาใส่ในบริบท เคสที่ **verified** (ผ่านหน้างานจริง) ได้ลำดับก่อน

```
factory-ai memory add ...        # เพิ่มเคส (หรือพิมพ์ /save ระหว่าง chat)
factory-ai memory verify <id> "ผลหน้างานจริง / บทเรียน"
```

## ชั้นที่ 2 — กฎที่วิศวกรยืนยัน (เก่งขึ้นตรงจุด)
คำแก้ไขของคุณถูกเก็บเป็น *rule* และถูกบังคับใช้ก่อนความรู้ทั่วไป

```
factory-ai memory rule "egg line" "เผื่อ buffer 10% ก่อน sealer เสมอ"
```

## ชั้นที่ 3 — Fine-tune เป็นรอบ (เก่งขึ้นถาวรในตัวโมเดล)
ส่งออกเคส verified + rules เป็น JSONL รูปแบบ chat แล้วเทรน LoRA ด้วยเครื่องมือมาตรฐาน
(เช่น Unsloth, Axolotl, LLaMA-Factory) จากนั้นแปลงเป็น GGUF แล้วสร้าง Ollama model ใหม่

```
factory-ai memory export dataset.jsonl
# เทรน LoRA -> merge -> GGUF -> ollama create factory-ai-personal -f Modelfile
# set FACTORY_AI_MODEL=factory-ai-personal
```

แนะนำทำทุก 3 เดือน หรือเมื่อมีเคส verified เพิ่มเกิน ~200 รายการ และทดสอบกับชุดโจทย์ benchmark ก่อนเปลี่ยนไปใช้

## โครงสร้างโมเดลแบบซ้อนชั้น

```
Personal layer   (experience memory + LoRA ส่วนตัว)   <- เก่งในแบบของคุณ
Community LoRA   (ทุกคนช่วยกันเทรน, ปล่อยเป็นเวอร์ชัน) <- ดู CONTRIBUTING.md
Base model       (open-weight model)
```
