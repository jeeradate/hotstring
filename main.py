import json
import os
import re
import subprocess
import threading
import time
from typing import Any

import pyperclip  # type: ignore[import-untyped]
from nicegui import app, ui
from pynput import keyboard

DATA_FILE = "hotstring_data.jason"

# ตารางเทียบแป้นพิมพ์ภาษาไทย (เกษมณี) เป็นอังกฤษตัวเล็ก
THAI_TO_ENG: dict[str, str] = {
    "ๆ": "q",
    "ไ": "w",
    "ำ": "e",
    "พ": "r",
    "ะ": "t",
    "ั": "y",
    "ี": "u",
    "ร": "i",
    "น": "o",
    "ย": "p",
    "บ": "[",
    "ล": "]",
    "ฟ": "a",
    "ห": "s",
    "ก": "d",
    "ด": "f",
    "เ": "g",
    "้": "h",
    "่": "j",
    "า": "k",
    "ส": "l",
    "ว": ";",
    "ง": "'",
    "ผ": "z",
    "ป": "x",
    "แ": "c",
    "อ": "v",
    "ิ": "b",
    "ื": "n",
    "ท": "m",
    "ม": ",",
    "ใ": ".",
    "ฝ": "/",
    "๐": "q",
    '"': "w",
    "ฎ": "e",
    "ฑ": "r",
    "ธ": "t",
    "ํ": "y",
    "๊": "u",
    "ณ": "i",
    "ฯ": "o",
    "ญ": "p",
    "ฐ": "[",
    ",": "]",
    "ฤ": "a",
    "ฆ": "s",
    "ฏ": "d",
    "โ": "f",
    "ฌ": "g",
    "็": "h",
    "๋": "j",
    "ษ": "k",
    "ศ": "l",
    "ซ": ";",
    ".": "'",
    "(": "z",
    ")": "x",
    "ฉ": "c",
    "ฮ": "v",
    "ฺ": "b",
    "์": "n",
    "?": "m",
    "ฒ": ",",
    "ฬ": ".",
    "ฦ": "/",
    "ๅ": "1",
    "/": "2",
    "_": "3",
    "ภ": "4",
    "ถ": "5",
    "ุ": "6",
    "ึ": "7",
    "ค": "8",
    "ต": "9",
    "จ": "0",
    "ข": "-",
    "ช": "=",
    "+": "1",
    "๑": "2",
    "๒": "3",
    "๓": "4",
    "๔": "5",
    "ู": "6",
    "฿": "7",
    "๕": "8",
    "๖": "9",
    "๗": "0",
    "๘": "-",
    "๙": "=",
}


def normalize_char(ch: str) -> str:
    if ch in THAI_TO_ENG:
        return THAI_TO_ENG[ch]
    return ch.lower()


def normalize_text(text: str) -> str:
    return "".join(normalize_char(c) for c in text)


# ----------------- จัดการข้อมูล JSON -----------------
def load_data() -> dict[str, dict[str, str]]:
    if not os.path.exists(DATA_FILE):
        default_data: dict[str, dict[str, str]] = {
            "hw": {
                "type": "message",
                "description": "พิมพ์คำทักทายมาตรฐาน",
                "content": "Hello World! สวัสดีครับ",
            },
            "calc": {
                "type": "run",
                "description": "เปิดโปรแกรมเครื่องคิดเลข",
                "content": "calc.exe",
            },
        }
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data: dict[str, dict[str, str]] = json.load(f)
            for k, v in data.items():
                if "description" not in v:
                    v["description"] = ""
            return data
    except Exception:
        return {}


def save_data(data: dict[str, dict[str, str]]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


hotstrings: dict[str, dict[str, str]] = load_data()


# ----------------- ระบบดักจับคีย์บอร์ด (Hotstring Engine) -----------------
class HotstringListener:
    def __init__(self) -> None:
        self.buffer: str = ""
        self.last_triggered: str = "ยังไม่มีการเรียกใช้"
        self.controller = keyboard.Controller()
        self.is_executing: bool = False
        self.listener: keyboard.Listener | None = None

    def start(self) -> None:
        if self.listener is None:
            self.listener = keyboard.Listener(on_press=self.on_press)
            self.listener.daemon = True
            self.listener.start()

    def extract_char(self, key: keyboard.Key | keyboard.KeyCode) -> str | None:
        """ดึงตัวอักษรจากปุ่มกด รองรับทั้ง char ปกติ และ Virtual Key Code (vk) บน Windows"""
        if isinstance(key, keyboard.KeyCode):
            # 1. ลองดึงจาก Virtual Key Code ก่อน (แม่นยำสุดเวลาเปลี่ยนภาษาไทย/อังกฤษบน Windows)
            vk = getattr(key, "vk", None)
            if vk is not None:
                if 65 <= vk <= 90:  # ปุ่ม A-Z
                    return chr(vk + 32)
                if 48 <= vk <= 57:  # ปุ่ม 0-9 แถวบน
                    return chr(vk)
                if 96 <= vk <= 105:  # ปุ่ม 0-9 Numpad
                    return chr(vk - 48)
                if vk in (190, 110):  # ปุ่ม . (หรือ ใ ในแป้นไทย) และจุดบน Numpad
                    return "."

            # 2. ถ้าไม่ได้ใช้ vk ให้ดึงจาก char แล้วแปลงภาษาไทยเป็นอังกฤษ
            if key.char is not None:
                return normalize_char(key.char)
        return None

    def on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if self.is_executing or key is None:
            return

        try:
            if key == keyboard.Key.backspace:
                self.buffer = self.buffer[:-1]
            elif key == keyboard.Key.space:
                self.check_and_trigger()
                self.buffer = ""
            elif key in (keyboard.Key.enter, keyboard.Key.tab, keyboard.Key.esc):
                self.buffer = ""
            else:
                ch = self.extract_char(key)
                if ch is not None:
                    self.buffer += ch
                    if len(self.buffer) > 20:
                        self.buffer = self.buffer[-20:]
        except Exception as e:
            print(f"Key listener error: {e}")

    def check_and_trigger(self) -> None:
        match = re.search(r"\.\.([a-z0-9]{1,8})$", self.buffer)
        if not match:
            return

        hs_key = match.group(1)
        if hs_key in hotstrings:
            action = hotstrings[hs_key]
            self.last_triggered = f"..{hs_key} ({action['type']})"
            bs_count = 2 + len(hs_key) + 1
            threading.Thread(
                target=self.execute_action,
                args=(bs_count, action["type"], action["content"]),
                daemon=True,
            ).start()

    def execute_action(self, bs_count: int, action_type: str, content: str) -> None:
        self.is_executing = True
        try:
            time.sleep(0.08)
            for _ in range(bs_count):
                self.controller.tap(keyboard.Key.backspace)
                time.sleep(0.015)

            if action_type == "message":
                time.sleep(0.05)
                old_clip = pyperclip.paste()
                pyperclip.copy(content)
                time.sleep(0.05)
                with self.controller.pressed(keyboard.Key.ctrl):
                    self.controller.tap("v")
                time.sleep(0.15)
                pyperclip.copy(old_clip)
            elif action_type == "run":
                subprocess.Popen(content, shell=True)
        except Exception as e:
            print(f"Execution error: {e}")
        finally:
            self.is_executing = False


listener_engine = HotstringListener()

# สำคัญมากสำหรับ native=True: ต้องเริ่ม Listener ตอนที่ Server ของแอปเริ่มทำงานแล้วเท่านั้น
app.on_startup(listener_engine.start)


# ----------------- ส่วนติดต่อผู้ใช้ด้วย NiceGUI (Desktop Mode) -----------------
@ui.page("/")
def main_page() -> None:
    ui.colors(primary="#2563eb")

    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-4"):
        # Header + แถบเช็คสถานะคีย์บอร์ดแบบ Real-time
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-0"):
                ui.label("⚡ Hotstring Manager").classes(
                    "text-2xl font-bold text-gray-800"
                )
                ui.label(
                    'พิมพ์ ".." หรือ "ใใ" ตามด้วยรหัส 1-8 ตัวอักษร แล้วกด Spacebar'
                ).classes("text-xs text-gray-500")

            with ui.row().classes(
                "items-center gap-2 bg-gray-100 px-3 py-1.5 rounded border"
            ):
                ui.badge("Active", color="green")
                buffer_label = ui.label("Buffer: (ว่าง)").classes(
                    "font-mono text-xs text-blue-700 w-36 truncate"
                )
                last_label = ui.label("ล่าสุด: -").classes("text-xs text-gray-600")

        # อัปเดตสถานะปุ่มที่พิมพ์บนหน้าจอทุกๆ 0.2 วินาที เพื่อเช็คว่าคีย์บอร์ดเข้าหรือไม่
        def update_status() -> None:
            buf = listener_engine.buffer
            buffer_label.text = f"Buffer: {buf if buf else '(ว่าง)'}"
            last_label.text = f"ล่าสุด: {listener_engine.last_triggered}"

        ui.timer(0.2, update_status)

        # การ์ดสำหรับเพิ่ม/แก้ไขข้อมูล
        with ui.card().classes("w-full p-4 shadow-sm border border-gray-200"):
            ui.label("เพิ่ม / แก้ไข Hotstring").classes("text-base font-semibold mb-1")

            with ui.row().classes("w-full gap-4 items-center"):
                hs_input = ui.input(
                    label="Hotstring (1-8 ตัว)", placeholder="เช่น hw (หรือพิมพ์ ้ไ)"
                ).classes("w-44")

                type_select = ui.select(
                    options={"message": "💬 Hot Message", "run": "🚀 Hot Run"},
                    value="message",
                    label="ชนิดคำสั่ง (Type)",
                ).classes("w-48")

                desc_input = ui.input(
                    label="คำอธิบาย (Description)",
                    placeholder="เช่น ข้อความทักทายลูกค้า, เปิดเครื่องคิดเลข",
                ).classes("flex-1")

            content_input = (
                ui.textarea(
                    label="Content (ข้อความที่ต้องการพิมพ์ หรือ คำสั่ง/Path ของแอป)",
                    placeholder="ใส่ข้อความ หรือ เช่น notepad.exe, calc.exe, C:\\path\\to\\app.exe",
                )
                .classes("w-full")
                .props("rows=2")
            )

            def add_or_update() -> None:
                raw_key = (hs_input.value or "").strip()
                norm_key = normalize_text(raw_key)
                content_val = content_input.value or ""

                if (
                    not norm_key
                    or not (1 <= len(norm_key) <= 8)
                    or not norm_key.isalnum()
                ):
                    ui.notify(
                        "Hotstring ต้องแปลงเป็นตัวอักษรภาษาอังกฤษหรือตัวเลข 1-8 ตัวเท่านั้น",
                        type="negative",
                    )
                    return
                if not content_val:
                    ui.notify("กรุณากรอก Content", type="negative")
                    return

                hotstrings[norm_key] = {
                    "type": str(type_select.value or "message"),
                    "description": (desc_input.value or "").strip(),
                    "content": content_val,
                }
                save_data(hotstrings)
                refresh_table()
                hs_input.value = ""
                desc_input.value = ""
                content_input.value = ""
                ui.notify(f'บันทึก "..{norm_key}" เรียบร้อยแล้ว!', type="positive")

            with ui.row().classes("w-full justify-end mt-2"):
                ui.button("บันทึกข้อมูล", on_click=add_or_update, icon="save")

        # ตารางแสดงรายการ Hotstring พร้อมระบบ Sort
        with ui.card().classes("w-full p-4 shadow-sm border border-gray-200"):
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label("รายการ Hotstring ทั้งหมด").classes("text-base font-semibold")

                with ui.row().classes("items-center gap-2"):
                    sort_by = (
                        ui.select(
                            options={
                                "type": "ชนิดคำสั่ง (Type)",
                                "description": "คำอธิบาย (Description)",
                                "key": "รหัส (Hotstring)",
                            },
                            value="type",
                            label="เรียงตาม (Sort by)",
                            on_change=lambda _: refresh_table(),
                        )
                        .classes("w-48")
                        .props("dense outlined")
                    )

                    sort_order = (
                        ui.select(
                            options={"asc": "น้อยไปมาก (A-Z)", "desc": "มากไปน้อย (Z-A)"},
                            value="asc",
                            label="ลำดับ",
                            on_change=lambda _: refresh_table(),
                        )
                        .classes("w-40")
                        .props("dense outlined")
                    )

            table_container = ui.column().classes("w-full gap-1")

            def delete_item(key: str) -> None:
                if key in hotstrings:
                    del hotstrings[key]
                    save_data(hotstrings)
                    refresh_table()
                    ui.notify(f'ลบ "..{key}" แล้ว', type="warning")

            def edit_item(key: str, item: dict[str, Any]) -> None:
                hs_input.value = key
                type_select.value = item.get("type", "message")
                desc_input.value = item.get("description", "")
                content_input.value = item.get("content", "")
                ui.notify(f'กำลังแก้ไข "..{key}"', type="info")

            def refresh_table() -> None:
                table_container.clear()
                with table_container:
                    if not hotstrings:
                        ui.label("ยังไม่มีข้อมูล Hotstring").classes(
                            "text-gray-400 italic py-4"
                        )
                        return

                    reverse_flag = sort_order.value == "desc"
                    if sort_by.value == "type":
                        sorted_items = sorted(
                            hotstrings.items(),
                            key=lambda item: (
                                item[1].get("type", ""),
                                item[1].get("description", "").lower(),
                            ),
                            reverse=reverse_flag,
                        )
                    elif sort_by.value == "description":
                        sorted_items = sorted(
                            hotstrings.items(),
                            key=lambda item: (
                                item[1].get("description", "").lower(),
                                item[0],
                            ),
                            reverse=reverse_flag,
                        )
                    else:
                        sorted_items = sorted(
                            hotstrings.items(),
                            key=lambda item: item[0],
                            reverse=reverse_flag,
                        )

                    # Header ของตาราง
                    with ui.row().classes(
                        "w-full items-center px-3 py-2 bg-gray-100 rounded font-semibold text-xs text-gray-600"
                    ):
                        ui.label("Hotstring").classes("w-24")
                        ui.label("ชนิด (Type)").classes("w-28")
                        ui.label("คำอธิบาย (Description)").classes("w-48")
                        ui.label("เนื้อหา / คำสั่ง (Content)").classes("flex-1")
                        ui.label("จัดการ").classes("w-20 text-right")

                    # แสดงรายการแต่ละแถว
                    for k, v in sorted_items:
                        with ui.row().classes(
                            "w-full items-center px-3 py-2 border-b border-gray-100 hover:bg-gray-50 rounded text-sm"
                        ):
                            with ui.row().classes("w-24"):
                                ui.label(f"..{k}").classes(
                                    "font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded"
                                )

                            with ui.row().classes("w-28"):
                                badge_color = (
                                    "blue" if v.get("type") == "message" else "purple"
                                )
                                badge_text = (
                                    "Hot Message"
                                    if v.get("type") == "message"
                                    else "Hot Run"
                                )
                                ui.badge(badge_text, color=badge_color)

                            ui.label(v.get("description") or "-").classes(
                                "w-48 font-medium text-gray-800 truncate pr-2"
                            )
                            ui.label(v.get("content", "")).classes(
                                "flex-1 text-gray-600 truncate pr-2"
                            )

                            with ui.row().classes("w-20 justify-end gap-1"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda _, k=k, v=v: edit_item(k, v),
                                ).props("flat round size=sm color=primary")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda _, k=k: delete_item(k),
                                ).props("flat round size=sm color=negative")

            refresh_table()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Hotstring App", native=True, window_size=(960, 720), reload=False)
