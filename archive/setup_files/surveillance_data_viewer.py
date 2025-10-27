#!/usr/bin/env python3
"""
📊 Surveillance Data Viewer
View all user activities, detections, and system logs
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from pathlib import Path

class SurveillanceDataViewer:
    """GUI for viewing surveillance system data"""
    
    def __init__(self, db_path="surveillance_data.db"):
        self.db_path = db_path
        
        # Check if database exists
        if not Path(db_path).exists():
            messagebox.showerror("Error", f"Database not found: {db_path}")
            return
        
        self.root = tk.Tk()
        self.root.title("📊 Surveillance Data Viewer")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2c3e50')
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup user interface"""
        # Title
        title_label = tk.Label(
            self.root,
            text="📊 Smart Surveillance System - Data Viewer",
            font=('Arial', 16, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Users tab
        self.setup_users_tab()
        
        # Sessions tab
        self.setup_sessions_tab()
        
        # Detections tab
        self.setup_detections_tab()
        
        # System logs tab
        self.setup_logs_tab()
        
        # Statistics tab
        self.setup_statistics_tab()
        
        # Refresh button
        refresh_frame = tk.Frame(self.root, bg='#2c3e50')
        refresh_frame.pack(fill='x', padx=10, pady=5)
        
        refresh_btn = tk.Button(
            refresh_frame,
            text="🔄 Refresh Data",
            command=self.load_data,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        )
        refresh_btn.pack(side='right')
    
    def setup_users_tab(self):
        """Setup users tab"""
        users_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(users_frame, text="👤 Users")
        
        # Users treeview
        columns = ('ID', 'Email', 'Created', 'Last Login', 'Total Sessions', 'Total Detections')
        self.users_tree = ttk.Treeview(users_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=150)
        
        # Scrollbars
        users_scrollbar_v = ttk.Scrollbar(users_frame, orient='vertical', command=self.users_tree.yview)
        users_scrollbar_h = ttk.Scrollbar(users_frame, orient='horizontal', command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=users_scrollbar_v.set, xscrollcommand=users_scrollbar_h.set)
        
        # Pack
        self.users_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        users_scrollbar_v.pack(side='right', fill='y')
        users_scrollbar_h.pack(side='bottom', fill='x')
    
    def setup_sessions_tab(self):
        """Setup sessions tab"""
        sessions_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(sessions_frame, text="🔐 Sessions")
        
        # Sessions treeview
        columns = ('ID', 'User Email', 'Login Time', 'Logout Time', 'Duration (min)', 'Detections')
        self.sessions_tree = ttk.Treeview(sessions_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.sessions_tree.heading(col, text=col)
            self.sessions_tree.column(col, width=150)
        
        # Scrollbars
        sessions_scrollbar_v = ttk.Scrollbar(sessions_frame, orient='vertical', command=self.sessions_tree.yview)
        sessions_scrollbar_h = ttk.Scrollbar(sessions_frame, orient='horizontal', command=self.sessions_tree.xview)
        self.sessions_tree.configure(yscrollcommand=sessions_scrollbar_v.set, xscrollcommand=sessions_scrollbar_h.set)
        
        # Pack
        self.sessions_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        sessions_scrollbar_v.pack(side='right', fill='y')
        sessions_scrollbar_h.pack(side='bottom', fill='x')
    
    def setup_detections_tab(self):
        """Setup detections tab"""
        detections_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(detections_frame, text="🚨 Threat Detections")
        
        # Detections treeview
        columns = ('ID', 'User', 'Type', 'Confidence', 'Time', 'Description', 'Email Sent')
        self.detections_tree = ttk.Treeview(detections_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.detections_tree.heading(col, text=col)
            self.detections_tree.column(col, width=130)
        
        # Scrollbars
        detections_scrollbar_v = ttk.Scrollbar(detections_frame, orient='vertical', command=self.detections_tree.yview)
        detections_scrollbar_h = ttk.Scrollbar(detections_frame, orient='horizontal', command=self.detections_tree.xview)
        self.detections_tree.configure(yscrollcommand=detections_scrollbar_v.set, xscrollcommand=detections_scrollbar_h.set)
        
        # Pack
        self.detections_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        detections_scrollbar_v.pack(side='right', fill='y')
        detections_scrollbar_h.pack(side='bottom', fill='x')
    
    def setup_logs_tab(self):
        """Setup system logs tab"""
        logs_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(logs_frame, text="📝 System Logs")
        
        # Logs treeview
        columns = ('ID', 'User', 'Action', 'Details', 'Timestamp')
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.logs_tree.heading(col, text=col)
            if col == 'Details':
                self.logs_tree.column(col, width=300)
            else:
                self.logs_tree.column(col, width=150)
        
        # Scrollbars
        logs_scrollbar_v = ttk.Scrollbar(logs_frame, orient='vertical', command=self.logs_tree.yview)
        logs_scrollbar_h = ttk.Scrollbar(logs_frame, orient='horizontal', command=self.logs_tree.xview)
        self.logs_tree.configure(yscrollcommand=logs_scrollbar_v.set, xscrollcommand=logs_scrollbar_h.set)
        
        # Pack
        self.logs_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        logs_scrollbar_v.pack(side='right', fill='y')
        logs_scrollbar_h.pack(side='bottom', fill='x')
    
    def setup_statistics_tab(self):
        """Setup statistics tab"""
        stats_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(stats_frame, text="📈 Statistics")
        
        # Statistics text widget
        self.stats_text = tk.Text(
            stats_frame,
            bg='#2c3e50',
            fg='white',
            font=('Consolas', 11),
            wrap=tk.WORD,
            state='disabled'
        )
        
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient='vertical', command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        stats_scrollbar.pack(side='right', fill='y')
    
    def load_data(self):
        """Load all data from database"""
        self.load_users_data()
        self.load_sessions_data()
        self.load_detections_data()
        self.load_logs_data()
        self.load_statistics_data()
    
    def load_users_data(self):
        """Load users data"""
        # Clear existing data
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.created_at, u.last_login,
                   COUNT(DISTINCT s.id) as session_count,
                   COUNT(DISTINCT d.id) as detection_count
            FROM users u
            LEFT JOIN sessions s ON u.id = s.user_id
            LEFT JOIN detections d ON u.id = d.user_id
            GROUP BY u.id, u.email, u.created_at, u.last_login
            ORDER BY u.created_at DESC
        """)
        
        for row in cursor.fetchall():
            user_id, email, created_at, last_login, session_count, detection_count = row
            
            # Format dates
            created_formatted = self.format_datetime(created_at) if created_at else "N/A"
            last_login_formatted = self.format_datetime(last_login) if last_login else "Never"
            
            self.users_tree.insert('', 'end', values=(
                user_id, email, created_formatted, last_login_formatted, session_count, detection_count
            ))
        
        conn.close()
    
    def load_sessions_data(self):
        """Load sessions data"""
        # Clear existing data
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, u.email, s.login_time, s.logout_time, s.duration_minutes,
                   COUNT(d.id) as detection_count
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN detections d ON s.id = d.session_id
            GROUP BY s.id, u.email, s.login_time, s.logout_time, s.duration_minutes
            ORDER BY s.login_time DESC
        """)
        
        for row in cursor.fetchall():
            session_id, email, login_time, logout_time, duration, detection_count = row
            
            # Format data
            login_formatted = self.format_datetime(login_time) if login_time else "N/A"
            logout_formatted = self.format_datetime(logout_time) if logout_time else "Active"
            duration_formatted = f"{duration:.1f}" if duration else "Active"
            
            self.sessions_tree.insert('', 'end', values=(
                session_id, email, login_formatted, logout_formatted, duration_formatted, detection_count
            ))
        
        conn.close()
    
    def load_detections_data(self):
        """Load detections data"""
        # Clear existing data
        for item in self.detections_tree.get_children():
            self.detections_tree.delete(item)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.id, u.email, d.detection_type, d.confidence, d.timestamp, 
                   d.description, d.email_sent
            FROM detections d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.timestamp DESC
        """)
        
        for row in cursor.fetchall():
            det_id, email, det_type, confidence, timestamp, description, email_sent = row
            
            # Format data
            timestamp_formatted = self.format_datetime(timestamp) if timestamp else "N/A"
            confidence_formatted = f"{confidence:.2f}" if confidence else "N/A"
            email_status = "✅ Yes" if email_sent else "❌ No"
            
            self.detections_tree.insert('', 'end', values=(
                det_id, email, det_type, confidence_formatted, timestamp_formatted, 
                description, email_status
            ))
        
        conn.close()
    
    def load_logs_data(self):
        """Load system logs data"""
        # Clear existing data
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.id, u.email, l.action, l.details, l.timestamp
            FROM system_logs l
            JOIN users u ON l.user_id = u.id
            ORDER BY l.timestamp DESC
            LIMIT 1000
        """)
        
        for row in cursor.fetchall():
            log_id, email, action, details, timestamp = row
            
            # Format timestamp
            timestamp_formatted = self.format_datetime(timestamp) if timestamp else "N/A"
            
            self.logs_tree.insert('', 'end', values=(
                log_id, email, action, details or "", timestamp_formatted
            ))
        
        conn.close()
    
    def load_statistics_data(self):
        """Load and display statistics"""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall statistics
        self.stats_text.insert(tk.END, "📊 SURVEILLANCE SYSTEM STATISTICS\n")
        self.stats_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"👤 Total Users: {total_users}\n")
        
        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"🔐 Total Sessions: {total_sessions}\n")
        
        # Active sessions
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE logout_time IS NULL")
        active_sessions = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"🟢 Active Sessions: {active_sessions}\n")
        
        # Total detections
        cursor.execute("SELECT COUNT(*) FROM detections")
        total_detections = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"🚨 Total Detections: {total_detections}\n")
        
        # Emails sent
        cursor.execute("SELECT COUNT(*) FROM detections WHERE email_sent = 1")
        emails_sent = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"📧 Emails Sent: {emails_sent}\n\n")
        
        # Detection breakdown
        self.stats_text.insert(tk.END, "🚨 THREAT DETECTION BREAKDOWN\n")
        self.stats_text.insert(tk.END, "=" * 30 + "\n")
        
        cursor.execute("""
            SELECT detection_type, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM detections 
            GROUP BY detection_type 
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            det_type, count, avg_conf = row
            avg_conf_str = f"{avg_conf:.2f}" if avg_conf else "N/A"
            self.stats_text.insert(tk.END, f"{det_type}: {count} (avg confidence: {avg_conf_str})\n")
        
        # Recent activity
        self.stats_text.insert(tk.END, "\n📅 RECENT ACTIVITY (Last 24 hours)\n")
        self.stats_text.insert(tk.END, "=" * 35 + "\n")
        
        # Recent logins
        cursor.execute("""
            SELECT COUNT(*) FROM sessions 
            WHERE login_time >= datetime('now', '-1 day')
        """)
        recent_logins = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"Recent Logins: {recent_logins}\n")
        
        # Recent detections
        cursor.execute("""
            SELECT COUNT(*) FROM detections 
            WHERE timestamp >= datetime('now', '-1 day')
        """)
        recent_detections = cursor.fetchone()[0]
        self.stats_text.insert(tk.END, f"Recent Detections: {recent_detections}\n")
        
        # Top users by activity
        self.stats_text.insert(tk.END, "\n👑 TOP USERS BY ACTIVITY\n")
        self.stats_text.insert(tk.END, "=" * 25 + "\n")
        
        cursor.execute("""
            SELECT u.email, COUNT(DISTINCT s.id) as sessions, COUNT(DISTINCT d.id) as detections
            FROM users u
            LEFT JOIN sessions s ON u.id = s.user_id
            LEFT JOIN detections d ON u.id = d.user_id
            GROUP BY u.id, u.email
            ORDER BY sessions DESC, detections DESC
            LIMIT 5
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            email, sessions, detections = row
            self.stats_text.insert(tk.END, f"{i}. {email}: {sessions} sessions, {detections} detections\n")
        
        # System health
        self.stats_text.insert(tk.END, "\n💚 SYSTEM HEALTH\n")
        self.stats_text.insert(tk.END, "=" * 15 + "\n")
        
        # Database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0] / (1024 * 1024)  # Convert to MB
        self.stats_text.insert(tk.END, f"Database Size: {db_size:.2f} MB\n")
        
        # Last activity
        cursor.execute("SELECT MAX(timestamp) FROM system_logs")
        last_activity = cursor.fetchone()[0]
        if last_activity:
            last_activity_formatted = self.format_datetime(last_activity)
            self.stats_text.insert(tk.END, f"Last Activity: {last_activity_formatted}\n")
        
        conn.close()
        self.stats_text.config(state='disabled')
    
    def format_datetime(self, dt_string):
        """Format datetime string for display"""
        try:
            dt = datetime.datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return dt_string if dt_string else "N/A"
    
    def run(self):
        """Run the data viewer"""
        self.root.mainloop()

def main():
    """Main function"""
    print("📊 Starting Surveillance Data Viewer...")
    
    try:
        viewer = SurveillanceDataViewer()
        viewer.run()
    except Exception as e:
        print(f"❌ Error starting data viewer: {e}")
        messagebox.showerror("Error", f"Failed to start data viewer: {e}")

if __name__ == "__main__":
    main()