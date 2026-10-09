def key(row):
    # Old single-warehouse bridge feeds have globally unique event IDs.
    return row['event_id']

def collapsed(rows):
    return {key(row): row for row in rows}
