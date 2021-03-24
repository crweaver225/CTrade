import sqlite3, config
from flask import Flask
from flask import request
import json
from flask import render_template, redirect
from datetime import date
#import threading

app = Flask(__name__)

@app.route("/")
def index():

    stock_filter = request.args.get('filter')
    
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    if stock_filter == 'new_closing_highs':
        cursor.execute("""
            select * from (
                select symbol, name, stock_id, max(close), date
                from stock_price join stock on stock.id = stock_price.stock_id
                group by stock_id
                order by symbol
            ) where date = ?
        """, (date.today().isoformat(),))
        print("running query for new high")
    else:
         cursor.execute("""
            SELECT id, symbol, name FROM stock order by symbol
        """)

    rows = cursor.fetchall()
    return render_template(
        'index.html',
        stocks = rows
    )

@app.route("/stock/<path:symbol>")
def stock_detail(symbol):
    
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM strategy
    """)
    strategies = cursor.fetchall()

    cursor.execute("""
        SELECT id, symbol, name FROM stock where symbol = ?
    """, (symbol,))

    row = cursor.fetchone()

    cursor.execute("""
        SELECT * from stock_price where stock_id = ? ORDER BY date DESC
    """, (row['id'],))

    prices = cursor.fetchall()

    return render_template(
        'stock_detail.html',
        bars = prices,
        stock = row,
        strategies = strategies
    )

@app.route("/apply_strategy", methods=['POST'])
def apply_strategy():
    print("Applying strategy...")

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    strategy_id = request.form.get('strategy_id')
    stock_id = request.form.get('stock_id')

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
    """, (stock_id, strategy_id))

    connection.commit()
    print("Redirecting..")
    return redirect(f"/strategy/{strategy_id}", code=303)

@app.route("/strategy/<path:strategy_id>")
def strategy(strategy_id):
    print("redirected!")
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name
        FROM strategy
        WHERE id = ?
    """, (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, name
        FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
        WHERE strategy_id = ?
    """, (strategy_id,))

    stocks = cursor.fetchall()

    return render_template(
        'strategy.html',
        stocks = stocks,
        strategy = strategy
    ) 




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=False)