from datetime import datetime, timedelta
from collections import defaultdict
import logging
from consumer import OrderStatsConsumer

logger = logging.getLogger(__name__)

class WindowedStatsConsumer(OrderStatsConsumer):
    def __init__(self, *args, window_seconds=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_seconds = window_seconds
        self.order_history = []

    def update_stats(self, order):
        now = datetime.now()
        categories = [item['category'] for item in order['items']]
        city = order['customer']['city']
        self.order_history.append((now, order['total_amount'], categories, city))
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.order_history = [
            entry for entry in self.order_history if entry[0] >= cutoff
        ]

        self.stats['total_orders'] = len(self.order_history)
        self.stats['total_revenue'] = 0.0
        self.stats['orders_by_category'] = defaultdict(int)
        self.stats['orders_by_city'] = defaultdict(int)
        for ts, amount, cats, city in self.order_history:
            self.stats['total_revenue'] += amount
            for cat in cats:
                self.stats['orders_by_category'][cat] += 1
            self.stats['orders_by_city'][city] += 1

        self.stats['recent_orders'].append({
            'order_id': order['order_id'],
            'customer': order['customer']['name'],
            'total': order['total_amount'],
            'time': order['timestamp']
        })
        if len(self.stats['recent_orders']) > 10:
            self.stats['recent_orders'].pop(0)


if __name__ == "__main__":
    consumer = WindowedStatsConsumer(group_id='windowed_stats_group', window_seconds=60)
    consumer.run()