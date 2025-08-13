# v2ray_api.py
import requests
from typing import Optional

class V2RayPanelError(Exception):
    pass

class V2RayPanel:
    def __init__(self, base_url: str, api_key: str, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def create_account(self, username: str, inbound: dict, traffic_mb: int, duration_days: int) -> dict:
        """
        ساخت حساب جدید در پنل.
        body و مسیرها باید بسته به API پنل تنظیم شود.
        برگشت: dict شامل حداقل { "id": "...", "cfg_link": "..."}
        """
        url = f"{self.base_url}/api/accounts"  # نمونه
        payload = {
            "username": username,
            "inbound": inbound,
            "traffic_mb": traffic_mb,
            "duration_days": duration_days
        }
        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        if r.status_code not in (200,201):
            raise V2RayPanelError(f"Create account failed: {r.status_code} {r.text}")
        return r.json()

    def delete_account(self, account_id: str) -> bool:
        url = f"{self.base_url}/api/accounts/{account_id}"
        r = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return r.status_code in (200,204)

    def get_account_config(self, account_id: str) -> dict:
        url = f"{self.base_url}/api/accounts/{account_id}/config"
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        if r.status_code != 200:
            raise V2RayPanelError(f"Get config failed: {r.status_code} {r.text}")
        return r.json()

# اگر API پنل سنایی مستندات مشخصی داره اینجا endpointها را متناسب تغییر بده.
