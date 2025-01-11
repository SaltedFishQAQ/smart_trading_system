import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx


class Printer:
    def __init__(self):
        self.data = []

    def add_data(self, data):
        self.data.append(data)

    def print_by_datetime_and_user(self, dateStr):
        df = pd.DataFrame(self.data)
        grouped = df.groupby('datetime')
        for datetime, group in grouped:
            if datetime != dateStr:
                continue
            G = nx.DiGraph()
            for _, row in group.iterrows():
                G.add_edge(row['supplier_id'], row['consumer_id'], weight=row['amount'])

            pos = nx.spring_layout(G)
            plt.figure(figsize=(10, 7))
            nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue', font_size=10)
            labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
            plt.title(f'energy flow - {datetime}')
            plt.show()

    def print_by_mode(self):
        df = pd.DataFrame(self.data)
        mode_counts = df.groupby('mode')['amount'].count()
        plt.figure(figsize=(8, 5))
        mode_counts.plot(kind='bar')
        plt.title('data group by mode')
        plt.ylabel('trade amount')
        plt.xlabel('trade mode')
        plt.show()
