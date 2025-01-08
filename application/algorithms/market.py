import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def forecast_price(hours, prices, next_hours):
    if len(hours) != len(prices) or len(hours) == 0:
        return None

    data = pd.DataFrame({'hour': hours, 'price': prices})
    model = ExponentialSmoothing(data['price'], trend='add', seasonal='add', seasonal_periods=24 * 7)
    fit = model.fit()
    forecast = fit.forecast(steps=next_hours)
    return forecast
