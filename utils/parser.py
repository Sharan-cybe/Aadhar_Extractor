from lxml import etree
import base64
import os


def parse_aadhaar_xml(xml_path: str, output_dir: str = "temp"):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_path, parser)
    root = tree.getroot()

    # -------------------------
    # masked aadhaar number
    # -------------------------
    reference_id = root.attrib.get("referenceId")

    masked_uid = (
        root.attrib.get("uid")
        or root.attrib.get("maskedUid")
    )

    # If UIDAI did not provide masked UID
    # create masked number using first 4 digits of referenceId
    if masked_uid is None and reference_id:
        last4 = reference_id[:4]   # first 4 digits
        masked_uid = f"XXXX-XXXX-{last4}"

    # -------------------------
    # Aadhaar data
    # -------------------------
    uid_data = root.find(".//UidData")
    if uid_data is None:
        raise ValueError("Invalid Aadhaar XML")

    poi = uid_data.find(".//Poi")
    poa = uid_data.find(".//Poa")
    pht = uid_data.find(".//Pht")

    if poi is None or pht is None:
        raise ValueError("Missing Aadhaar fields")

    # -------------------------
    # personal info
    # -------------------------
    name = poi.attrib.get("name")
    dob = poi.attrib.get("dob")
    gender = poi.attrib.get("gender")
# father / guardian name
    father_name = None

    if poa is not None:
        careof = poa.attrib.get("careof")

    if careof:
        father_name = careof.replace("S/O ", "").replace("D/O ", "").replace("W/O ", "")

    # -------------------------
    # address
    # -------------------------
    address = {}
    if poa is not None:
        address = {
            "house": poa.attrib.get("house"),
            "street": poa.attrib.get("street"),
            "location": poa.attrib.get("loc"),
            "city": poa.attrib.get("vtc"),
            "district": poa.attrib.get("dist"),
            "state": poa.attrib.get("state"),
            "pincode": poa.attrib.get("pc")
        }

    # -------------------------
    # decode photo
    # -------------------------
    photo_bytes = base64.b64decode(pht.text)
    photo_path = os.path.join(output_dir, "photo.jpg")

    with open(photo_path, "wb") as f:
        f.write(photo_bytes)

    return {
        "masked_aadhaar": masked_uid,
        "name": name,
        "dob": dob,
        "gender": gender,
        "father_name": father_name,
        "address": address,
        "photo_path": photo_path
    }