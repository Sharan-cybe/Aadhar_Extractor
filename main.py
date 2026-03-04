from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
import hashlib

from utils.unzipper import extract_zip
from utils.signature_verifier import verify_uidai_xml
from utils.parser import parse_aadhaar_xml

app = FastAPI()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Aadhaar Verification Server Running"}


# ------------------------------------------------
# Generate deterministic 6-character alphanumeric ID
# ------------------------------------------------
def generate_aadhaar_id(data):

    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    unique_string = (
        str(data["name"]) +
        str(data["dob"]) +
        str(data["gender"]) +
        str(data["address"].get("pincode", ""))
    )

    hash_bytes = hashlib.sha256(unique_string.encode()).digest()

    unique_part = ""

    for b in hash_bytes[:6]:
        unique_part += charset[b % len(charset)]

    aadhaar_id = f"AAD-{unique_part}"

    return aadhaar_id


@app.post("/verify-aadhaar")
async def verify_aadhaar(
    file: UploadFile = File(...),
    share_code: str = Form(...)
):

    processing_dir = os.path.join(UPLOAD_DIR, "processing")
    os.makedirs(processing_dir, exist_ok=True)

    try:

        # -----------------------------
        # Save uploaded ZIP
        # -----------------------------
        zip_path = os.path.join(processing_dir, file.filename)

        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # -----------------------------
        # Extract XML
        # -----------------------------
        xml_path = extract_zip(zip_path, share_code, processing_dir)

        if not xml_path:
            shutil.rmtree(processing_dir, ignore_errors=True)
            return {"status": "failed", "reason": "XML not found in ZIP"}

        # -----------------------------
        # Verify Aadhaar Signature
        # -----------------------------
        valid, reason = verify_uidai_xml(xml_path)

        if not valid:
            shutil.rmtree(processing_dir, ignore_errors=True)
            return {"status": "failed", "reason": reason}

        # -----------------------------
        # Parse Aadhaar Data
        # -----------------------------
        data = parse_aadhaar_xml(xml_path, processing_dir)

        # -----------------------------
        # Generate Unique Aadhaar ID
        # -----------------------------
        aadhaar_id = generate_aadhaar_id(data)

        final_dir = os.path.join(UPLOAD_DIR, aadhaar_id)

        # -----------------------------
        # If Aadhaar already exists
        # -----------------------------
        if os.path.exists(final_dir):

            shutil.rmtree(processing_dir, ignore_errors=True)

            return {
                "status": "success",
                "aadhaar_id": aadhaar_id,
                "message": "Aadhaar already verified",
                "data": data
            }

        # -----------------------------
        # Move verified Aadhaar folder
        # -----------------------------
        shutil.move(processing_dir, final_dir)

        return {
            "status": "success",
            "aadhaar_id": aadhaar_id,
            "data": data,
            "verification": reason
        }

    except ValueError as e:

        shutil.rmtree(processing_dir, ignore_errors=True)

        return {"status": "failed", "reason": str(e)}

    except Exception as e:

        shutil.rmtree(processing_dir, ignore_errors=True)

        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )