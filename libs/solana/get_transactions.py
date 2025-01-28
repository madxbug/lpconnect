import asyncio
import sys
from typing import List

from solders.pubkey import Pubkey
from solders.transaction_status import EncodedConfirmedTransactionWithStatusMeta


async def get_all_signatures(client, account_address):
    pubkey = Pubkey.from_string(account_address)
    all_signatures = []
    before = None

    while True:
        try:
            response = await client.get_signatures_for_address(
                pubkey,
                limit=1000,  # Maximum allowed by the API
                before=before
            )
            signatures = response.value
            if not signatures:
                if before is None:
                    sys.stderr.write("Wasn't able to fetch any signatures")
                break
            all_signatures.extend(signatures)
            before = signatures[-1].signature
        except Exception as e:
            sys.stderr.write(f"Error fetching signatures: {e}")
            break

    return all_signatures


async def get_transactions_batch(client, signatures, batch_size=100) -> List[EncodedConfirmedTransactionWithStatusMeta]:
    transactions = []
    for i in range(0, len(signatures), batch_size):
        batch = signatures[i:i + batch_size]
        tasks = [client.get_transaction(sig.signature) for sig in batch]
        batch_transactions = await asyncio.gather(*tasks, return_exceptions=True)
        for sig, tx_response in zip(batch, batch_transactions):
            if isinstance(tx_response, Exception):
                sys.stderr.write(f"Transaction {sig.signature} failed with error: {tx_response}")
                continue  # Skip this transaction
            if tx_response.value:
                transactions.append(tx_response.value)
    return transactions


async def get_all_transactions(client, account_address) -> List[EncodedConfirmedTransactionWithStatusMeta]:
    signatures = await get_all_signatures(client, account_address)
    return await get_transactions_batch(client, signatures)
