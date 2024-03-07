from typing import BinaryIO, Union

from httpx import Client
from json_minify import json_minify
from ujson import dumps

from .exception import CheckExceptions
from .headers import Headers
from .util import *

user_settings = {
    "sid": None,
    "userId": None,
    "secret": None
}


class Session(Headers):
    def __init__(self, proxies: Union[dict, str] = None, staticDevice: str = None):
        self.proxy = proxies
        self.staticDevice = staticDevice

        self.sid = user_settings["sid"]
        self.uid = user_settings["userId"]
        self.secret = user_settings["secret"]

        Headers.__init__(self, header_device=self.staticDevice)
        self.session = Client(proxies=self.proxy, timeout=20)

        self.deviceId = self.header_device
        self.sidInit()

    def sidInit(self):
        if self.sid: self.updateHeaders(sid=self.sid)

    def settings(self, user_session: str = None, user_userId: str = None, user_secret: str = None):
        user_settings.update({
            "sid": user_session,
            "userId": user_userId,
            "secret": user_secret
        })

        self.sid = user_settings["sid"]
        self.uid = user_settings["userId"]
        self.secret = user_settings["secret"]

        self.sidInit()

    def postRequest(self, url: str, data: Union[str, dict, BinaryIO, bytes] = None, newHeaders: dict = None,
                    webRequest: bool = False, minify: bool = False, deviceId: str = None):
        if newHeaders: self.app_headers.update(newHeaders)

        if isinstance(data, dict):
            data = json_minify(dumps(data)) if minify else dumps(data)
            head = self.updateHeaders(data=data, sid=self.sid)
        elif isinstance(data, BinaryIO):
            head = self.updateHeaders(data=data, sid=self.sid)
        else:
            head = self.updateHeaders(data=None, sid=self.sid)

        req = self.session.post(
            url=webApi(url) if webRequest else api(url),
            data=data,
            files={"file": data} if isinstance(data, BinaryIO) else None,
            headers=head
        )
        if newHeaders: self.app_headers.pop("content-length")
        return CheckExceptions(req.json()) if req.status_code != 200 else req.json()

    def getRequest(self, url: str):
        req = self.session.get(url=api(url), headers=self.updateHeaders())
        return CheckExceptions(req.json()) if req.status_code != 200 else req.json()

    def deleteRequest(self, url: str):
        req = self.session.delete(url=api(url), headers=self.updateHeaders())
        return CheckExceptions(req.json()) if req.status_code != 200 else req.json()
