import zipfile
import os

def extract_zip(zip_path: str, share_code: str, extract_to: str):
    try:
        # open the actual zip path passed from main.py
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(path=extract_to, pwd=bytes(share_code, "utf-8"))

        # find xml ONLY inside this session folder
        for file in os.listdir(extract_to):
            if file.lower().endswith(".xml"):
                return os.path.join(extract_to, file)

        return None

    except RuntimeError:
        raise ValueError("Wrong share code or corrupted ZIP")
