from lxml import etree
import base64
from cryptography import x509

def verify_uidai_xml(xml_path: str):
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(xml_path, parser)
        root = tree.getroot()

        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}

        # 1. Aadhaar root must be OfflinePaperlessKyc
        if root.tag != "OfflinePaperlessKyc":
            return False, "Not Aadhaar XML"

        # 2. Must contain UidData
        uid_data = root.find(".//UidData")
        if uid_data is None:
            return False, "Missing Aadhaar data"

        # 3. Signature must exist
        signature = root.find(".//ds:Signature", ns)
        if signature is None:
            return False, "Missing digital signature"

        # 4. Certificate must exist
        cert_node = root.find(".//ds:X509Certificate", ns)
        if cert_node is None:
            return False, "Missing certificate"

        cert_der = base64.b64decode(cert_node.text.strip())
        cert = x509.load_der_x509_certificate(cert_der)

        issuer = cert.issuer.rfc4514_string()

        # UIDAI certificates always issued in India Govt PKI
        if "IN" not in issuer:
            return False, "Not UIDAI issued"

        # 5. Mandatory attributes
        poi = uid_data.find(".//Poi")
        if poi is None or "name" not in poi.attrib:
            return False, "Invalid Aadhaar structure"

        return True, "Valid Aadhaar structure"

    except Exception:
        return False, "Invalid Aadhaar file"
