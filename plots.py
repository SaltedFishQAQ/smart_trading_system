import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

file_path = 'energy_flow_output.csv'

data = pd.read_csv(file_path)

def preprocess_datetime_column(data):
    """
    Splits the 'datetime' column into separate 'day' and 'hour' columns.
    Assumes the format is 'day:hour'.
    """
    data[['day', 'hour']] = data['datetime'].str.split(':', expand=True).astype(int)
    return data

data = preprocess_datetime_column(data)

sns.set_theme(style="whitegrid")

# Total Energy Supplied by Source
def total_energy_supplied_by_source(data):
    total_supply = data.groupby('supplier_id')['amount'].sum().reset_index()
    total_supply = total_supply.sort_values(by='amount', ascending=False)
    plt.figure(figsize=(12, 7))
    sns.barplot(x='amount', y='supplier_id', data=total_supply, palette='viridis', legend=False)
    plt.title('Total Energy Supplied by Source', fontsize=18)
    plt.xlabel('Total Energy Supplied (Units)', fontsize=14)
    plt.ylabel('Supplier', fontsize=14)
    plt.tight_layout()
    plt.show()

# Hourly Trends of Energy Supply
def hourly_energy_trends(data):
    hourly_supply = data.groupby(['hour', 'supplier_id'])['amount'].sum().reset_index()
    plt.figure(figsize=(14, 8))
    sns.lineplot(x='hour', y='amount', hue='supplier_id', data=hourly_supply, palette='tab10', marker='o')
    plt.title('Hourly Trends of Energy Supply', fontsize=18)
    plt.xlabel('Hour of Day', fontsize=14)
    plt.ylabel('Energy Supplied (Units)', fontsize=14)
    plt.legend(title='Supplier', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Energy Contribution Percentage by Source
def energy_contribution_percentage(data):
    total_supply = data.groupby('supplier_id')['amount'].sum().reset_index()
    total_supply['percentage'] = (total_supply['amount'] / total_supply['amount'].sum()) * 100

    plt.figure(figsize=(10, 10))
    colors = sns.color_palette('pastel')[0:len(total_supply)]
    plt.pie(total_supply['percentage'], labels=total_supply['supplier_id'], autopct='%1.1f%%',
            startangle=140, colors=colors, textprops={'fontsize': 12})
    plt.title('Energy Contribution Percentage by Source', fontsize=18)
    plt.tight_layout()
    plt.show()

# Grid Dependency Plot
def grid_dependency_plot(data):
    """
    Plots the grid dependency as a percentage of total supply.
    """
    total_supply = data.groupby('supplier_id')['amount'].sum().reset_index()
    total_grid_supply = total_supply[total_supply['supplier_id'] == 'MainGrid']['amount'].sum()
    total_energy = total_supply['amount'].sum()

    print("Total Supply by All Suppliers:\n", total_supply)
    print("Total Grid Supply:", total_grid_supply)
    print("Total Energy Supply:", total_energy)

    if total_grid_supply > 0 and total_energy > 0:
        grid_ratio = (total_grid_supply / total_energy) * 100

        plt.figure(figsize=(8, 6))
        labels = ['Grid Dependency', 'Other Sources']
        sizes = [grid_ratio, 100 - grid_ratio]
        colors = ['#ff9999', '#66b3ff']
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        plt.title('Grid Dependency', fontsize=18)
        plt.tight_layout()
        plt.show()
    else:
        print("Error: Invalid total_grid_supply or total_energy")
        print(f"Total Grid Supply: {total_grid_supply}, Total Energy: {total_energy}")

def self_sufficiency_ratio_plot(data):
    """
    Plots the self-sufficiency ratio (percentage of demand met by internal sources).
    """
    internal_supply = data[data['mode'].isin(['SELF_USE', 'TO_ESS'])]['amount'].sum()
    total_demand = data['amount'].sum()

    print("Internal Supply:", internal_supply)
    print("Total Demand:", total_demand)

    if internal_supply > 0 and total_demand > 0:
        ssr = (internal_supply / total_demand) * 100
        plt.figure(figsize=(8, 6))
        sns.barplot(x=['Self-Sufficiency Ratio'], y=[ssr], palette='crest', legend=False)
        plt.title('Self-Sufficiency Ratio (SSR)', fontsize=18)
        plt.ylabel('Percentage (%)', fontsize=14)
        plt.xlabel('', fontsize=14)
        plt.tight_layout()
        plt.show()
    else:
        print("Error: Invalid internal_supply or total_demand")
        print(f"Internal Supply: {internal_supply}, Total Demand: {total_demand}")

total_energy_supplied_by_source(data)
hourly_energy_trends(data)
energy_contribution_percentage(data)
grid_dependency_plot(data)
self_sufficiency_ratio_plot(data)
