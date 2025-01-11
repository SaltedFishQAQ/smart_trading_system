

def predict_prices(predict_ratio, predict_price, self_ratio, factor=0.1):
    delta_self = self_ratio / predict_ratio if predict_ratio > 0 else 1
    sell_price = predict_price * (1 + factor * (1 - delta_self))
    buy_price = predict_price * (1 - factor * (1 - delta_self))

    return sell_price, buy_price
