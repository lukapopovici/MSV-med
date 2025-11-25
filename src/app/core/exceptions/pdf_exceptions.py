class PdfError(Exception):
    pass

class PdfGenerationError(PdfError):
    pass

class PdfTemplateError(PdfError):
    pass