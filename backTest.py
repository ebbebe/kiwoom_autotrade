def backtest(historical_data, trading_strategy):
    # 포트폴리오 값, trade 리스트 초기화
    portfolio_value = 100000
    trades = []

    # historical_data 반복
    for data in historical_data:
        # 트레이딩 전략 현재 데이터 포인트에 적용
        trade = trading_strategy(data)


        # 만약 전략이 매수신호를 보내면, 잔금 체크
        if trade == "BUY" and portfolio_value > data["price"]:
            # 포트폴리오 값에서 구매한 가격 제외
            portfolio_value -= data["price"]
            # 트레이드 기록 남김
            trades.append({"type": "BUY", "price": data["price"], "timestamp": data["timestamp"], "quantity" : 1})
        # 만약 전략이 매도 신호를 보내면, 잔여주식 체크
        elif trade == "SELL" and trades:
            # 매도된 주식값 계산
            asset_value = data["price"] * trades[-1]["quantity"]
            # 계산된 결과값 포트폴리오에 합산
            portfolio_value += asset_value
            # 트레이드 기록 남김
            trades.append({"type": "SELL", "price": data["price"], "timestamp": data["timestamp"], "quantity" : 1})
    return portfolio_value, trades

def trading_strategy(data):
    # 트레이딩 알고리즘
    if data["price"] < 89500:
        return "BUY"
    elif data["price"] > 89500:
        return "SELL"
    else:
        return "HOLD"

# 시간 데이터 샘플
# 20221222142458 = 2022년 01월 03일 14시 52분 32초
historical_data = [
    {"timestamp": "20221222142500", "price": 89300},
    {"timestamp": "20221222142504", "price": 89600},
    {"timestamp": "20221222142458", "price": 89500},
    {"timestamp": "20221222142458", "price": 89600}, 
    {"timestamp": "20221222142456", "price": 89500},
    {"timestamp": "20221222142451", "price": 89600},
    {"timestamp": "20221222142459", "price": 89300},
]

# 백테스트 시작
final_portfolio_value, trades = backtest(historical_data, trading_strategy)


print(f"Final portfolio value: {final_portfolio_value}")
print("Trades:")
for trade in trades:
    print(trade)
    
    
    
    
    
    
    

# Set up the Kiwoom API
api = Kiwoom.CpTdUtil()
api.CommConnect()

# Place a trade using the Kiwoom API
api.SendOrder(
    "RQ_1",  # request identifier
    1,  # order type (1 for buy, 2 for sell)
    "AAPL",  # stock code
    10,  # order quantity
    100,  # order price
    "00",  # account number
    0,  # order number (0 for new order)
    "03",  # order type (03 for market order)
    ""  # original order number (empty for new order)
)

# Retrieve the trade data using the Kiwoom API
trade_data = api.GetChejanData(9203)

# Save the trade data to a file or database
with open("trades.csv", "a") as f:
    f.write(",".join(trade_data.values()) + "\n")
