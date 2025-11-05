import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import pytz
from dash import Dash, dcc, html, Input, Output, State
from dash.dependencies import ALL
import dash_bootstrap_components as dbc

class OptionsDashboard:
    def __init__(self, symbol):
        self.symbol = symbol
        self.options_data = None
        self.price_data = None
        self.current_price = None
        self.levels = []

    def fetch_options_data(self):
        """Fetch options data using yfinance"""
        try:
            ticker = yf.Ticker(self.symbol)
            self.current_price = ticker.history(period='1d')['Close'].iloc[-1]
            
            expirations = ticker.options
            if len(expirations) == 0:
                print(f"No options data available for {self.symbol}")
                return None
            
            exp_date = expirations[0]
            print(f"Using expiration: {exp_date} for {self.symbol}")
            
            opt_chain = ticker.option_chain(exp_date)
            
            calls = opt_chain.calls[['strike', 'openInterest']].rename(
                columns={'openInterest': 'Call_OI'})
            puts = opt_chain.puts[['strike', 'openInterest']].rename(
                columns={'openInterest': 'Put_OI'})
            
            df = pd.merge(calls, puts, on='strike', how='outer').fillna(0)
            df = df.sort_values('strike').reset_index(drop=True)
            
            price_range = self.current_price * 0.10
            df = df[(df['strike'] >= self.current_price - price_range) & 
                    (df['strike'] <= self.current_price + price_range)]
            
            return df
        except Exception as e:
            print(f"Error fetching options data for {self.symbol}: {e}")
            if self.symbol in ['/ES', '/NQ']:
                print(f"Note: {self.symbol} is a futures symbol, which yfinance may not support. Try a stock/ETF symbol.")
            return None

    def fetch_price_data(self, days=30, interval='30m'):
        """Fetch historical price data, filtered to market hours"""
        try:
            ticker = yf.Ticker(self.symbol)
            est = pytz.timezone('US/Eastern')
            # Set end_date to tomorrow to ensure we get all of today's data
            current_time = datetime.now(est)
            end_date = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=days+1)  # Add extra day to compensate

            df = ticker.history(start=start_date, end=end_date, interval=interval)
            if df.empty:
                return None
            
            df.index = df.index.tz_convert(est)
            # Filter strictly to 9:30 AM - 4:00 PM EST market hours
            df = df.between_time('09:30', '16:00')
            df = df[df.index.dayofweek < 5]  # Weekdays only
            
            return df
        except Exception as e:
            print(f"Error fetching price data for {self.symbol}: {e}")
            return None

    def calculate_levels(self, threshold=2.0, top_n=5):
        """Calculate option levels"""
        if self.options_data is None:
            return
        
        df = self.options_data.copy()
        top_calls = df.nlargest(top_n, 'Call_OI')
        top_puts = df.nlargest(top_n, 'Put_OI')
        relevant_strikes = pd.concat([top_calls, top_puts]).drop_duplicates(subset=['strike'])
        
        self.levels = []
        
        for idx, row in relevant_strikes.iterrows():
            strike = row['strike']
            call_oi = row['Call_OI']
            put_oi = row['Put_OI']
            
            if call_oi == 0 and put_oi == 0:
                continue
            
            call_put_ratio = call_oi / put_oi if put_oi > 0 else float('inf')
            put_call_ratio = put_oi / call_oi if call_oi > 0 else float('inf')
            
            is_top_call = strike in top_calls['strike'].values
            is_top_put = strike in top_puts['strike'].values
            
            level_type = None
            color = None
            emoji = None
            
            if is_top_call and is_top_put:
                level_type = 'Pin Zone'
                color = 'orange'
                emoji = '📌'
            elif call_put_ratio >= threshold:
                level_type = 'Call Wall'
                color = 'red'
                emoji = '🔴'
            elif put_call_ratio >= threshold:
                level_type = 'Put Support'
                color = 'green'
                emoji = '🟢'
            elif 1.3 < call_put_ratio < threshold or 1/threshold < put_call_ratio < 1/0.7:
                level_type = 'Flip Zone'
                color = 'purple'
                emoji = '🟣'
            elif 0.7 <= call_put_ratio <= 1.3:
                level_type = 'Chop Zone'
                color = 'yellow'
                emoji = '🟡'
            
            if level_type:
                self.levels.append({
                    'strike': strike,
                    'type': level_type,
                    'color': color,
                    'emoji': emoji,
                    'call_oi': int(call_oi),
                    'put_oi': int(put_oi),
                    'ratio': call_put_ratio
                })
        
        self.levels = sorted(self.levels, key=lambda x: x['strike'])

    def create_figure(self):
        """Create Plotly figure"""
        if self.price_data is None or len(self.levels) == 0:
            return go.Figure()
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=self.price_data.index,
            open=self.price_data['Open'],
            high=self.price_data['High'],
            low=self.price_data['Low'],
            close=self.price_data['Close'],
            name=self.symbol,
            increasing_line_color='green',
            decreasing_line_color='red'
        ))
        
        for level in self.levels:
            fig.add_hline(
                y=level['strike'],
                line_dash="dot",
                line_color=level['color'],
                line_width=2,
                annotation_text=f"{level['emoji']} ${level['strike']:.1f} (C:{level['call_oi']:,} P:{level['put_oi']:,})",
                annotation_position="right",
                annotation=dict(
                    font=dict(size=10, color='white'),  # White text for dark background
                    bgcolor="rgba(50,50,50,0.8)",  # Darker annotation background
                    bordercolor=level['color'],
                    borderwidth=1
                )
            )
        
        fig.update_layout(
            title=f'{self.symbol} Options Levels Dashboard',
            yaxis_title='Price ($)',
            xaxis_title='Date',
            height=600,  # Fixed height for graph
            width=2400,  # Maintain your manually adjusted width
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_dark',  # Dark background
            showlegend=True,
            margin=dict(r=250, b=50),  # Maintain right margin for OI annotations
            xaxis=dict(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),  # Weekend breaks
                    dict(bounds=[17, 9.5], pattern="hour"),  # Exclude 4:01 PM - 9:29 AM EST
                    # dict(values=[f"{datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d')} 00:00-09:30", f"{datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d')} 16:00-23:59"])  # Today’s non-market hours - commented out to show current day
                ]
            )
        )
        
        return fig

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # Dark theme for Dash layout

# Custom CSS to fix dropdown visibility - injected into HTML head
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .Select--multi .Select-value {
                color: white !important;
            }
            .Select-control, .Select-menu-outer {
                background-color: #2c3e50 !important;
                color: white !important;
                border: 1px solid #34495e !important;
            }
            .Select-option {
                background-color: #2c3e50 !important;
                color: white !important;
            }
            .Select-placeholder {
                color: #bdc3c7 !important; /* Lighter gray for placeholder */
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    dbc.Row([
        dbc.Col(
            html.H1("Options Levels Dashboard"),
            width=12,
            className="text-center mb-4"
        )
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='ticker-dropdown',
                options=[{'label': ticker, 'value': ticker} for ticker in ['QQQ', 'SPY', '^SPX', '^NDX', 'IWM']],
                value='QQQ',
                clearable=False,
                className="mb-3"
            ),
            width=3
        ),
        dbc.Col(
            dbc.Button("Refresh Data", id='refresh-button', color="primary", className="mb-3"),
            width=3
        ),
    ]),
    dcc.Graph(id='dashboard-graph', style={'height': '600px'}),
    dbc.Row([
        dbc.Col(
            html.Div(id='summary-output', style={'marginTop': '20px'}),
            width=12
        )
    ]),
    dcc.Interval(
        id='auto-refresh',
        interval=15*60*1000,  # 15 minutes
        n_intervals=0
    )
])

@app.callback(
    [Output('dashboard-graph', 'figure'),
     Output('summary-output', 'children')],
    [Input('ticker-dropdown', 'value'),
     Input('refresh-button', 'n_clicks'),
     Input('auto-refresh', 'n_intervals')]
)
def update_dashboard(ticker, n_clicks, n_intervals):
    dashboard = OptionsDashboard(ticker)
    
    dashboard.options_data = dashboard.fetch_options_data()
    if dashboard.options_data is None:
        return go.Figure(), html.Div([f"No options data available for {ticker}"])
    
    dashboard.price_data = dashboard.fetch_price_data(days=30)
    if dashboard.price_data is None:
        return go.Figure(), html.Div([f"No price data available for {ticker}"])
    
    dashboard.calculate_levels()
    
    fig = dashboard.create_figure()
    
    summary = [
        html.H4(f"Options Levels Summary for {ticker}"),
        dbc.Table(
            [html.Tr([html.Th("Type"), html.Th("Strike"), html.Th("Calls"), html.Th("Puts")])] +
            [html.Tr([
                html.Td(f"{level['emoji']} {level['type']}"),
                html.Td(f"${level['strike']:.2f}"),
                html.Td(f"{level['call_oi']:,}"),
                html.Td(f"{level['put_oi']:,}")
            ]) for level in dashboard.levels],
            bordered=True,
            striped=True,
            hover=True,
            style={'width': '100%', 'tableLayout': 'fixed'}  # Ensure table fits
        )
    ]
    
    return fig, summary

if __name__ == '__main__':
    app.run(debug=True)