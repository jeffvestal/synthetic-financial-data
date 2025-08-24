#!/usr/bin/env python3
"""
Interactive Control Script for Synthetic Financial Data Generation

This script provides a user-friendly command-line interface for managing
all aspects of synthetic financial data generation, including configuration,
execution, and monitoring.
"""

import os
import sys
import signal
import argparse
from typing import Dict, Any, Optional

# Add lib and scripts to path with robust resolution for all environments
def setup_module_paths():
    """Setup module paths for both local and notebook environments."""
    # Try multiple path resolution strategies
    possible_script_dirs = [
        os.path.dirname(os.path.abspath(__file__)),  # Standard approach
        os.path.dirname(os.path.realpath(__file__)),  # Follow symlinks
        os.getcwd(),  # Current working directory (Colab fallback)
        os.path.dirname(os.getcwd())  # Parent of current directory
    ]
    
    for script_dir in possible_script_dirs:
        lib_path = os.path.join(script_dir, 'lib')
        scripts_path = os.path.join(script_dir, 'scripts')
        
        # Check if this looks like our project directory
        if (os.path.exists(lib_path) and 
            os.path.exists(os.path.join(lib_path, 'menu_system.py')) and
            os.path.exists(os.path.join(lib_path, 'config_manager.py'))):
            
            sys.path.insert(0, lib_path)
            if os.path.exists(scripts_path):
                sys.path.insert(0, scripts_path)
            return True
    
    return False

# Setup paths before any local imports
if not setup_module_paths():
    print("❌ Could not locate project modules. Ensure you're running from the project directory.")
    print("Current working directory:", os.getcwd())
    print("Script location:", __file__)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
except ImportError:
    print("❌ Required dependency 'rich' not found.")
    print("Please install it with: pip install rich")
    sys.exit(1)

# Local imports
from menu_system import MenuSystem
from config_manager import ConfigManager
from task_executor import TaskExecutor

class SyntheticDataController:
    """Main controller for the interactive data generation interface."""
    
    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.menu_system = MenuSystem(self.console)
        self.task_executor = TaskExecutor(self.console)
        
        # Setup signal handler for graceful exit
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Track if we're in the middle of operations
        self._operations_running = False
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        if self._operations_running:
            self.console.print("\n🛑 [yellow]Interrupt received. Cleaning up...[/yellow]")
            self.task_executor.stop_all_tasks()
        else:
            self.console.print("\n👋 [blue]Goodbye![/blue]")
        sys.exit(0)
    
    def run_interactive(self):
        """Run the interactive menu system."""
        self.menu_system.show_welcome()
        
        while True:
            try:
                choice = self.menu_system.show_main_menu()
                
                if choice == "1":
                    self._quick_start()
                elif choice == "2":
                    self._custom_generation()
                elif choice == "3":
                    self._trigger_events()
                elif choice == "4":
                    self._check_status()
                elif choice == "5":
                    self._manage_indices()
                elif choice == "6":
                    self._configure_settings()
                elif choice == "7":
                    self._dry_run_mode()
                elif choice == "8":
                    break
                    
            except KeyboardInterrupt:
                self._signal_handler(None, None)
            except Exception as e:
                self.console.print(f"❌ [red]Error: {e}[/red]")
        
        self.console.print("\n👋 [blue]Goodbye![/blue]")
    
    def run_non_interactive(self, args):
        """Run in non-interactive mode with command-line arguments."""
        self.console.print("🚀 [blue]Running in non-interactive mode...[/blue]")
        
        if args.quick_start:
            self._quick_start(interactive=False)
        elif args.custom:
            self._run_custom_from_args(args)
        elif args.trigger_event:
            self._trigger_events(interactive=False, event_type=args.trigger_event)
        elif args.status:
            self._check_status()
        elif args.check_indices:
            self._check_indices()
        elif args.update_timestamps:
            self._update_timestamps(args.timestamp_offset)
        elif args.update_files:
            self._update_data_files(args.timestamp_offset)
        else:
            self.console.print("❌ [red]No valid action specified for non-interactive mode[/red]")
    
    def _quick_start(self, interactive=True):
        """Execute quick start with default settings."""
        if interactive:
            self.console.print(Panel.fit(
                "[bold blue]Quick Start[/bold blue]\n\n"
                "This will generate a complete dataset with default settings:\n"
                "• 7,000 accounts with holdings\n"
                "• 500+ news articles\n"
                "• 100+ reports\n"
                "• Ingest to Elasticsearch (if configured)",
                title="🚀 Quick Start"
            ))
            
            if not Confirm.ask("Proceed with quick start?", default=False):
                return
        
        # Set up quick start configuration
        config = {
            'generate_accounts': True,
            'generate_news': True,
            'generate_reports': True,
            'ingest_elasticsearch': True,
            'preset': 'full_dataset'
        }
        
        self._execute_generation(config)
    
    def _custom_generation(self):
        """Run custom generation with user-specified options."""
        self.console.print(Panel.fit(
            "[bold green]Custom Generation[/bold green]\n\n"
            "Configure your data generation settings",
            title="⚙️ Custom Generation"
        ))
        
        config = self._gather_custom_config()
        
        if self._confirm_execution(config):
            self._execute_generation(config)
    
    def _trigger_events(self, interactive=True, event_type=None):
        """Trigger controlled events for demo purposes."""
        if interactive:
            event_type = self.menu_system.show_event_menu()
        
        if event_type:
            config = {
                'trigger_event': True,
                'event_type': event_type,
                'generate_accounts': False,
                'generate_news': False,
                'generate_reports': False
            }
            self._execute_generation(config)
    
    def _check_status(self):
        """Display current system status and configuration."""
        self.menu_system.show_status(self.config_manager, interactive=False)
    
    def _check_indices(self):
        """Check and display Elasticsearch index status only."""
        self.menu_system.show_index_status_only()
    
    def _update_timestamps(self, offset_hours=0):
        """Update timestamps in Elasticsearch indices."""
        self.menu_system.update_elasticsearch_timestamps(offset_hours)
    
    def _update_data_files(self, offset_hours=0):
        """Update timestamps in data files."""
        self.menu_system.update_data_file_timestamps(offset_hours)
    
    def _manage_indices(self):
        """Manage Elasticsearch indices."""
        self.menu_system.show_index_management_menu()
    
    def _configure_settings(self):
        """Configure system settings and presets."""
        self.menu_system.show_configuration_menu(self.config_manager)
    
    def _dry_run_mode(self):
        """Show what would be executed without actually running."""
        self.console.print(Panel.fit(
            "[bold yellow]Dry Run Mode[/bold yellow]\n\n"
            "Preview what would be executed without running",
            title="🔍 Dry Run"
        ))
        
        config = self._gather_custom_config()
        self._show_execution_plan(config)
    
    def _gather_custom_config(self) -> Dict[str, Any]:
        """Gather custom configuration from user input."""
        config = {}
        
        # Accounts & Holdings
        config['generate_accounts'] = Confirm.ask("Generate Accounts & Holdings?", default=False)
        if config['generate_accounts']:
            config['num_accounts'] = int(Prompt.ask("Number of accounts", default="7000"))
            config['min_holdings'] = int(Prompt.ask("Min holdings per account", default="10"))
            config['max_holdings'] = int(Prompt.ask("Max holdings per account", default="25"))
        
        # News & Reports
        config['generate_news'] = Confirm.ask("Generate News & Reports?", default=False)
        if config['generate_news']:
            config['num_news'] = int(Prompt.ask("Number of news articles", default="500"))
            config['num_reports'] = int(Prompt.ask("Number of reports", default="100"))
            config['include_specific_news'] = Confirm.ask("Include specific company news?", default=True)
        
        # Elasticsearch
        config['ingest_elasticsearch'] = Confirm.ask("Ingest to Elasticsearch?", default=False)
        
        return config
    
    def _confirm_execution(self, config: Dict[str, Any]) -> bool:
        """Show execution plan and confirm with user."""
        self._show_execution_plan(config)
        return Confirm.ask("Proceed with generation?", default=True)
    
    def _show_execution_plan(self, config: Dict[str, Any]):
        """Display what will be executed."""
        table = Table(title="📋 Execution Plan")
        table.add_column("Task", style="cyan", no_wrap=True)
        table.add_column("Details", style="white")
        table.add_column("Status", style="green")
        
        if config.get('generate_accounts'):
            table.add_row(
                "Generate Accounts",
                f"{config.get('num_accounts', 7000)} accounts with {config.get('min_holdings', 10)}-{config.get('max_holdings', 25)} holdings",
                "✓ Enabled"
            )
        
        if config.get('generate_news'):
            table.add_row(
                "Generate News",
                f"{config.get('num_news', 500)} articles, specific news: {config.get('include_specific_news', True)}",
                "✓ Enabled"
            )
        
        if config.get('generate_reports'):
            table.add_row(
                "Generate Reports",
                f"{config.get('num_reports', 100)} reports",
                "✓ Enabled"
            )
        
        if config.get('ingest_elasticsearch'):
            table.add_row(
                "Elasticsearch",
                "Ingest all generated data",
                "✓ Enabled"
            )
        
        if config.get('trigger_event'):
            table.add_row(
                "Trigger Event",
                f"Event type: {config.get('event_type', 'unknown')}",
                "✓ Enabled"
            )
        
        self.console.print(table)
    
    def _execute_generation(self, config: Dict[str, Any]):
        """Execute the data generation with live progress tracking."""
        self._operations_running = True
        
        try:
            self.task_executor.execute_tasks(config)
        finally:
            self._operations_running = False
    
    def _run_custom_from_args(self, args):
        """Run custom generation from command-line arguments."""
        config = {
            'generate_accounts': args.accounts,
            'generate_news': args.news,
            'generate_reports': args.reports,
            'ingest_elasticsearch': args.elasticsearch,
            'num_accounts': args.num_accounts,
            'num_news': args.num_news,
            'num_reports': args.num_reports,
            'update_timestamps_on_load': args.update_timestamps_on_load if hasattr(args, 'update_timestamps_on_load') else False,
            'timestamp_offset': args.timestamp_offset if hasattr(args, 'timestamp_offset') else 0
        }
        self._execute_generation(config)

def setup_argparse():
    """Setup command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Interactive Synthetic Financial Data Generation Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python control.py                           # Interactive mode
  python control.py --quick-start             # Quick start with defaults
  python control.py --custom --accounts --news --num-accounts 100
  python control.py --trigger-event bad_news  # Trigger bad news event
  python control.py --status                  # Show full system status
  python control.py --check-indices           # Check ES indices only
  python control.py --update-timestamps       # Update timestamps in ES to now
  python control.py --update-timestamps --timestamp-offset -24  # 24 hours ago
  python control.py --custom --elasticsearch --update-timestamps-on-load  # Load with current timestamps
        """
    )
    
    parser.add_argument("--quick-start", action="store_true",
                       help="Run quick start with default settings")
    parser.add_argument("--custom", action="store_true",
                       help="Run custom generation (requires additional flags)")
    parser.add_argument("--accounts", action="store_true",
                       help="Generate accounts and holdings")
    parser.add_argument("--news", action="store_true",
                       help="Generate news articles")
    parser.add_argument("--reports", action="store_true",
                       help="Generate reports")
    parser.add_argument("--elasticsearch", action="store_true",
                       help="Ingest to Elasticsearch")
    parser.add_argument("--update-timestamps-on-load", action="store_true",
                       help="Update timestamps to current time during data loading")
    parser.add_argument("--num-accounts", type=int, default=7000,
                       help="Number of accounts to generate")
    parser.add_argument("--num-news", type=int, default=500,
                       help="Number of news articles to generate")
    parser.add_argument("--num-reports", type=int, default=100,
                       help="Number of reports to generate")
    parser.add_argument("--trigger-event", choices=["bad_news", "market_crash", "volatility"],
                       help="Trigger a specific event type")
    parser.add_argument("--status", action="store_true",
                       help="Show system status and exit")
    parser.add_argument("--check-indices", action="store_true",
                       help="Check Elasticsearch index status only")
    parser.add_argument("--update-timestamps", action="store_true",
                       help="Update timestamps in Elasticsearch to current time")
    parser.add_argument("--timestamp-offset", type=int, default=0,
                       help="Hours offset from now (negative for past, positive for future)")
    parser.add_argument("--update-files", action="store_true",
                       help="Update timestamps in data files before loading")
    
    return parser

def main():
    """Main entry point."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Initialize controller
    controller = SyntheticDataController()
    
    # Determine if running in interactive mode
    if len(sys.argv) == 1:
        # No arguments provided, run interactive mode
        controller.run_interactive()
    else:
        # Arguments provided, run non-interactive mode
        controller.run_non_interactive(args)

if __name__ == "__main__":
    main()