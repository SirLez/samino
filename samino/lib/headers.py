import base64
import json

from .util import generateDevice, generateSig, uuidString

# Not Required for normal samino only for async (for now at least)
# IDK if async version works either so ima leave it for later :eyes:
userId = None
staticDevice = None


class Headers:
    def __init__(self, header_device: str = None):
        self.header_device = header_device if header_device else generateDevice()

        self.app_headers = {
            "NDCDEVICEID": self.header_device,
            "NDCLANG": "en",
            "Accept-Language": "en-US",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Apple iPhoneXS iOS v16.7.2 Main/3.22.0",
            "Host": "service.aminoapps.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }

        self.web_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ar,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            "x-requested-with": "xmlhttprequest"
        }

    def updateHeaders(self, data=None, lang=None, updateDevice=None, sid=None):
        self.app_headers.update({
            "SMDEVICEID": uuidString(),
            "NDCDEVICEID": staticDevice if staticDevice else generateDevice(),
            "Content-Type": "application/x-www-form-urlencoded"
        })

        if data: self.app_headers.update(
            {"NDC-MSG-SIG": generateSig(data), "Content-Type": "application/json; charset=utf-8"})
        if updateDevice: self.app_headers.update({"NDCDEVICEID": updateDevice})
        if lang: self.app_headers.update({"NDCLANG": lang[:lang.index("-")], "Accept-Language": lang})

        if sid:
            self.web_headers.update({"cookie": sid})
            self.app_headers.update({"NDCAUTH": sid})
            decoded_sid = base64.b64decode(
                (sid.replace("sid=", "").encode() + b'=' * (-len(sid) % 4)).decode().replace('-', '+').replace('_',
                                                                                                               '/'))
            self.app_headers.update(
                {
                    "AUID":
                        json.loads(decoded_sid[decoded_sid.index(b"{"):decoded_sid.index(b"}") + 1].decode("utf-8"))[
                            "2"]
                }
            )

        self.headers_device = self.app_headers.get("NDCDEVICEID", None)
        return self.app_headers
