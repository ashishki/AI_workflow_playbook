from src.common.errors import conflict

class Ledger:
    def __init__(self):
        self.seen = {}

    def accept(self, row):
        identity = row['tenant'], row['provider'], row['refund_id']
        payload = row['order_id'], row['amount_minor']
        if identity in self.seen:
            if self.seen[identity] != payload:
                conflict('refunds', identity)
            return False
        self.seen[identity] = payload
        return True
