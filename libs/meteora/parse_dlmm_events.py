from typing import List

import base58
from solders.transaction_status import EncodedConfirmedTransactionWithStatusMeta

from libs.meteora.idl.meteora_dllm.events.decoder import EventDecoder, DLMMEvent
from libs.meteora.idl.meteora_dllm.program_id import PROGRAM_ID


def parse_dlmm_events(transaction: EncodedConfirmedTransactionWithStatusMeta) -> List[DLMMEvent]:
    events = []
    account_keys = transaction.transaction.transaction.message.account_keys
    for ix in transaction.transaction.meta.inner_instructions:
        for iix in ix.instructions:
            program_id_index = iix.program_id_index
            if program_id_index < len(account_keys):
                if account_keys[program_id_index] != PROGRAM_ID:
                    continue
                ix_data = base58.b58decode(iix.data)
                event_data = ix_data[8:]

                events.append(EventDecoder.decode_event(event_data, transaction.block_time,
                                                        str(transaction.transaction.transaction.signatures[0])))

    return events
