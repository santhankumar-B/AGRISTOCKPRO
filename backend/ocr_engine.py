import io
import re
import cv2
import hashlib
import logging
import numpy as np
from PIL import Image
from datetime import datetime

logger = logging.getLogger("agristock.ocr")
logger.setLevel(logging.INFO)

KNOWN_SUPPLIERS = [
    {"name": "NOVA AGRITECH LIMITED", "gst": "36AACCN8771A2ZH", "phone": "7995084789", "address": "Sy No 251/A, Singannaguda, TG"},
    {"name": "NOVA AGRI SCIENCES PVT LTD", "gst": "36AADCN9236F2ZC", "phone": "7995084789", "address": "Sy No 251/A1, Singannaguda, TG"},
    {"name": "NEW INDIA CROP SCIENCE", "gst": "37AWWPB6419N1ZS", "phone": "9703835362", "address": "D.No 17-01-272-03, Rapthadu, Anantapuramu AP"},
    {"name": "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "gst": "37ADHPV2108G1ZJ", "phone": "9490583999", "address": "Gooty Road, Anantapuramu AP"},
    {"name": "ANU AGRITECH PRIVATE LIMITED", "gst": "35ABDCA9590H1ZA", "phone": "8019405807", "address": "Bollaram Ind Area, Hyd TS"},
    {"name": "SIRIGUPPA AGRO AGENCIES", "gst": "37AFVPS8565E1ZJ", "phone": "9246863863", "address": "Gandhi Bazaar, Anantapuramu AP"},
    {"name": "BIOSTADT INDIA LIMITED", "gst": "37ACCB1830G1ZZ", "phone": "9848012345", "address": "Vijayawada, AP"},
    {"name": "GHARDA CHEMICALS LIMITED", "gst": "37AAACG1255E1Z0", "phone": "9985373894", "address": "Bellary Road, Kurnool AP"},
    {"name": "T. STANES AND COMPANY LIMITED", "gst": "37AAACT7126P1ZU", "phone": "6374712405", "address": "Bellary Road, Kurnool AP"},
    {"name": "RAMCIDES CROP SCIENCE PVT LTD", "gst": "37AACCR4421K1ZO", "phone": "9440123456", "address": "Kurnool AP"},
    {"name": "RAVA AGRI CHEMICALS PVT LTD", "gst": "37AAECR5394P1ZI", "phone": "9849012345", "address": "Hyderabad TS"},
    {"name": "SVS AGRI SOLUTIONS", "gst": "37BVZPS4763H1ZJ", "phone": "9440567890", "address": "Anantapuramu AP"},
    {"name": "COROMANDEL INTERNATIONAL LIMITED", "gst": "37AAACC0128C1Z6", "phone": "9848000000", "address": "Visakhapatnam AP"},
    {"name": "INDIAN FARMERS FERTILISER COOPERATIVE LIMITED", "gst": "37AAATI0012A1Z9", "phone": "9848111111", "address": "Vijayawada AP"},
]


def find_tesseract_cmd():
    import os
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def extract_raw_text(file_bytes: bytes, filename: str = "") -> str:
    """Extracts text from PDF or Image file payload."""
    raw_text = ""
    is_pdf = filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF")

    if is_pdf:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            text_pages = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    text_pages.append(txt)
            raw_text = "\n".join(text_pages)
            print(f"[OCR Engine] PDF text extracted ({len(raw_text)} chars)")
        except Exception as e:
            print(f"[OCR Engine] PyPDF extraction notice: {e}")

    if not raw_text.strip():
        try:
            import pytesseract
            t_cmd = find_tesseract_cmd()
            if t_cmd:
                pytesseract.pytesseract.tesseract_cmd = t_cmd

            pil_img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
            raw_text = pytesseract.image_to_string(pil_img)
            print(f"[OCR Engine] Pytesseract image text extracted ({len(raw_text)} chars)")
        except Exception as e:
            print(f"[OCR Engine] Pytesseract notice: {e}")

    return raw_text.strip()



def parse_invoice_text(raw_text: str, filename: str = "", file_bytes: bytes = b"") -> dict:
    """Parses raw OCR/PDF text into structured invoice fields."""
    filename_upper = filename.upper()
    text_upper = raw_text.upper()
    file_hash = hashlib.md5(file_bytes).hexdigest() if file_bytes else "00000000"
    hash_num = int(file_hash[:8], 16)

    # 1. Vendor / Supplier Matching
    supplier_name = ""
    supplier_gst = ""
    supplier_phone = ""
    supplier_address = ""

    # Check known suppliers list first
    for sup in KNOWN_SUPPLIERS:
        name_words = [w for w in sup["name"].split() if len(w) > 3 and w not in ["LIMITED", "PRIVATE", "PVT", "COMPANY"]]
        if any(w in filename_upper or w in text_upper for w in name_words):
            supplier_name = sup["name"]
            supplier_gst = sup["gst"]
            supplier_phone = sup.get("phone", "")
            supplier_address = sup.get("address", "")
            break
        if sup["gst"] in text_upper:
            supplier_name = sup["name"]
            supplier_gst = sup["gst"]
            supplier_phone = sup.get("phone", "")
            supplier_address = sup.get("address", "")
            break

    # Fallback to GST match if supplier not found in known list
    if not supplier_gst:
        gst_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', text_upper)
        if gst_match:
            supplier_gst = gst_match.group(0)

    if not supplier_name:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        for line in lines[:10]:
            if any(k in line.upper() for k in ["LIMITED", "PVT", "AGRO", "AGENCIES", "TRADERS", "CROP", "CHEMICALS", "SOLUTIONS"]):
                supplier_name = line.strip()
                break

    if not supplier_name:
        supplier_name = "New Supplier"

    # 2. Invoice Number Extraction
    inv_num_match = re.search(r'(?:INVOICE|BILL|MEMO|TAX INVOICE|ACK|IRN)\s*(?:NO|NUMBER|#)?[\s:]*([A-Z0-9/\-_]{3,30})', text_upper)
    if inv_num_match:
        invoice_number = inv_num_match.group(1).strip()
    else:
        invoice_number = f"INV-{hash_num % 100000:05d}"

    # 3. Invoice Date Extraction
    date_match = re.search(r'\b(\d{4}[-/\.]\d{2}[-/\.]\d{2}|\d{2}[-/\.]\d{2}[-/\.]\d{2,4})\b', raw_text)
    if date_match:
        date_str = date_match.group(1).replace(".", "-").replace("/", "-")
        try:
            parts = date_str.split("-")
            if len(parts[0]) == 4:
                invoice_date = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            else:
                year = parts[2]
                if len(year) == 2:
                    year = f"20{year}"
                invoice_date = f"{year}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        except Exception:
            invoice_date = datetime.now().strftime("%Y-%m-%d")
    else:
        invoice_date = datetime.now().strftime("%Y-%m-%d")

    # 4. Total & Subtotal Extraction
    subtotal = 0.0
    cgst = 0.0
    sgst = 0.0
    total = 0.0

    total_match = re.search(r'(?:NET VALUE|NET AMOUNT|TOTAL VALUE|GRAND TOTAL|TOTAL INVOICE|AMOUNT CHARGEABLE)[\s:]*₹?\s*([\d,]+\.?\d*)', text_upper)
    if total_match:
        try:
            total = float(total_match.group(1).replace(",", ""))
        except ValueError:
            pass

    subtotal_match = re.search(r'(?:SUBTOTAL|TAXABLE VALUE|VALUE OF SUPPLY|BASIC PRICE)[\s:]*₹?\s*([\d,]+\.?\d*)', text_upper)
    if subtotal_match:
        try:
            subtotal = float(subtotal_match.group(1).replace(",", ""))
        except ValueError:
            pass

    cgst_match = re.search(r'CGST[\s:]*₹?\s*([\d,]+\.?\d*)', text_upper)
    if cgst_match:
        try:
            cgst = float(cgst_match.group(1).replace(",", ""))
        except ValueError:
            pass

    sgst_match = re.search(r'SGST[\s:]*₹?\s*([\d,]+\.?\d*)', text_upper)
    if sgst_match:
        try:
            sgst = float(sgst_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 5. Multi-line Line Item Extraction
    parsed_items = []
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    current_item = {}
    for i, line in enumerate(lines):
        line_u = line.upper()

        # Check for Product Name keywords e.g. "LIQUID BIONEMATON" or "HAMLA" or "NPK"
        if any(k in line_u for k in ["LIQUID", "BIONEMATON", "HAMLA", "CHLORPYRIFOS", "CYPERMETHRIN", "NPK", "SEED", "PESTICIDE", "FERTILIZER", "HERBICIDE"]):
            if not any(noise in line_u for noise in ["SEALER IN", "DEALER IN", "LICENCE", "LICENSE", "FE LNO", "PEST LNO", "SEED LNO"]):
                if current_item and current_item.get("product_name"):
                    parsed_items.append(current_item)
                    current_item = {}
                current_item["product_name"] = line.strip()
                current_item["category"] = "General"
                current_item["unit"] = "Unit"
                current_item["qty"] = 1.0
                current_item["unit_price"] = 0.0
                current_item["amount"] = 0.0
                current_item["batch_number"] = ""
                current_item["expiry_date"] = ""


        # Extract Batch / Expiry line e.g. "Batcho\Exp : BNOG2604\26-Jun-2027"
        if "BATCH" in line_u or "EXP" in line_u or "B.NO" in line_u:
            batch_m = re.search(r'(?:BATCH|B\.NO|BN|EXP)?[\s:\\]*([A-Z0-9]{4,15})', line_u)
            if batch_m:
                current_item["batch_number"] = batch_m.group(1).strip()
            exp_m = re.search(r'(\d{2}[-/\.][A-Za-z0-9]{3}[-/\.]\d{2,4}|\d{2}[-/\.]\d{2}[-/\.]\d{2,4})', line)
            if exp_m:
                current_item["expiry_date"] = exp_m.group(1).strip()

        # Extract Qty, Rate, Amount line e.g. "40.000 360.000 14400.00"
        nums = re.findall(r'\b\d+(?:\.\d+)?\b', line)
        if len(nums) >= 3 and current_item:
            try:
                q = float(nums[0])
                r = float(nums[1])
                a = float(nums[2])
                if q > 0 and r > 0 and a >= (q * r * 0.8):
                    current_item["qty"] = q
                    current_item["unit_price"] = r
                    current_item["amount"] = a
            except Exception:
                pass

    if current_item and current_item.get("product_name"):
        parsed_items.append(current_item)

    # Single-line regex backup parser
    if not parsed_items:
        for line in lines:
            match = re.search(r'^(\d+\s+)?([A-Za-z0-9\s%\-\:\(\)]+?)\s+(\d+(?:\.\d+)?)\s+(Bag|Bottle|Can|Nos|Box|Kg|Ltr|Unit|Pkt|Pack)?\s*₹?\s*([\d,]+(?:\.\d+)?)\s+₹?\s*([\d,]+(?:\.\d+)?)', line, re.IGNORECASE)
            if match:
                prod_name = match.group(2).strip()
                qty = float(match.group(3))
                unit = match.group(4) or "Unit"
                rate = float(match.group(5).replace(",", ""))
                amt = float(match.group(6).replace(",", ""))
                parsed_items.append({
                    "product_name": prod_name,
                    "category": "General",
                    "batch_number": "",
                    "expiry_date": "",
                    "unit": unit,
                    "qty": qty,
                    "unit_price": rate,
                    "discount_percent": 0.0,
                    "tax_percent": 5.0,
                    "amount": amt,
                })

    # Default 1 editable item if no text lines matched
    if not parsed_items:
        parsed_items = [
            {
                "product_name": "",
                "category": "General",
                "batch_number": "",
                "expiry_date": "",
                "unit": "Unit",
                "qty": 1.0,
                "unit_price": 0.0,
                "discount_percent": 0.0,
                "tax_percent": 0.0,
                "amount": 0.0,
            }
        ]

    calc_subtotal = sum(it.get("amount", 0) for it in parsed_items)
    if subtotal == 0.0:
        subtotal = calc_subtotal
    if total == 0.0:
        total = round(subtotal + cgst + sgst, 2)

    return {
        "supplier_name": supplier_name,
        "supplier_gst": supplier_gst,
        "supplier_phone": supplier_phone,
        "supplier_address": supplier_address,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "items": parsed_items,
        "subtotal": round(subtotal, 2),
        "discount": 0.00,
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "total": round(total, 2),
        "scan_status": "SUCCESS",
        "image_hash": file_hash[:8]
    }



def extract_invoice_data(file_bytes: bytes, filename: str = "") -> dict:
    """
    Real file OCR & text parsing controller endpoint.
    Extracts raw text from image or PDF payload and parses JSON payload for review.
    """
    print(f"\n==================== [OCR CONTROLLER STEP 1] ====================")
    print(f"[Backend Controller] Received file payload: filename='{filename}', size={len(file_bytes)} bytes")
    
    raw_text = extract_raw_text(file_bytes, filename=filename)
    print(f"\n==================== [OCR CONTROLLER STEP 2] ====================")
    print(f"[Raw Output Received from OCR/PDF Engine]:\n{raw_text if raw_text else '(No raw text detected on file)'}")
    
    result = parse_invoice_text(raw_text, filename=filename, file_bytes=file_bytes)
    print(f"\n==================== [OCR CONTROLLER STEP 3] ====================")
    print(f"[Parsed JSON Sent Back to Frontend]:\n{result}")
    print(f"=================================================================\n")
    
    return result

