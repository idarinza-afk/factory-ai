"""Multilingual requests.

The local model already understands many languages; what needs help is Improvise's
own keyword matching (tool routing, skill hints, knowledge search), which works on
English words. expand() appends English equivalents of common engineering terms
found in Thai, Chinese, Japanese, Vietnamese, Indonesian/Malay, Korean, German and Spanish.
Add terms freely - one line per concept.
"""

from __future__ import annotations

GLOSSARY: dict[str, list[str]] = {
    "snack line extruded corn khao taen rice cracker": ["ขนม", "สแน็ค", "ข้าวแต๋น", "ข้าวโพดอบกรอบ", "ขนมอบกรอบ", "零食", "膨化",
                                                       "スナック", "bánh snack", "makanan ringan", "과자"],
    "pork sheet meat snack": ["หมูแผ่น", "肉脯", "khô heo"],
    "extruder extrusion": ["เอ็กซ์ทรูดเดอร์", "เครื่องอัดรีด", "挤压机", "膨化机", "エクストルーダー", "máy đùn", "압출기"],
    "seasoning coating tumble drum": ["ผงปรุงรส", "คลุกผง", "โรยผง", "เคลือบน้ำตาล", "调味", "シーズニング", "tẩm gia vị", "bumbu"],
    "vffs packing bag multihead weigher": ["บรรจุซอง", "ซอง", "เครื่องชั่งหลายหัว", "包装机", "组合秤", "包装", "đóng gói", "kemasan", "포장"],
    "x-ray checkweigher inspection": ["เอกซเรย์", "เครื่องชั่งตรวจสอบ", "ตรวจสอบสิ่งแปลกปลอม", "X光", "金检", "異物検査", "kiểm tra", "검사"],
    "oven baking drying": ["อบ", "เตาอบ", "อบแห้ง", "烘烤", "烤箱", "オーブン", "sấy", "nướng", "oven", "오븐"],
    "conveyor belt": ["สายพาน", "คอนเวเยอร์", "输送带", "传送带", "输送机", "コンベア", "băng tải", "konveyor", "ban berjalan",
                      "컨베이어", "förderband", "transportband", "cinta transportadora", "transportador"],
    "motor": ["มอเตอร์", "电机", "马达", "モーター", "động cơ", "motor listrik", "모터", "antrieb"],
    "speed": ["ความเร็ว", "速度", "スピード", "tốc độ", "kecepatan", "속도", "geschwindigkeit", "velocidad"],
    "gap spacing pitch": ["ระยะห่าง", "เว้นระยะ", "间距", "間隔", "khoảng cách", "jarak", "간격", "abstand", "separación"],
    "plc program ladder logic": ["พีแอลซี", "ladder", "แลดเดอร์", "梯形图", "ラダー", "lập trình plc", "래더", "kontaktplan", "escalera"],
    "sensor": ["เซ็นเซอร์", "เซนเซอร์", "传感器", "センサー", "cảm biến", "센서", "fühler"],
    "takt time demand capacity": ["แท็กไทม์", "กำลังการผลิต", "产能", "节拍", "タクト", "能力", "năng suất", "kapasitas", "생산능력", "taktzeit", "kapazität", "capacidad"],
    "oee": ["โออีอี", "设备综合效率", "稼働率", "hiệu suất thiết bị"],
    "roi payback investment": ["คืนทุน", "ความคุ้มค่า", "การลงทุน", "投资回报", "回収", "投資", "hoàn vốn", "đầu tư", "investasi", "투자", "amortisation", "inversión"],
    "layout": ["เลย์เอาต์", "ผังโรงงาน", "วางผัง", "布局", "レイアウト", "bố trí", "tata letak", "배치", "aufstellung", "distribución"],
    "machine list": ["รายการเครื่องจักร", "设备清单", "機械リスト", "danh sách máy", "daftar mesin", "기계 목록", "maschinenliste"],
    "part list spare parts": ["รายการอะไหล่", "อะไหล่", "备件", "部品表", "phụ tùng", "suku cadang", "부품", "ersatzteile", "repuestos"],
    "manual": ["คู่มือ", "手册", "説明書", "マニュアル", "hướng dẫn", "buku panduan", "매뉴얼", "handbuch"],
    "alarm error fault code": ["อลาร์ม", "สัญญาณเตือน", "รหัสผิดพลาด", "故障", "报警", "アラーム", "エラー", "lỗi", "báo động", "kesalahan", "알람", "오류", "störung", "fehler", "alarma", "falla"],
    "pneumatic cylinder air": ["กระบอกลม", "ลม", "气缸", "エアシリンダ", "xi lanh khí", "silinder pneumatik", "공압", "zylinder"],
    "pump pipe flow": ["ปั๊ม", "ท่อ", "อัตราการไหล", "泵", "管道", "ポンプ", "配管", "bơm", "ống", "pompa", "pipa", "펌프", "pumpe", "rohr", "bomba", "tubería"],
    "steam heating": ["ไอน้ำ", "การให้ความร้อน", "蒸汽", "蒸気", "hơi nước", "uap", "증기", "dampf", "vapor"],
    "cooling freezing refrigeration": ["ทำความเย็น", "แช่แข็ง", "制冷", "冷冻", "冷凍", "làm lạnh", "pendingin", "냉동", "kühlung", "refrigeración"],
    "cleaning cip hygiene": ["ล้าง", "ทำความสะอาด", "สุขอนามัย", "清洗", "洗浄", "vệ sinh", "pembersihan", "세척", "reinigung", "limpieza"],
    "packaging": ["บรรจุภัณฑ์", "แพ็ค", "บรรจุ", "包装", "包装機", "đóng gói", "kemasan", "포장", "verpackung", "envasado"],
    "palletising pallet": ["พาเลท", "托盘", "パレット", "pallet", "팔레트", "palette", "paletizado"],
    "proposal quotation": ["ใบเสนอราคา", "ข้อเสนอ", "报价", "見積", "báo giá", "penawaran", "견적", "angebot", "cotización"],
    "flowchart workflow": ["ผังงาน", "โฟลว์ชาร์ต", "ขั้นตอนการทำงาน", "流程图", "フローチャート", "lưu đồ", "diagram alir", "순서도", "ablaufdiagramm", "diagrama de flujo"],
    "maintenance": ["บำรุงรักษา", "ซ่อมบำรุง", "维护", "保守", "bảo trì", "perawatan", "정비", "wartung", "mantenimiento"],
    "safety risk": ["ความปลอดภัย", "ความเสี่ยง", "安全", "风险", "リスク", "an toàn", "keselamatan", "안전", "sicherheit", "seguridad"],
    "electrical panel wiring": ["ตู้ไฟ", "ตู้คอนโทรล", "ไฟฟ้า", "电气", "电柜", "制御盤", "điện", "panel listrik", "전기", "schaltschrank", "eléctrico"],
    "inverter vfd drive": ["อินเวอร์เตอร์", "变频器", "インバータ", "biến tần", "인버터", "frequenzumrichter", "variador"],
    "simulation code python": ["จำลอง", "เขียนโค้ด", "โปรแกรม", "仿真", "代码", "シミュレーション", "mô phỏng", "simulasi", "시뮬레이션"],
    "utilities power electricity": ["สาธารณูปโภค", "กำลังไฟ", "公用工程", "用役", "tiện ích", "utilitas", "유틸리티"],
    "egg tray": ["ไข่", "ถาด", "鸡蛋", "卵", "trứng", "telur", "계란"],
}


def expand(text: str) -> str:
    """text + English keywords for any glossary term it contains."""
    low = text.lower()
    extra = [en for en, terms in GLOSSARY.items() if any(t.lower() in low for t in terms)]
    return text if not extra else text + " " + " ".join(extra)
