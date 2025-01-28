from typing import Optional, Dict, Any, List

import requests


class HeliusWebhookAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.helius.xyz/v0/webhooks"

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}?api-key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json() if method != 'DELETE' else {'success': True}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error during {method} request: {str(e)}")

    def create_webhook(self, webhook_url: str, transaction_types: List[str] = ["Any"],
                       account_addresses: Optional[List[str]] = None, webhook_type: str = "raw",
                       txn_status: str = "success", auth_header: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "webhookURL": webhook_url,
            "transactionTypes": transaction_types,
            "accountAddresses": account_addresses or [],
            "webhookType": webhook_type,
            "txnStatus": txn_status,
            "authHeader": auth_header
        }
        return self._make_request('POST', '', payload)

    def get_all_webhooks(self) -> List[Dict[str, Any]]:
        return self._make_request('GET', '')

    def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        return self._make_request('GET', f"/{webhook_id}")

    def edit_webhook(self, webhook_id: str, **kwargs: Any) -> Dict[str, Any]:
        existing_webhook = self.get_webhook(webhook_id)
        edit_request = {
            "webhookURL": kwargs.get("webhookURL", existing_webhook.get("webhookURL")),
            "transactionTypes": kwargs.get("transactionTypes", existing_webhook.get("transactionTypes")),
            "accountAddresses": kwargs.get("accountAddresses", existing_webhook.get("accountAddresses")),
            "accountAddressOwners": kwargs.get("accountAddressOwners", existing_webhook.get("accountAddressOwners")),
            "webhookType": kwargs.get("webhookType", existing_webhook.get("webhookType")),
            "authHeader": kwargs.get("authHeader", existing_webhook.get("authHeader")),
            "txnStatus": kwargs.get("txnStatus", existing_webhook.get("txnStatus")),
            "encoding": kwargs.get("encoding", existing_webhook.get("encoding")),
        }
        return self._make_request('PUT', f"/{webhook_id}", edit_request)

    def delete_webhook(self, webhook_id: str) -> Dict[str, bool]:
        return self._make_request('DELETE', f"/{webhook_id}")

    def append_addresses_to_webhook(self, webhook_id: str, new_addresses: List[str]) -> Dict[str, Any]:
        existing_webhook = self.get_webhook(webhook_id)
        updated_addresses = existing_webhook['accountAddresses'] + new_addresses
        if len(updated_addresses) > 100_000:
            raise ValueError("A single webhook cannot contain more than 100,000 addresses")
        return self.edit_webhook(webhook_id, accountAddresses=updated_addresses)

    def remove_addresses_from_webhook(self, webhook_id: str, addresses_to_remove: List[str]) -> Dict[str, Any]:
        existing_webhook = self.get_webhook(webhook_id)
        updated_addresses = [addr for addr in existing_webhook['accountAddresses'] if addr not in addresses_to_remove]
        return self.edit_webhook(webhook_id, accountAddresses=updated_addresses)
