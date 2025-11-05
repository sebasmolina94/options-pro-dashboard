import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import time
import webbrowser
import os

class QQQOptionsDashboard:
    def __init__(self):
        self.options_data = None
        self.price_data = None
        self.current_price = None
        self.levels = []

    def fetch_options_data(self, symbol='QQQ'):
        """Fetch options data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            self.current_price = ticker.history(period='1d')['Close'].iloc[-1]
            
            # Get options expiration dates
            expirations = ticker.options
            if len(expirations) == 0:
                print("No options data available")
                return None
            
            # Use the nearest expiration
            exp_date = expirations[0]
            print(f"Using expiration: {exp_date}")
            
            # Get options chain
            opt_chain = ticker.option_chain(exp_date)
            
            # Combine calls and puts by strike
            calls = opt_chain.calls[['strike', 'openInterest']].rename(
                columns={'openInterest': 'Call_OI'})
            puts = opt_chain.puts[['strike', 'openInterest']].rename(
                columns={'openInterest': 'Put_OI'})
            
            # Merge on strike
            df = pd.merge(calls, puts, on='strike', how='outer').fillna(0)
            df = df.sort_values('strike').reset_index(drop=True)
            
            # Filter to strikes near current price (±10%)
            price_range = self.current_price * 0.10
            df = df[(df['strike'] >= self.current_price - price_range) & 
                   (df['strike'] <= self.current_price + price_range)]
            
            print(f"Current price: ${self.current_price:.2f}")
            print(f"Found {len(df)} strikes in range")
            
            return df
            
        except Exception as e:
            print(f"Error fetching options data: {e}")
            return None

    def fetch_price_data(self, symbol='QQQ', days=7, interval='30m'):
        """Fetch historical price data with specified interval, filtered to market hours"""
        try:
            ticker = yf.Ticker(symbol)
            est = pytz.timezone('US/Eastern')
            end_date = datetime.now(est).replace(hour=16, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=days)
            
            # Fetch raw data
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            if df.empty:
                return None
            
            # Convert index to EST and filter to market hours (9:30 AM - 4:00 PM)
            df.index = df.index.tz_convert(est)
            market_open = pd.Timestamp('09:30', tz=est).time()
            market_close = pd.Timestamp('16:00', tz=est).time()
            
            df = df.between_time('09:30', '16:00')
            
            # Remove weekends (Saturday/Sunday)
            df = df[df.index.dayofweek < 5]
            
            return df
        except Exception as e:
            print(f"Error fetching price data: {e}")
            return None

    def calculate_levels(self, threshold=2.0, top_n=5):
        """Calculate option levels - top N for calls and puts"""
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
            
            if put_oi > 0:
                call_put_ratio = call_oi / put_oi
            else:
                call_put_ratio = float('inf')
            
            if call_oi > 0:
                put_call_ratio = put_oi / call_oi
            else:
                put_call_ratio = float('inf')
            
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

    def create_dashboard(self):
        """Create the candlestick chart with levels, showing only market hours"""
        if self.price_data is None or len(self.levels) == 0:
            print("Missing data for dashboard")
            return None
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=self.price_data.index,
            open=self.price_data['Open'],
            high=self.price_data['High'],
            low=self.price_data['Low'],
            close=self.price_data['Close'],
            name='QQQ',
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
                    font=dict(size=10, color=level['color']),
                    bgcolor="rgba(255,255,255,0.8)"
                )
            )
        
        # Set layout to focus on market hours
        est = pytz.timezone('US/Eastern')
        fig.update_layout(
            title={
                'text': 'QQQ Options Levels Dashboard',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            yaxis_title='Price ($)',
            xaxis_title='Date',
            height=900,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True,
            xaxis=dict(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),  # Hide weekends
                    dict(values=["2025-10-14 00:00-09:30", "2025-10-14 16:00-23:59"])  # Hide non-market hours
                    # Add rangebreaks for other days as needed based on data
                ]
            )
        )
        
        return fig

    def print_summary(self):
        """Print summary of levels"""
        print("\n" + "="*60)
        print("OPTIONS LEVELS SUMMARY")
        print("="*60)
        for level in self.levels:
            print(f"{level['emoji']} {level['type']:12s} | Strike: ${level['strike']:7.2f} | "
                  f"Calls: {level['call_oi']:6,} | Puts: {level['put_oi']:6,}")
        print("="*60 + "\n")

    def run(self, symbol='QQQ', threshold=2.0, top_n=5, days=7, save_html=True):
        """Run the complete dashboard once"""
        print(f"Fetching options data for {symbol}...")
        self.options_data = self.fetch_options_data(symbol)
        
        if self.options_data is None:
            print("Failed to fetch options data")
            return None
        
        print(f"\nFetching {days} days of 30-minute price data...")
        self.price_data = self.fetch_price_data(symbol, days, interval='30m')
        
        if self.price_data is None:
            print("Failed to fetch price data")
            return None
        
        print(f"\nCalculating top {top_n} levels for calls and puts...")
        self.calculate_levels(threshold=threshold, top_n=top_n)
        
        self.print_summary()
        print("Creating chart...")
        fig = self.create_dashboard()
        
        if fig and save_html:
            filename = f"qqq_options_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            fig.write_html(filename)
            print(f"\n✅ Chart saved to: {filename}")
            
            try:
                filepath = os.path.abspath(filename)
                webbrowser.open('file://' + filepath)
                print(f"✅ Opening chart in browser...")
            except:
                print(f"⚠️ Please open {filename} manually in your browser")
        
        return fig

    def run_scheduler(self, symbol='QQQ', threshold=2.0, top_n=5, days=7, interval_minutes=15):
        """Automatically run dashboard between 9:30am–4:00pm EST"""
        est = pytz.timezone('US/Eastern')
        print("📈 Starting QQQ Options Dashboard Scheduler...")
        print(f"Will update every {interval_minutes} minutes during market hours (9:30am–4:00pm EST).")

        while True:
            now = datetime.now(est)
            weekday = now.weekday()  # 0=Mon, 6=Sun
            current_time = now.time()

            market_open = datetime.strptime("09:30", "%H:%M").time()
            market_close = datetime.strptime("16:00", "%H:%M").time()

            if weekday >= 5:
                print("🛑 It's the weekend. Sleeping for 1 hour...")
                time.sleep(3600)
                continue

            if market_open <= current_time <= market_close:
                print(f"\n🚀 Running dashboard update at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}...")
                try:
                    self.run(symbol=symbol, threshold=threshold, top_n=top_n, days=days, save_html=True)
                except Exception as e:
                    print(f"⚠️ Error during dashboard run: {e}")
                print(f"✅ Sleeping for {interval_minutes} minutes...\n")
                time.sleep(interval_minutes * 60)
            else:
                print(f"⏸ Outside market hours ({now.strftime('%H:%M %Z')}). Sleeping 15 minutes...")
                time.sleep(900)


if __name__ == "__main__":
    dashboard = QQQOptionsDashboard()
    dashboard.run_scheduler(
        symbol='QQQ',
        threshold=2.0,
        top_n=5,
        days=30,
        interval_minutes=15  # Update every 15 minutes
    )