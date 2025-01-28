import logging
from typing import List, Any, Dict

import base58

from config.constants import LPCONNECT
from libs.meteora.idl.meteora_dllm.events.decoder import EventDecoder, DLMMEvent
from libs.meteora.idl.meteora_dllm.program_id import PROGRAM_ID_STR

logger = logging.getLogger(LPCONNECT)


def helius_webhook_parse_dlmm_events(transaction: Dict[str, Any]) -> List[DLMMEvent]:
    events = []
    meta = transaction.get('meta', {})
    tx = transaction.get('transaction', {})
    message = tx.get('message', {})

    if not all([meta, tx, message]) or meta.get('err') is not None:
        return events

    account_keys = message.get('accountKeys', [])

    for ix in meta.get('innerInstructions', []):
        for iix in ix.get('instructions', []):
            program_id_index = iix.get('programIdIndex', 0)
            if program_id_index < len(account_keys):
                if account_keys[program_id_index] != PROGRAM_ID_STR:
                    continue
                ix_data = base58.b58decode(iix.get('data', ''))
                event_data = ix_data[8:]
                try:
                    events.append(EventDecoder.decode_event(event_data, transaction.get('blockTime', 0),
                                                            transaction.get('transaction', {}).get('signatures',
                                                                                                   ['N/A'])[0]))
                except:
                    logger.error(f"Failed to decode event {event_data}")

    return events
