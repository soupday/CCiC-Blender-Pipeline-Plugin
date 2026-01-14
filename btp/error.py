import RLPy
from typing import List
from enum import IntEnum


class ErrorCode(IntEnum):
    SPOTLIGHT_01 = 1001
    REPLACE_MESH_01 = 1002

REPORT: 'ErrorReport' = None


def get_error_report() -> 'ErrorReport':
    global REPORT
    if not REPORT:
        REPORT = ErrorReport()
    return REPORT


def error_reset():
    error_report = get_error_report()
    error_report.reset()


def error_report(code: ErrorCode):
    error_report = get_error_report()
    error_report.add(code)


def error_show():
    error_report = get_error_report()
    error_report.show()


class ErrorReport():

    error_codes: List[ErrorCode] = None

    error_id = {
        ErrorCode.SPOTLIGHT_01: "SPOTLIGHT_01",
        ErrorCode.REPLACE_MESH_01: "REPLACE_MESH_01",
    }

    error_text = {
        ErrorCode.SPOTLIGHT_01: "The Spotlight API GetSpotLightBeam() always throws errors, the spotlight data will not be correct: CC5.05 CC4.65 IC8.65",
        ErrorCode.REPLACE_MESH_01: "Replace Mesh API does not correctly update mesh from .obj file: CC5.05 CC4.65 IC8.65",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.error_codes = []

    def add(self, code: ErrorCode):
        if code not in self.error_codes:
            self.error_codes.append(code)

    def show(self):
        if self.error_codes:
            text = "Errors Occured during the last operation ...\n\n"
            for code in self.error_codes:
                text += f"{self.error_id[code]}: {self.error_text[code]}\n\n"
            app = RLPy.RApplication.GetProductName()
            version = RLPy.RApplication.GetProductVersion()
            text += f"{app} {version[0]}.{version[1]:02d}.{version[2]}"
            print(text)
            RLPy.RUi.ShowMessageBox("Error Report", text, RLPy.EMsgButton_Ok)

