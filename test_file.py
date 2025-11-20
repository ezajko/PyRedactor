
class TestClass:
    def __init__(self):
        # TEMPORARILY DISABLED OCR LANGUAGE DETECTION TO AVOID HANGS
        # available_langs = self.get_available_ocr_languages()
        available_langs = ["eng"]  # Default to English

        if available_langs:
            self.ocr_lang = available_langs[0]
        else:
            self.ocr_lang = "eng"

if __name__ == "__main__":
    test = TestClass()
