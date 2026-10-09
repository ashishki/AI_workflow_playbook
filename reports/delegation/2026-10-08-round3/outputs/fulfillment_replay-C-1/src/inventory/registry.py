from src.common.errors import conflict

class Registry:
    def __init__(self):
        self.operations = {}

    def accept(self, row):
        identity = row['tenant'], row['warehouse'], row['operation_id']
        payload = (row['order_id'], row['sku'], row['action'], row['qty'])
        if identity in self.operations:
            if self.operations[identity] != payload:
                conflict('inventory', identity)
            return False
        self.operations[identity] = payload
        return True
