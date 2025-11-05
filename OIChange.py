import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import webbrowser
import os

class QQQOptionsDashboard:
    def __init__(self):
        self.options_data = None
        self.price_data = None
        self.current_price = None
        self.levels = []
        
    def fetch_options_data(self, symbol='IWM'):
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
    
    def fetch_price_data(self, symbol='IWM', days=7, interval='30m'):
        """Fetch historical price data with specified interval"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            return df
        except Exception as e:
            print(f"Error fetching price data: {e}")
            return None
    
    def calculate_levels(self, threshold=2.0, top_n=5):
        """Calculate option levels - top N for calls and puts"""
        if self.options_data is None:
            return
        
        df = self.options_data.copy()
        
        # Get top N calls by OI
        top_calls = df.nlargest(top_n, 'Call_OI')
        
        # Get top N puts by OI
        top_puts = df.nlargest(top_n, 'Put_OI')
        
        # Combine all strikes we care about
        relevant_strikes = pd.concat([top_calls, top_puts]).drop_duplicates(subset=['strike'])
        
        self.levels = []
        
        for idx, row in relevant_strikes.iterrows():
            strike = row['strike']
            call_oi = row['Call_OI']
            put_oi = row['Put_OI']
            
            if call_oi == 0 and put_oi == 0:
                continue
            
            # Calculate ratio
            if put_oi > 0:
                call_put_ratio = call_oi / put_oi
            else:
                call_put_ratio = float('inf')
            
            if call_oi > 0:
                put_call_ratio = put_oi / call_oi
            else:
                put_call_ratio = float('inf')
            
            # Check if this is a Pin Zone (high OI for both)
            is_top_call = strike in top_calls['strike'].values
            is_top_put = strike in top_puts['strike'].values
            
            level_type = None
            color = None
            emoji = None
            
            # Pin Zone: High OI for BOTH calls and puts
            if is_top_call and is_top_put:
                level_type = 'Pin Zone'
                color = 'orange'
                emoji = '📌'
            
            # Call Wall: Call OI significantly > Put OI
            elif call_put_ratio >= threshold:
                level_type = 'Call Wall'
                color = 'red'
                emoji = '🔴'
            
            # Put Support: Put OI significantly > Call OI
            elif put_call_ratio >= threshold:
                level_type = 'Put Support'
                color = 'green'
                emoji = '🟢'
            
            # Flip Zone: Transitional ratios
            elif 1.3 < call_put_ratio < threshold or 1/threshold < put_call_ratio < 1/0.7:
                level_type = 'Flip Zone'
                color = 'purple'
                emoji = '🟣'
            
            # Chop Zone: Mixed OI
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
        
        # Sort by strike
        self.levels = sorted(self.levels, key=lambda x: x['strike'])
    
    def create_dashboard(self):
        """Create the candlestick chart with levels"""
        if self.price_data is None or len(self.levels) == 0:
            print("Missing data for dashboard")
            return None
        
        # Create candlestick chart
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=self.price_data.index,
            open=self.price_data['Open'],
            high=self.price_data['High'],
            low=self.price_data['Low'],
            close=self.price_data['Close'],
            name='IWM',
            increasing_line_color='green',
            decreasing_line_color='red'
        ))
        
        # Add horizontal levels with better visibility
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
        
        # Update layout
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
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
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
    
    def run(self, symbol='IWM', threshold=2.0, top_n=5, days=7, save_html=True):
        """Run the complete dashboard"""
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
            # Save to HTML file
            filename = f"qqq_options_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            fig.write_html(filename)
            print(f"\n✅ Chart saved to: {filename}")
            
            # Try to open in browser
            try:
                filepath = os.path.abspath(filename)
                webbrowser.open('file://' + filepath)
                print(f"✅ Opening chart in browser...")
            except:
                print(f"⚠️  Please open {filename} manually in your browser")
        
        return fig

# Run the dashboard
if __name__ == "__main__":
    dashboard = QQQOptionsDashboard()
    # Shows top 5 calls and top 5 puts, saves to HTML file
    fig = dashboard.run(symbol='IWM', threshold=2.0, top_n=5, days=6, save_html=True)
    
    print("\n" + "="*60)
    print("Dashboard complete!")
    print("="*60)