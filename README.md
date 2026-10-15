# factory-ai

**AI ผู้ช่วยวิศวกรรมการผลิต ที่รันในเครื่องตัวเอง (Local AI)**
ออกแบบไลน์ผลิต · คำนวณ capacity / line balance / OEE / ROI · layout 2D + ส่งต่อ 3D
· ทำ machine list, part list, manual และเอกสารที่เกี่ยวข้อง
และ **เก่งขึ้นเรื่อยๆ จากประสบการณ์ของคุณเอง** โดยข้อมูลไม่ออกจากเครื่อง

ใช้ฟรี — งาน PLC, IoT และ dashboard อยู่ใน **factory-ai Pro** (เร็วๆ นี้ — ดูหัวข้อด้านล่าง)

*A local AI assistant for production engineering that learns from your own verified experience.*

> สถานะ: v0.1 (preview) — ดู [docs/ROADMAP.md](docs/ROADMAP.md)

---

## ทำอะไรได้บ้าง (ฟรี)

| โมดูล | ความสามารถ | ไฟล์ |
|---|---|---|
| คำนวณไลน์ | takt time, จำนวนเครื่อง (คิด OEE), bottleneck, line balancing (RPW), buffer | `factory_ai/calc/line.py` |
| OEE / ROI | OEE แยก A×P×Q + loss หลัก, payback / NPV / IRR | `calc/oee.py`, `calc/roi.py` |
| เอกสาร | Machine list, Part list (Excel), O&M manual (Markdown/Word) — ราคาที่ไม่รู้จะเว้นว่าง | `documents.py` |
| Layout | วางเครื่องตาม flow (ตรง / U / งู), เช็กพื้นที่, SVG + JSON สำหรับ 3D | `layout.py` |
| ความรู้ | Knowledge base ค้นได้ (+ โน้ตของคุณเองใน `~/.factory-ai/knowledge`) | `knowledge.py` |
| เรียนรู้ | Experience memory, กฎที่วิศวกรยืนยัน, export dataset สำหรับ fine-tune | `memory.py` |
| ชุมชน | แพ็กข้อมูลแบบลบข้อมูลลับ เพื่อช่วยเทรนโมเดลกลาง | `contribute.py` |

หลักการสำคัญ: **AI ไม่เดาตัวเลข** — ตัวเลขทุกตัวมาจากฟังก์ชันคำนวณที่ทดสอบแล้ว โมเดลภาษามีหน้าที่เข้าใจโจทย์ เลือกเครื่องมือ และอธิบายผล

## ติดตั้ง (Windows / macOS / Linux)

1. ติดตั้ง Python 3.10+ และ [Ollama](https://ollama.com)
2. ดึงโมเดลที่รองรับ tool calling เช่น
   ```bash
   ollama pull qwen2.5:14b
   ```
   (เลือกขนาดตาม VRAM; ตั้งชื่อโมเดลด้วยตัวแปร `FACTORY_AI_MODEL`)
3. ติดตั้ง factory-ai
   ```bash
   git clone https://github.com/idarinza-afk/factory-ai
   cd factory-ai
   pip install -e ".[docs]"
   factory-ai doctor
   ```

## ใช้งาน

```bash
factory-ai chat                      # คุยกับผู้ช่วย (พิมพ์ /save เพื่อเก็บคำตอบเป็นเคส)
factory-ai ask "ไลน์บรรจุ 20,000 ขวด/วัน 2 กะ ต้องใช้ filler 3,000 bph กี่เครื่อง"
factory-ai tools                     # ดูเครื่องมือทั้งหมด
factory-ai run takt_time '{"demand_units":20000,"shifts":2,"hours_per_shift":8,"break_min_per_shift":60}'
factory-ai run layout_line examples/bottling_line.json
factory-ai pro                       # ดูว่า Pro จะเพิ่มอะไร
```

### ทำให้มันเก่งขึ้น

```bash
factory-ai memory add --kind line_design --title "ไลน์ไข่" --problem "..." --solution "..."
factory-ai memory verify 1 "หน้างานจริง sealer เป็นคอขวด ต้องเผื่อ 10%"
factory-ai memory rule "egg line" "เผื่อ buffer 10% ก่อน sealer เสมอ"
factory-ai memory export dataset.jsonl     # สำหรับ fine-tune LoRA เป็นรอบ
```

รายละเอียด: [docs/LEARNING.md](docs/LEARNING.md) · ช่วยเทรนโมเดลกลาง: [CONTRIBUTING.md](CONTRIBUTING.md)

## factory-ai Pro (เร็วๆ นี้)

ต่อยอดจากงานออกแบบไลน์ในตัวฟรี ไปสู่งานควบคุมและระบบอัตโนมัติ

| ความสามารถ | รายละเอียด |
|---|---|
| **PLC control logic** | สร้าง I/O list จาก machine list, แปลง sequence เป็น IEC 61131-3 Structured Text, function block มาตรฐาน (motor, valve, conveyor, alarm), ตรวจโค้ดอัตโนมัติ, ทดสอบผ่าน simulator, ส่งออกไปยัง Siemens TIA / Mitsubishi GX Works / Omron Sysmac |
| **IoT** | tag map MQTT / OPC UA จาก I/O list, โค้ด edge collector แบบอ่านอย่างเดียว, ตั้งค่า gateway |
| **Dashboard** | OEE และ production dashboard จากข้อมูลไลน์ที่ออกแบบไว้, วิเคราะห์ downtime / ของเสีย, รายงานประจำกะ และ dashboard แบบ real-time |

**ค่าใช้จ่าย** (ประกาศราคาเร็วๆ นี้)

| แพ็กเกจ | การคิดเงิน | เหมาะกับ |
|---|---|---|
| Pro | รายเดือน ต่อผู้ใช้ | วิศวกร / ฟรีแลนซ์ / SI ขนาดเล็ก |
| Team | รายเดือน ต่อที่นั่ง + experience memory ใช้ร่วมกันในทีม | บริษัท SI / ผู้ผลิตเครื่องจักร |
| Enterprise | รายปี + ติดตั้งในองค์กร, เทรนโมเดลด้วยข้อมูลบริษัท, ซัพพอร์ต | โรงงาน / องค์กรขนาดใหญ่ |

สนใจทดลองใช้ Pro: เปิด issue บน GitHub แล้วติดป้าย `pro-interest`

## ความปลอดภัย (อ่านก่อนใช้)

- ผลคำนวณเป็นเครื่องมือช่วยตัดสินใจ วิศวกรผู้รับผิดชอบต้องตรวจสอบก่อนใช้งานจริง
- ราคาที่ไม่ได้ใส่จะเว้นว่างเสมอ AI จะไม่เดาราคา

ดู [docs/SAFETY.md](docs/SAFETY.md)

## ข้อมูลส่วนตัว

ทุกอย่างที่เป็นของคุณ (experience memory, โน้ต, ไฟล์ output) อยู่ที่ `~/.factory-ai` (เปลี่ยนได้ด้วย `FACTORY_AI_HOME`) ซึ่งอยู่นอก repo และไม่ถูก push ขึ้น GitHub

## License

ดู [LICENSE](LICENSE)
