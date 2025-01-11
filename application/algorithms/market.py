import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression


def predict_external_price(hours, prices, next_hours):
    if len(hours) != len(prices) or len(hours) == 0:
        return None
    if next_hours == 0:
        return []

    data = pd.DataFrame({'hour': hours, 'price': prices})
    model = ExponentialSmoothing(data['price'], trend='add', seasonal='add', seasonal_periods=24 * 7)
    fit = model.fit()
    forecast = fit.forecast(steps=next_hours)
    return forecast.tolist()


def predict_supply_demand(pre_ratio, pre_prices, curr_ratio, curr_prices, curr_round):
    if curr_round == len(curr_ratio):
        return curr_ratio, curr_prices

    ratio_model = LinearRegression()
    ratio_model.fit(pre_ratio[:-1].reshape(-1, 1), pre_ratio[1:])
    price_model = LinearRegression()
    price_model.fit(pre_ratio[:-1].reshape(-1, 1), pre_prices[:-1])

    for _ in range(len(curr_ratio) - curr_round):
        next_ratio = ratio_model.predict([[curr_ratio[curr_round - 1]]])[0]
        curr_ratio[curr_round] = next_ratio

        next_price = price_model.predict([[next_ratio]])[0]
        curr_prices[curr_round] = next_price
