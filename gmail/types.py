from typing import List, Optional
from datetime import datetime

# TODO: Update and add docstrings

class GmailEmailHeaders:
    def __init__(self, headers: List[dict]):
        self._headers = {header["name"]: header["value"] for header in headers}

    @property
    def subject(self) -> Optional[str]:
        return self._headers.get("Subject", None)

    @property
    def sender(self) -> Optional[str]:
        return self._headers.get("From", None)

    @property
    def receiver(self) -> Optional[str]:
        return self._headers.get("To", None)

    @property
    def date(self) -> Optional[str]:
        return self._headers.get("Date", None)

    @property
    def dt_date(self) -> Optional[datetime]:
        if self.date:
            try:
                return datetime.strptime(
                    self.date, "%a, %d %b %Y %H:%M:%S %z"
                )  # "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return None


class GmailMessagePayload:
    def __init__(self, data) -> None:
        self.data = data
        self.headers = GmailEmailHeaders(headers=self.data.get("headers", []))


class GmailMessageWrapper:
    def __init__(self, data):
        self.data = data
        self.payload = GmailMessagePayload(data.get("payload", {}))

    @property
    def message_id(self):
        return self.data.get("id", "")

    @property
    def thread_id(self):
        return self.data.get("threadId", "")

    @property
    def headers(self):
        return self.payload.headers

    @property
    def subject(self):
        return self.headers.subject

    @property
    def receiver(self):
        return self.headers.receiver


class GmailMessageListEntry:
    def __init__(self, json_data: dict):
        self.id: str = json_data.get("id", None)
        self.threadId: str = json_data.get("threadId", None)


class GmailMessageListResponse:
    def __init__(self, json_data: dict):
        self.messages: List[GmailMessageListEntry] = [
            GmailMessageListEntry(message) for message in json_data.get("messages", [])
        ]
        self.nextPageToken: Optional[str] = json_data.get("nextPageToken", None)
        self.resultSizeEstimate: int = json_data.get("resultSizeEstimate", 0)
