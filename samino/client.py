import os
import warnings
from base64 import b64encode
from binascii import hexlify
from time import time as timestamp
from typing import BinaryIO, Union
from uuid import UUID

from .lib.objects import *
from .lib import headers, util
from .lib.sessions import Session
from .sockets import Wss


class Client(Wss, Session):
    def __init__(
            self,
            deviceId: str = None, 
            proxies: dict = None, 
            trace: bool = False, 
            http_proxy_port: str = None,
            http_proxy_host: str = None,
            proxy_type: str = None, 
            http_proxy_auth: tuple = None
    ):
        """
        Initializes a new client instance.

        Parameters:
            
        - deviceId (str, optional): The device ID for the client.
        
        - proxies (dict, optional): A dictionary containing proxy settings for requests.
        
        - trace (bool, optional): Indicates whether tracing should be enabled. Defaults to False.
        
        - http_proxy_port (str, optional): The port for the WSS proxy.
        
        - http_proxy_host (str, optional): The host address for the WSS proxy.
        
        - proxy_type (str, optional): The type of proxy being used for the WSS. 
        
        - http_proxy_auth (tuple, optional): A tuple containing the username and password for WSS proxy authentication.
        """
        self.trace = trace
        self.proxies = proxies
        self.deviceId = deviceId if deviceId else util.generateDevice()
        headers.staticDevice = self.deviceId

        Wss.__init__(
            self, self,
            trace=self.trace,
            http_proxy_port=http_proxy_port,
            http_proxy_host=http_proxy_host,
            proxy_type=proxy_type,
            http_proxy_auth=http_proxy_auth
        )
        Session.__init__(self, proxies=self.proxies, staticDevice=self.deviceId)

    def change_lang(self, lang: str = "ar-SY"):
        self.updateHeaders(lang=lang)

    def sid_login(self, sid: str, socket=False):
        self.settings(
            user_session=sid if "sid=" in sid else f"sid={sid}",
        )
        info = self.get_account_info()
        if socket: self.launch()
        return info

    def login(
            self,
            email: str = None,
            password: str = None,
            secret: str = None,
            socket: bool = False,
            clientType: int = 100
    ):

        if not ((email and password) or secret):
            raise ValueError("Please provide VALID login info")
        data = {
            "email": email if email else "",
            "secret": f"0 {password}" if password else secret,
            "clientType": clientType,
            "action": "normal",
            "deviceID": self.deviceId,
            "v": 2,
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/auth/login", data)
        self.settings(
            user_userId=req["auid"],
            user_session=f'sid={req["sid"]}',
            user_secret=secret if secret else req["secret"],
        )
        if socket: self.launch()
        return Login(req)

    def logout(self):
        data = {
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/auth/logout", data)
        self.settings()  # Resets the sid and uid and secret to None in sessions.py

        if self.isOpened: self.close()
        return Json(req)

    def check_device(self, deviceId: str):
        data = {
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000),
            "clientType": 100,
        }
        self.headers["NDCDEVICEID"] = deviceId
        req = self.postRequest("/g/s/device/", data)
        return Json(req)

    def upload_image(self, image: BinaryIO):
        image.seek(0)
        newHeaders = {"content-type": "image/jpg", "content-length": str(os.fstat(image.fileno()).st_size)}
        return self.postRequest("/g/s/media/upload", data=image, newHeaders=newHeaders)["mediaValue"]

    def upload_sticker(self, image: BinaryIO):
        newHeaders = {"content-type": "video/mp4"}
        return self.postRequest("/g/s/media/upload/target/sticker", data=image, newHeaders=newHeaders)["mediaValue"]

    def send_verify_code(self, email: str, deviceId: str):
        data = {
            "identity": email,
            "type": 1,
            "level": 2,
            "purpose": "reset-password",
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/auth/request-security-validation", data)
        return Json(req)

    def accept_host(self, requestId: str, chatId: str):
        req = self.postRequest(
            f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"
        )
        return Json(req)

    def verify_account(self, email: str, code: str):
        data = {
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.deviceId,
        }
        req = self.postRequest("/g/s/auth/activate-email", data)
        return Json(req)

    def restore(self, email: str, password: str):
        data = {
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/account/delete-request/cancel", data)
        return Json(req)

    def delete_account(self, password: str = None):
        data = {
            "deviceID": self.deviceId,
            "secret": f"0 {password}",
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/account/delete-request", data)
        return Json(req)

    def get_account_info(self):
        req = self.getRequest("/g/s/account")
        return Account(req["account"])

    def claim_coupon(self):
        req = self.postRequest("/g/s/coupon/new-user-coupon/claim")
        return Json(req)

    def change_amino_id(self, aminoId: str = None):
        data = {"aminoId": aminoId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest("/g/s/account/change-amino-id", data)
        return Json(req)

    def get_my_communities(self, start: int = 0, size: int = 25):
        req = self.getRequest(f"/g/s/community/joined?v=1&start={start}&size={size}")
        return CommunityList(req["communityList"]).CommunityList

    def get_chat_threads(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/g/s/chat/thread?type=joined-me&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def get_chat_info(self, chatId: str):
        req = self.getRequest(f"/g/s/chat/thread/{chatId}")
        return Thread(req["thread"]).Thread

    def leave_chat(self, chatId: str):
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def join_chat(self, chatId: str):
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def start_chat(self,
        userId: Union[str, list] = None,
        message: str = None,
        title: str = None,
        content: str = None,
        isGlobal: bool = False,
        publishToGlobal: bool = False,
        chatType: int = None,
    ):

        if userId:
            if isinstance(userId, str):
                userId = [userId]
        else:
            userId = []

        data = {
            "title": title,
            "inviteeUids": userId,
            "initialMessageContent": message,
            "content": content,
            "timestamp": int(timestamp() * 1000),
        }

        if isGlobal is True:
            data["type"] = 2; data["eventSource"] = "GlobalComposeMenu"
        else:
            data["type"] = 0

        if chatType:
            data["type"] = chatType

        if publishToGlobal is True:
            data["publishToGlobal"] = 1
        else:
            data["publishToGlobal"] = 0

        req = self.postRequest(f"/g/s/chat/thread", data)
        return Thread(req['thread']).Thread

    def get_from_link(self, link: str):
        req = self.getRequest(f"/g/s/link-resolution?q={link}")
        return FromCode(req["linkInfoV2"]["extensions"]).FromCode

    def edit_profile(
            self,
            nickname: str = None,
            content: str = None,
            icon: BinaryIO = None,
            backgroundColor: str = None,
            backgroundImage: str = None,
            defaultBubbleId: str = None,
    ):
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000),
        }

        if content:
            data["content"] = content
        if nickname:
            data["nickname"] = nickname
        if icon:
            data["icon"] = self.upload_image(icon)
        if backgroundColor:
            data["extensions"]["style"]["backgroundColor"] = backgroundColor
        if defaultBubbleId:
            data["extensions"] = {"defaultBubbleId": defaultBubbleId}
        if backgroundImage:
            data["extensions"]["style"] = {
                "backgroundMediaList": [[100, backgroundImage, None, None, None]]
            }

        req = self.postRequest(f"/g/s/user-profile/{self.uid}", data)
        return Json(req)

    def flag_community(self, comId: str, reason: str, flagType: int):
        data = {
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{comId}/s/g-flag", data)
        return Json(req)

    def leave_community(self, comId: str):
        req = self.postRequest(f"/x{comId}/s/community/leave")
        return Json(req)

    def join_community(self, comId: str, InviteId: str = None):
        data = {"timestamp": int(timestamp() * 1000)}

        if InviteId:
            data["invitationId"] = InviteId

        req = self.postRequest(f"/x{comId}/s/community/join", data)
        return Json(req)

    def flag(
            self,
            reason: str,
            flagType: str = "spam",
            userId: str = None,
            wikiId: str = None,
            blogId: str = None,
    ):
        types = {
            "violence": 106,
            "hate": 107,
            "suicide": 108,
            "troll": 109,
            "nudity": 110,
            "bully": 0,
            "off-topic": 4,
            "spam": 2,
        }

        data = {"message": reason, "timestamp": int(timestamp() * 1000)}

        if flagType in types:
            data["flagType"] = types.get(flagType)
        else:
            raise TypeError("choose a certain type to report")

        if userId:
            data["objectId"] = userId
            data["objectType"] = 0
        elif blogId:
            data["objectId"] = blogId
            data["objectType"] = 1
        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = 2
        else:
            raise TypeError("Please put blog or user or wiki Id")

        req = self.postRequest("/g/s/flag", data)
        return Json(req)

    def unfollow(self, userId: str):
        req = self.postRequest(f"/g/s/user-profile/{userId}/member/{self.uid}")
        return Json(req)

    def follow(self, userId: Union[str, list]):
        data = {"timestamp": int(timestamp() * 1000)}

        if isinstance(userId, str):
            link = f"/g/s/user-profile/{userId}/member"
        elif isinstance(userId, list):
            data["targetUidList"] = userId
            link = f"/g/s/user-profile/{self.uid}/joined"
        else:
            raise TypeError(f"Please use either str or list[str] not {type(userId)}")

        req = self.postRequest(link, data)
        return Json(req)

    def get_member_following(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/joined?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_followers(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/member?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_visitors(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}"
        )
        return VisitorsList(req["visitors"]).VisitorsList

    def get_blocker_users(self, start: int = 0, size: int = 25):
        req = self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockerUidList"]

    def get_blocked_users(self, start: int = 0, size: int = 25):
        req = self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockedUidList"]

    def get_wall_comments(
            self, userId: str, sorting: str = "newest", start: int = 0, size: int = 25
    ):
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("حط تايب يا حمار")

        req = self.getRequest(
            f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}"
        )
        return CommentList(req["commentList"]).CommentList

    def get_blog_comments(
            self,
            wikiId: str = None,
            blogId: str = None,
            sorting: str = "newest",
            size: int = 25,
            start: int = 0,
    ):
        sorting = sorting.lower().replace("top", "vote")

        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("Please insert a valid sorting")
        if blogId:
            link = (
                f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
            )
        elif wikiId:
            link = (
                f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
            )
        else:
            raise TypeError("Please choose a wiki or a blog")

        req = self.getRequest(link)
        return CommentList(req["commentList"]).CommentList

    def send_message(
            self,
            chatId: str,
            message: str = None,
            messageType: int = 0,
            file: BinaryIO = None,
            fileType: str = None,
            replyTo: str = None,
            mentionUserIds: Union[list, str] = None,
            stickerId: str = None,
            snippetLink: str = None,
            ytVideo: str = None,
            snippetImage: BinaryIO = None,
            embedId: str = None,
            embedType: int = None,
            embedLink: str = None,
            embedTitle: str = None,
            embedContent: str = None,
            embedImage: BinaryIO = None,
    ):

        if message is not None and file is None:
            message = message.replace("[@", "‎‏").replace("@]", "‬‭")

        mentions = []
        if mentionUserIds:
            if isinstance(mentionUserIds, list):
                for mention_uid in mentionUserIds:
                    mentions.append({"uid": mention_uid})
            mentions.append({"uid": mentionUserIds})

        if embedImage:
            if not isinstance(embedImage, str):
                embedImage = [[100, self.upload_image(embedImage), None]]
            embedImage = [[100, embedImage, None]]

        data = {
            "type": messageType,
            "content": message,
            "attachedObject": {
                "objectId": embedId,
                "objectType": embedType,
                "link": embedLink,
                "title": embedTitle,
                "content": embedContent,
                "mediaList": embedImage,
            },
            "extensions": {"mentionedArray": mentions},
            "clientRefId": int(timestamp() / 10 % 100000000),
            "timestamp": int(timestamp() * 1000),
        }

        if replyTo:
            data["replyMessageId"] = replyTo

        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3

        if snippetLink and snippetImage:
            data["attachedObject"] = None
            data["extensions"]["linkSnippetList"] = [
                {
                    "link": snippetLink,
                    "mediaType": 100,
                    "mediaUploadValue": b64encode(snippetImage.read()).decode(),
                    "mediaUploadValueContentType": "image/png",
                }
            ]

        if ytVideo:
            data["content"] = None
            data["mediaType"] = 103
            data["mediaValue"] = ytVideo

        if file:
            data["content"] = None
            if fileType == "audio":
                data["type"] = 2
                data["mediaType"] = 110

            elif fileType == "image":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/jpg"
                data["mediaUhqEnabled"] = False

            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = False

            else:
                raise TypeError(fileType)

            data["mediaUploadValue"] = b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None

        req = self.postRequest(f"/g/s/chat/thread/{chatId}/message", data)
        return Json(req)

    def get_community_info(self, comId: str):
        link = (
            f"/g/s-x{comId}/community/info"
            f"?withInfluencerList=1"
            f"&withTopicList=true"
            f"&influencerListOrderStrategy=fansCount"
        )
        req = self.getRequest(link)
        return Community(req["community"]).Community

    def mark_as_read(self, chatId: str):
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/mark-as-read")
        return Json(req)

    def delete_message(self, messageId: str, chatId: str):
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Json(req)

    def get_chat_messages(self, chatId: str, size: int = 25):
        req = self.getRequest(
            f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        )
        return GetMessages(req["messageList"]).GetMessages

    def get_message_info(self, messageId: str, chatId: str):
        req = self.getRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Message(req["message"]).Message

    def tip_coins(
            self,
            chatId: str = None,
            blogId: str = None,
            coins: int = 0,
            transactionId: str = None,
    ):
        if transactionId is None:
            transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(timestamp() * 1000),
        }

        if chatId:
            link = f"/g/s/blog/{chatId}/tipping"
        elif blogId:
            link = f"/g/s/blog/{blogId}/tipping"
        else:
            raise TypeError("please put chat or blog Id")

        req = self.postRequest(link, data)
        return Json(req)

    def reset_password(
            self, email: str, password: str, code: str, deviceId: str = None
    ):
        if deviceId is None:
            deviceId = self.deviceId

        data = {
            "secret": f"0 {password}",
            "updateSecret": f"0 {password}",
            "emailValidationContext": {
                "data": {"code": code},
                "type": 1,
                "identity": email,
                "level": 2,
                "deviceID": deviceId,
            },
            "phoneNumberValidationContext": None,
            "deviceID": deviceId,
        }
        req = self.postRequest("/g/s/auth/reset-password", data, deviceId=deviceId)
        return Json(req)

    def change_password(self, password: str, newPassword: str):
        data = {
            "secret": f"0 {password}",
            "updateSecret": f"0 {newPassword}",
            "validationContext": None,
            "deviceID": self.deviceId,
        }
        req = self.postRequest("/g/s/auth/change-password", data)
        return Json(req)

    def get_user_info(self, userId: str):
        req = self.getRequest(f"/g/s/user-profile/{userId}")
        return UserProfile(req["userProfile"]).UserProfile

    def comment(self, comment: str, userId: str = None, replyTo: str = None):
        data = {
            "content": comment,
            "stickerId": None,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000),
        }

        if replyTo:
            data["respondTo"] = replyTo
        req = self.postRequest(f"/g/s/user-profile/{userId}/g-comment", data)
        return Json(req)

    def delete_comment(self, userId: str = None, commentId: str = None):
        req = self.deleteRequest(f"/g/s/user-profile/{userId}/g-comment/{commentId}")
        return Json(req)

    def invite_by_host(self, chatId: str, userId: Union[str, list]):
        data = {"uidList": userId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/avchat-members", data)
        return Json(req)

    def kick(self, chatId: str, userId: str, rejoin: bool = True):
        rejoin = 1 if rejoin else 0
        req = self.deleteRequest(
            f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin}"
        )
        return Json(req)

    def block(self, userId: str):
        req = self.postRequest(f"/g/s/block/{userId}")
        return Json(req)

    def unblock(self, userId: str):
        req = self.deleteRequest(f"/g/s/block/{userId}")
        return Json(req)

    def get_public_chats(
            self, filterType: str = "recommended", start: int = 0, size: int = 50
    ):
        req = self.getRequest(
            f"/g/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def get_content_modules(self, version: int = 2):
        req = self.getRequest(f"/g/s/home/discover/content-modules?v={version}")
        return Json(req)

    def get_banner_ads(self, size: int = 25, pagingType: str = "t"):
        link = (
            f"/g/s/topic/0/feed/banner-ads"
            f"?moduleId=711f818f-da0c-4aa7-bfa6-d5b58c1464d0&adUnitId=703798"
            f"&size={size}"
            f"&pagingType={pagingType}"
        )

        req = self.getRequest(link)
        return ItemList(req["itemList"]).ItemList

    def get_announcements(self, lang: str = "ar", start: int = 0, size: int = 20):
        req = self.getRequest(
            f"/g/s/announcement?language={lang}&start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    def get_discover(
            self,
            discoverType: str = "discover",
            category: str = "customized",
            size: int = 25,
            pagingType: str = "t",
    ):
        link = (
            f"/g/s/topic/0/feed/community"
            f"?type={discoverType}"
            f"&categoryKey={category}"
            f"&moduleId=64da14e8-0845-47bf-946a-17403bd6aa17"
            f"&size={size}"
            f"&pagingType={pagingType}"
        )

        req = self.getRequest(link)
        return CommunityList(req["communityList"]).CommunityList

    def search_community(
            self, word: str, lang: str = "ar", start: int = 0, size: int = 25
    ):
        req = self.getRequest(
            f"/g/s/community/search?q={word}&language={lang}&completeKeyword=1&start={start}&size={size}"
        )
        return CommunityList(req["communityList"]).CommunityList

    def invite_to_voice_chat(self, userId: str = None, chatId: str = None):
        data = {"uid": userId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", data
        )
        return Json(req)

    def get_wallet_history(self, start: int = 0, size: int = 25):
        req = self.getRequest(f"/g/s/wallet/coin/history?start={start}&size={size}")
        return WalletHistory(req).WalletHistory

    def get_wallet_info(self):
        req = self.getRequest("/g/s/wallet")
        return WalletInfo(req["wallet"]).WalletInfo

    def get_all_users(self, usersType: str = "recent", start: int = 0, size: int = 25):
        """
        Types:
            - recent
            - banned
            - featured
            - leaders
            - curators
        """
        req = self.getRequest(
            f"/g/s/user-profile?type={usersType}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_chat_members(self, start: int = 0, size: int = 25, chatId: str = None):
        req = self.getRequest(
            f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2"
        )
        return UserProfileList(req["memberList"]).UserProfileList

    def get_from_id(
            self, objectId: str, comId: str = None, objectType: int = 2
    ):  # never tried
        data = {
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(timestamp() * 1000),
        }

        link = f"/g/s/link-resolution"

        if comId:
            link = f"/g/s-x{comId}/link-resolution"

        req = self.postRequest(link, data)
        return FromCode(req["linkInfoV2"]["extensions"]["linkInfo"]).FromCode

    def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, title: str = None,
                  icon: str = None, backgroundImage: str = None, content: str = None, announcement: str = None,
                  coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None,
                  publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None,
                  fansOnly: bool = None):
        data = {"timestamp": int(timestamp() * 1000)}

        if title: data["title"] = title
        if content: data["content"] = content
        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"] = {"announcement": announcement}
        if pinAnnouncement: data["extensions"] = {"pinAnnouncement": pinAnnouncement}
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}

        if publishToGlobal is not None:
            data["publishToGlobal"] = 0 if publishToGlobal else 1

        res = []

        if doNotDisturb is not None:
            data["alertOption"] = 2 if doNotDisturb else 1
            response = self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}/alert", data=data)
            res.append(Json(response))

        if pinChat is not None:
            response = self.postRequest(f"/g/s/chat/thread/{chatId}/{'pin' if pinChat else 'unpin'}", data=data)
            res.append(Json(response))

        if backgroundImage is not None:
            data = {"media": [100, backgroundImage, None], "timestamp": int(timestamp() * 1000)}
            response = self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}/background", data=data)
            res.append(Json(response))

        if coHosts is not None:
            data = {"uidList": coHosts, "timestamp": int(timestamp() * 1000)}
            response = self.postRequest(f"/g/s/chat/thread/{chatId}/co-host", data=data)
            res.append(Json(response))

        if viewOnly is not None:
            response = self.postRequest(
                f"/g/s/chat/thread/{chatId}/{'view-only/enable' if viewOnly else 'view-only/disable'}")
            res.append(Json(response))

        if canInvite is not None:
            response = self.postRequest(
                f"/g/s/chat/thread/{chatId}/{'members-can-invite/enable' if canInvite else 'members-can-invite/disable'}",
                data=data)
            res.append(Json(response))

        if canTip is not None:
            response = self.postRequest(
                f"/g/s/chat/thread/{chatId}/{'tipping-perm-status/enable' if canTip else 'tipping-perm-status/disable'}",
                data=data)
            res.append(Json(response))

        response = self.postRequest(f"/g/s/chat/thread/{chatId}", data=data)
        res.append(Json(response))
        return res

    def like_comment(self, commentId: str, userId: str = None, blogId: str = None):
        data = {"value": 4, "timestamp": int(timestamp() * 1000)}

        if userId:
            link = (
                f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1"
            )
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1"
        else:
            raise TypeError("Please put blog or user Id")

        req = self.postRequest(link, data)
        return Json(req)

    def unlike_comment(self, commentId: str, blogId: str = None, userId: str = None):
        if userId:
            link = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        else:
            raise TypeError("Please put blog or user Id")

        req = self.deleteRequest(link)
        return Json(req)

    def register(
            self, nickname: str, email: str, password: str, code: str, deviceId: str = None
    ):
        warnings.warn("register() is deprecated and no longer functional.", DeprecationWarning)

        if deviceId is None:
            deviceId = self.deviceId

        data = {
            "secret": f"0 {password}",
            "deviceID": deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "validationContext": {"data": {"code": code}, "type": 1, "identity": email},
            "type": 1,
            "identity": email,
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest("/g/s/auth/register", data)
        return Json(req)

    def remove_host(self, chatId: str, userId: str):
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/co-host/{userId}")
        return Json(req)

    def edit_comment(self, commentId: str, comment: str, userId: str):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/g/s/user-profile/{userId}/comment/{commentId}", data)
        return Comment(req).Comments

    def get_comment_info(self, commentId: str, userId: str):
        req = self.getRequest(f"/g/s/user-profile/{userId}/comment/{commentId}")
        return Comment(req).Comments

    def get_notifications(self, size: int = 25, pagingType: str = "t"):
        req = self.getRequest(f"/g/s/notification?pagingType={pagingType}&size={size}")
        return NotificationList(req).NotificationList

    def get_notices(
            self, start: int = 0, size: int = 25, noticeType: str = "usersV2", status: int = 1
    ):
        req = self.getRequest(
            f"/g/s/notice?type={noticeType}&status={status}&start={start}&size={size}"
        )
        return NoticeList(req).NoticeList

    def accept_promotion(self, requestId: str):
        req = self.postRequest(f"/g/s/notice/{requestId}/accept")
        return Json(req)

    def decline_promotion(self, requestId: str):
        req = self.postRequest(f"/g/s/notice/{requestId}/decline")
        return Json(req)

    def invite_to_chat(self, userId: Union[str, list], chatId: str = None):
        if isinstance(userId, str):
            userId = [userId]

        data = {"uids": userId, "timestamp": int(timestamp() * 1000)}

        req = self.postRequest(
            f"/g/s/chat/thread/{chatId}/member/invite", data=data
        )
        return Json(req)

    def invite_presenter(self, comId: str, userId: str, chatId: str = None):
        data = {"uid": userId, "timestamp": int(timestamp() * 1000)}

        req = self.postRequest(
            f"/x{comId}/s/chat/thread/{chatId}/vvchat-presenter/invite", data=data
        )
        return Json(req)
