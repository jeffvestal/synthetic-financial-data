lib/menu_system.py"""
Menu System for Synthetic Financial Data Generator

Handles all menu display, navigation, and user interaction.
"""

import os
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

class MenuSystem:
    """Handles all menu operations and user interface."""

    def __init__(self, console: Console):
        self.console = console

    def show_welcome(self):
        """Display the welcome screen."""
        self.console.clear()

        # ASCII Robot reading financial newspaper
        robot_art = """

        ╭─────────────────────────────────────╮
        │    🤖 ROBO-ANALYST 3000 📊          │
        ╰─────────────────────────────────────╯
                    ╭───╮
                   ╭┤ ● ●├╮
                   │╰─┬─┬─╯│
                   │  │ │  │
                ╭──╯  ╰─╯  ╰──╮
                │ ╭─────────╮ │
                │ │FINANCIAL│ │
                │ │   DATA  │ │
                │ │ ═══════ │ │
                │ │📈 MARKET│ │
                │ │📊 NEWS  │ │
                │ │💰 PROFIT│ │
                │ ╰─────────╯ │
                ╰─╮         ╭─╯
                  │ ╱╲   ╱╲ │
                  ╰─╯ ╲─╱ ╰─╯
                      ╱─╲
                    ╱─╯ ╰─╲
        """

        # Create colored robot text
        robot_text = Text()
        for line in robot_art.strip().split('\n'):
            if 'ROBO-ANALYST' in line or '🤖' in line:
                robot_text.append(line + '\n', style="bold cyan")
            elif 'FINANCIAL' in line or 'DATA' in line:
                robot_text.append(line + '\n', style="bold yellow")
            elif 'MARKET' in line or 'NEWS' in line or 'PROFIT' in line:
                robot_text.append(line + '\n', style="bold green")
            elif '📈' in line or '📊' in line or '💰' in line:
                robot_text.append(line + '\n', style="bright_magenta")
            else:
                robot_text.append(line + '\n', style="bright_blue")

        # Display the robot
        self.console.print(Align.center(robot_text))
        self.console.print()

        welcome_text = Text.assemble(
            ("🏦", "bold blue"),
            (" Synthetic Financial Data Generator", "bold white"),
            ("\n"),
            ("Generate realistic financial data for testing and demos", "dim white"),
        )

        panel = Panel(
            Align.center(welcome_text),
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print()

    def show_main_menu(self) -> str:
        """Display main menu and return user choice."""

        menu_items = [
            ("1", "🚀 Quick Start", "Generate all data with defaults"),
            ("2", "⚙️  Custom Generation", "Configure specific generation options"),
            ("3", "💥 Trigger Events", "Create controlled market events"),
            ("4", "📊 Check Status", "View system status and data"),
            ("5", "🗄️  Manage Indices", "Manage Elasticsearch indices"),
            ("6", "🕐 Update Timestamps", "Update timestamps in Elasticsearch data"),
            ("7", "🔧 Configure Settings", "Manage configuration and presets"),
            ("8", "🔍 Test & Retry ES", "Test connectivity and retry data ingestion"),
            ("9", "🔄 Dry Run Mode", "Preview execution without running"),
            ("10", "🚪 Exit", "Exit the application"),
        ]

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Choice", style="bold cyan", width=3)
        table.add_column("Action", style="bold white", width=20)
        table.add_column("Description", style="dim white")

        for choice, action, description in menu_items:
            table.add_row(choice, action, description)

        panel = Panel(
            table,
            title="🏠 Main Menu",
            border_style="green"
        )

        self.console.print(panel)

        return Prompt.ask(
            "\n[bold cyan]Choose an option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default="1"
        )

    def show_event_menu(self) -> Optional[str]:
        """Display event trigger menu."""

        event_items = [
            ("1", "📉 Bad News Event", "Generate negative news for TSLA and FCX"),
            ("2", "💥 Market Crash", "Simulate market-wide negative event"),
            ("3", "📈 Volatility Spike", "Create high volatility scenario"),
            ("4", "🕵️  Insider Trading", "Generate pre-announcement trading scenarios"),
            ("5", "🔄 Wash Trading", "Create circular trading patterns"),
            ("6", "🎯 Pump & Dump", "Generate coordinated manipulation schemes"),
            ("7", "🔙 Back to Main Menu", "Return to main menu"),
        ]

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Choice", style="bold cyan", width=3)
        table.add_column("Event", style="bold white", width=25)
        table.add_column("Description", style="dim white")

        for choice, event, description in event_items:
            table.add_row(choice, event, description)

        panel = Panel(
            table,
            title="💥 Event Triggers",
            border_style="red"
        )

        self.console.print(panel)

        choice = Prompt.ask(
            "\n[bold cyan]Choose an event[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="7"
        )

        event_map = {
            "1": "bad_news",
            "2": "market_crash",
            "3": "volatility",
            "4": "insider_trading",
            "5": "wash_trading",
            "6": "pump_and_dump",
            "7": None
        }

        return event_map.get(choice)

    def show_timestamp_menu(self) -> Optional[dict]:
        """Display timestamp update menu and return selected options."""

        timestamp_items = [
            ("1", "⏰ Update All to Current Time", "Update all indices to current timestamp"),
            ("2", "📅 Update All with Offset", "Update all indices with time offset (hours)"),
            ("3", "📋 Update Specific Indices", "Choose which indices to update"),
            ("4", "🔍 Preview Changes (Dry Run)", "Show what would be updated without making changes"),
            ("5", "⚙️  Advanced Options", "Combined offset + specific indices"),
            ("6", "🔙 Back to Main Menu", "Return to main menu"),
        ]

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Choice", style="bold cyan", width=3)
        table.add_column("Action", style="bold white", width=28)
        table.add_column("Description", style="dim white")

        for choice, action, description in timestamp_items:
            table.add_row(choice, action, description)

        panel = Panel(
            table,
            title="🕐 Timestamp Update Options",
            border_style="yellow"
        )

        self.console.print(panel)

        choice = Prompt.ask(
            "\n[bold cyan]Choose an option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6"],
            default="6"
        )

        if choice == "6":
            return None  # Back to main menu

        # Handle each option
        if choice == "1":
            return {"action": "update_all", "offset": 0, "dry_run": False}

        elif choice == "2":
            offset = self._prompt_for_offset()
            if offset is not None:
                return {"action": "update_all", "offset": offset, "dry_run": False}
            return None

        elif choice == "3":
            indices = self._prompt_for_indices()
            if indices:
                return {"action": "update_specific", "indices": indices, "offset": 0, "dry_run": False}
            return None

        elif choice == "4":
            return {"action": "update_all", "offset": 0, "dry_run": True}

        elif choice == "5":
            # Advanced options - get both offset and indices
            offset = self._prompt_for_offset()
            if offset is not None:
                indices = self._prompt_for_indices()
                if indices:
                    dry_run = Confirm.ask("Preview changes only (dry run)?", default=False)
                    return {
                        "action": "update_specific",
                        "indices": indices,
                        "offset": offset,
                        "dry_run": dry_run
                    }
            return None

        return None

    def _prompt_for_offset(self) -> Optional[int]:
        """Prompt user for time offset in hours."""
        try:
            offset_str = Prompt.ask(
                "\n[bold cyan]Enter time offset in hours[/bold cyan]\n"
                "[dim](negative for past, positive for future, 0 for current time)[/dim]",
                default="0"
            )
            return int(offset_str)
        except ValueError:
            self.console.print("[red]❌ Invalid offset. Please enter a number.[/red]")
            return None

    def _prompt_for_indices(self) -> Optional[list]:
        """Prompt user to select specific indices."""

        # Available indices
        indices_info = [
            ("1", "financial_accounts", "Customer account data"),
            ("2", "financial_holdings", "Portfolio holdings"),
            ("3", "financial_asset_details", "Asset pricing and metadata"),
            ("4", "financial_news", "Market news articles"),
            ("5", "financial_reports", "Financial reports"),
        ]

        self.console.print("\n[bold cyan]Select indices to update:[/bold cyan]")

        # Create table for indices selection
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Choice", style="bold cyan", width=3)
        table.add_column("Index", style="bold white", width=25)
        table.add_column("Description", style="dim white")

        for choice, index, description in indices_info:
            table.add_row(choice, index.replace("financial_", ""), description)

        panel = Panel(
            table,
            title="📋 Available Indices",
            border_style="blue"
        )

        self.console.print(panel)

        selections = Prompt.ask(
            "\n[bold cyan]Enter index numbers (comma-separated)[/bold cyan]\n"
            "[dim](e.g., 1,3,4 for accounts, assets, and news)[/dim]",
            default=""
        )

        if not selections.strip():
            return None

        try:
            selected_numbers = [int(x.strip()) for x in selections.split(",")]
            selected_indices = []

            index_map = {
                1: "financial_accounts",
                2: "financial_holdings",
                3: "financial_asset_details",
                4: "financial_news",
                5: "financial_reports"
            }

            for num in selected_numbers:
                if num in index_map:
                    selected_indices.append(index_map[num])
                else:
                    self.console.print(f"[yellow]⚠️  Skipping invalid selection: {num}[/yellow]")

            if selected_indices:
                return selected_indices
            else:
                self.console.print("[red]❌ No valid indices selected.[/red]")
                return None

        except ValueError:
            self.console.print("[red]❌ Invalid selection format. Please use numbers separated by commas.[/red]")
            return None

    def show_status(self, config_manager, interactive=True):
        """Display current system status."""

        # Environment Status
        env_table = Table(title="🌍 Environment Status")
        env_table.add_column("Variable", style="cyan")
        env_table.add_column("Status", style="white")

        # Check environment variables with context
        es_endpoint = os.getenv("ES_ENDPOINT_URL", "Not Set")
        es_key_set = bool(os.getenv("ES_API_KEY"))
        gemini_key_set = bool(os.getenv("GEMINI_API_KEY"))

        # Add rows with appropriate status messages
        env_table.add_row("ES_ENDPOINT_URL", es_endpoint)
        env_table.add_row("ES_API_KEY", "✓ Set" if es_key_set else "❌ Not Set")

        # Gemini API key with context about when it's needed
        if gemini_key_set:
            gemini_status = "✓ Set"
        else:
            gemini_status = "⚠️ Not Set (only needed for generating new data)"
        env_table.add_row("GEMINI_API_KEY", gemini_status)

        # File Status
        file_table = Table(title="📁 File Status")
        file_table.add_column("File Type", style="cyan")
        file_table.add_column("Status", style="white")
        file_table.add_column("Count/Size", style="dim white")

        # Check data files
        data_dir = "generated_data"
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            file_table.add_row("Generated Data", "✓ Available", f"{len(files)} files")
        else:
            file_table.add_row("Generated Data", "❌ Missing", "No data directory")

        # Check prompt files
        prompt_dir = "prompts"
        if os.path.exists(prompt_dir):
            files = [f for f in os.listdir(prompt_dir) if f.endswith('.txt')]
            file_table.add_row("Prompt Templates", "✓ Available", f"{len(files)} templates")
        else:
            file_table.add_row("Prompt Templates", "❌ Missing", "No prompts directory")

        # Configuration Status
        config_table = Table(title="⚙️ Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")

        # Get current config values
        config_values = config_manager.get_current_config()
        for key, value in config_values.items():
            config_table.add_row(key.replace('_', ' ').title(), str(value))

        # Elasticsearch Status
        es_status = config_manager.get_elasticsearch_status()
        es_table = Table(title="🔍 Elasticsearch Status")
        es_table.add_column("Component", style="cyan")
        es_table.add_column("Status", style="white")
        es_table.add_column("Details", style="dim white")

        # Basic configuration
        config_status = "✓ Configured" if es_status['configured'] else "❌ Not Configured"
        es_table.add_row("Configuration", config_status, es_status['endpoint'])

        # Connection test
        if es_status['configured']:
            if es_status['connection_test']:
                connection_status = "✓ Connected"
                cluster_info = es_status['cluster_info']
                details = f"{cluster_info['cluster_name']} v{cluster_info['version']}"
                if cluster_info.get('status'):
                    status_color = {
                        'green': '✓',
                        'yellow': '⚠️',
                        'red': '❌'
                    }.get(cluster_info['status'], '?')
                    details += f" ({status_color} {cluster_info['status']})"
            else:
                connection_status = "❌ Connection Failed"
                details = es_status['error'] if es_status['error'] else "Unknown error"
            es_table.add_row("Connection", connection_status, details)
        else:
            es_table.add_row("Connection", "⏸️  Not Tested", "Missing credentials")

        # Display all tables
        self.console.print(Columns([env_table, file_table], equal=True))
        self.console.print(es_table)
        self.console.print(config_table)

        # Add note about API key requirements
        self.console.print("\n[dim]📝 Note: API Key Requirements:[/dim]")
        self.console.print("[dim]   • GEMINI_API_KEY: Only required for generating new data (accounts, news, reports)[/dim]")
        self.console.print("[dim]   • ES_API_KEY: Required for loading data to Elasticsearch[/dim]")
        self.console.print("[dim]   • For loading existing data only, GEMINI_API_KEY is not needed[/dim]")

        # Pause for user only in interactive mode
        if interactive:
            self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def show_configuration_menu(self, config_manager):
        """Display configuration management menu."""

        while True:
            config_items = [
                ("1", "👁️  View Current Config", "Show all current settings"),
                ("2", "📝 Edit Settings", "Modify configuration values"),
                ("3", "💾 Save Preset", "Save current settings as preset"),
                ("4", "📂 Load Preset", "Load saved configuration preset"),
                ("5", "🔍 Validate Config", "Check configuration validity"),
                ("6", "🔙 Back to Main Menu", "Return to main menu"),
            ]

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Choice", style="bold cyan", width=3)
            table.add_column("Action", style="bold white", width=25)
            table.add_column("Description", style="dim white")

            for choice, action, description in config_items:
                table.add_row(choice, action, description)

            panel = Panel(
                table,
                title="🔧 Configuration Management",
                border_style="yellow"
            )

            self.console.print(panel)

            choice = Prompt.ask(
                "\n[bold cyan]Choose an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "6"],
                default="6"
            )

            if choice == "1":
                self._show_current_config(config_manager)
            elif choice == "2":
                self._edit_settings(config_manager)
            elif choice == "3":
                self._save_preset(config_manager)
            elif choice == "4":
                self._load_preset(config_manager)
            elif choice == "5":
                self._validate_config(config_manager)
            elif choice == "6":
                break

    def _show_current_config(self, config_manager):
        """Display current configuration values."""
        config = config_manager.get_current_config()

        table = Table(title="📋 Current Configuration")
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="white")
        table.add_column("Type", style="dim white")

        for key, value in config.items():
            table.add_row(
                key.replace('_', ' ').title(),
                str(value),
                type(value).__name__
            )

        self.console.print(table)
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _edit_settings(self, config_manager):
        """Edit configuration settings."""
        while True:
            # Create configuration sections menu
            sections_table = Table(title="⚙️ Configuration Sections")
            sections_table.add_column("Option", style="cyan", width=8)
            sections_table.add_column("Section", style="white")
            sections_table.add_column("Description", style="dim")

            sections_table.add_row("1", "Generation Settings", "Data volume and generation parameters")
            sections_table.add_row("2", "Elasticsearch Config", "Connection and index settings")
            sections_table.add_row("3", "Gemini API Config", "AI model and API settings")
            sections_table.add_row("4", "File Paths", "Output directories and file locations")
            sections_table.add_row("b", "Back", "Return to main settings menu")

            self.console.print(sections_table)

            choice = Prompt.ask(
                "Select section to edit",
                choices=["1", "2", "3", "4", "b"],
                default="b"
            )

            if choice == "1":
                self._edit_generation_settings(config_manager)
            elif choice == "2":
                self._edit_elasticsearch_config(config_manager)
            elif choice == "3":
                self._edit_gemini_config(config_manager)
            elif choice == "4":
                self._edit_file_paths(config_manager)
            elif choice == "b":
                break

    def _edit_generation_settings(self, config_manager):
        """Edit generation volume settings."""
        config = config_manager.get_current_config()
        generation_settings = config.get('GENERATION_SETTINGS', {})

        while True:
            # Display current settings
            settings_table = Table(title="📊 Generation Settings")
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Current Value", style="white")
            settings_table.add_column("Description", style="dim")

            # Accounts settings
            accounts = generation_settings.get('accounts', {})
            settings_table.add_row("1. Accounts Count", str(accounts.get('num_accounts', 7000)), "Total number of accounts to generate")
            settings_table.add_row("2. Min Holdings/Account", str(accounts.get('min_holdings_per_account', 10)), "Minimum holdings per account")
            settings_table.add_row("3. Max Holdings/Account", str(accounts.get('max_holdings_per_account', 25)), "Maximum holdings per account")

            # News settings
            news = generation_settings.get('news', {})
            settings_table.add_row("4. General News Articles", str(news.get('num_general_articles', 500)), "Number of general market news articles")
            settings_table.add_row("5. Specific News per Asset", str(news.get('num_specific_per_asset', 1)), "Company-specific news per asset")
            settings_table.add_row("6. Assets for News", str(news.get('num_specific_assets_for_news', 50)), "Number of assets to generate news for")

            # Reports settings
            reports = generation_settings.get('reports', {})
            settings_table.add_row("7. Thematic Reports", str(reports.get('num_thematic_reports', 100)), "Number of sector/thematic reports")
            settings_table.add_row("8. Specific Reports per Asset", str(reports.get('num_specific_per_asset', 1)), "Company-specific reports per asset")
            settings_table.add_row("9. Assets for Reports", str(reports.get('num_specific_assets_for_reports', 20)), "Number of assets to generate reports for")

            self.console.print(settings_table)

            choice = Prompt.ask(
                "Select setting to edit (1-9) or 'b' for back",
                choices=[str(i) for i in range(1, 10)] + ["b"],
                default="b"
            )

            if choice == "b":
                break
            elif choice == "1":
                new_value = self._get_int_input("Number of accounts", accounts.get('num_accounts', 7000))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'accounts', 'num_accounts'], new_value)
            elif choice == "2":
                new_value = self._get_int_input("Min holdings per account", accounts.get('min_holdings_per_account', 10))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'accounts', 'min_holdings_per_account'], new_value)
            elif choice == "3":
                new_value = self._get_int_input("Max holdings per account", accounts.get('max_holdings_per_account', 25))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'accounts', 'max_holdings_per_account'], new_value)
            elif choice == "4":
                new_value = self._get_int_input("General news articles", news.get('num_general_articles', 500))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'news', 'num_general_articles'], new_value)
            elif choice == "5":
                new_value = self._get_int_input("Specific news per asset", news.get('num_specific_per_asset', 1))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'news', 'num_specific_per_asset'], new_value)
            elif choice == "6":
                new_value = self._get_int_input("Assets for news", news.get('num_specific_assets_for_news', 50))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'news', 'num_specific_assets_for_news'], new_value)
            elif choice == "7":
                new_value = self._get_int_input("Thematic reports", reports.get('num_thematic_reports', 100))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'reports', 'num_thematic_reports'], new_value)
            elif choice == "8":
                new_value = self._get_int_input("Specific reports per asset", reports.get('num_specific_per_asset', 1))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'reports', 'num_specific_per_asset'], new_value)
            elif choice == "9":
                new_value = self._get_int_input("Assets for reports", reports.get('num_specific_assets_for_reports', 20))
                if new_value is not None:
                    config_manager.update_config(['GENERATION_SETTINGS', 'reports', 'num_specific_assets_for_reports'], new_value)

    def _edit_elasticsearch_config(self, config_manager):
        """Edit Elasticsearch configuration."""
        config = config_manager.get_current_config()
        es_config = config.get('ES_CONFIG', {})

        while True:
            # Display current settings
            settings_table = Table(title="🔍 Elasticsearch Configuration")
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Current Value", style="white")
            settings_table.add_column("Description", style="dim")

            # Get current API key status and source
            api_key_status = self._get_api_key_status('ES_API_KEY')
            
            settings_table.add_row("1. API Key", api_key_status, "Elasticsearch API key for authentication")
            settings_table.add_row("2. Endpoint URL", str(es_config.get('endpoint_url', 'https://localhost:9200')), "Elasticsearch server URL")
            settings_table.add_row("3. Batch Size", str(es_config.get('bulk_batch_size', 100)), "Documents per bulk request")
            settings_table.add_row("4. Request Timeout", str(es_config.get('request_timeout', 60)), "Request timeout in seconds")
            settings_table.add_row("5. Verify Certs", str(es_config.get('verify_certs', False)), "Verify SSL certificates")
            settings_table.add_row("6. Auto Create Indices", str(es_config.get('auto_create_indices', True)), "Automatically create missing indices")

            self.console.print(settings_table)

            choice = Prompt.ask(
                "Select setting to edit (1-6) or 'b' for back",
                choices=[str(i) for i in range(1, 7)] + ["b"],
                default="b"
            )

            if choice == "b":
                break
            elif choice == "1":
                self._edit_api_key("ES_API_KEY", "Elasticsearch")
            elif choice == "2":
                new_value = self._get_string_input("Elasticsearch endpoint URL", es_config.get('endpoint_url', 'https://localhost:9200'))
                if new_value is not None:
                    # Update in-memory config
                    config_manager.update_config(['ES_CONFIG', 'endpoint_url'], new_value)
                    # Save to .env file and reload
                    os.environ['ES_ENDPOINT_URL'] = new_value
                    if self._save_to_env_file('ES_ENDPOINT_URL', new_value):
                        self._reload_environment()
                        # Also update the cached ES_CONFIG
                        self._update_es_config()
                        self.console.print("[green]✓ Elasticsearch endpoint URL updated and saved[/green]")
                    else:
                        self.console.print("[yellow]⚠️ Endpoint updated for session, but could not save to .env file[/yellow]")
            elif choice == "3":
                new_value = self._get_int_input("Batch size", es_config.get('bulk_batch_size', 100))
                if new_value is not None:
                    config_manager.update_config(['ES_CONFIG', 'bulk_batch_size'], new_value)
            elif choice == "4":
                new_value = self._get_int_input("Request timeout (seconds)", es_config.get('request_timeout', 60))
                if new_value is not None:
                    config_manager.update_config(['ES_CONFIG', 'request_timeout'], new_value)
            elif choice == "5":
                new_value = self._get_bool_input("Verify SSL certificates", es_config.get('verify_certs', False))
                if new_value is not None:
                    config_manager.update_config(['ES_CONFIG', 'verify_certs'], new_value)
            elif choice == "6":
                new_value = self._get_bool_input("Auto create indices", es_config.get('auto_create_indices', True))
                if new_value is not None:
                    config_manager.update_config(['ES_CONFIG', 'auto_create_indices'], new_value)

    def _edit_gemini_config(self, config_manager):
        """Edit Gemini API configuration."""
        config = config_manager.get_current_config()
        gemini_config = config.get('GEMINI_CONFIG', {})

        while True:
            # Display current settings
            settings_table = Table(title="🤖 Gemini API Configuration")
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Current Value", style="white")
            settings_table.add_column("Description", style="dim")

            # Get current API key status and source
            gemini_api_key_status = self._get_api_key_status('GEMINI_API_KEY')
            
            settings_table.add_row("1. API Key", gemini_api_key_status, "Gemini API key for AI generation")
            settings_table.add_row("2. Model Name", str(gemini_config.get('model_name', 'gemini-2.5-pro')), "Gemini model to use")
            settings_table.add_row("3. Request Delay", str(gemini_config.get('request_delay_seconds', 0.5)), "Delay between requests (seconds)")
            settings_table.add_row("4. Max Retries", str(gemini_config.get('max_retries', 3)), "Maximum retry attempts")
            settings_table.add_row("5. Response MIME Type", str(gemini_config.get('response_mime_type', 'application/json')), "Expected response format")

            self.console.print(settings_table)

            choice = Prompt.ask(
                "Select setting to edit (1-5) or 'b' for back",
                choices=[str(i) for i in range(1, 6)] + ["b"],
                default="b"
            )

            if choice == "b":
                break
            elif choice == "1":
                self._edit_api_key("GEMINI_API_KEY", "Gemini")
            elif choice == "2":
                new_value = self._get_string_input("Gemini model name", gemini_config.get('model_name', 'gemini-2.5-pro'))
                if new_value is not None:
                    config_manager.update_config(['GEMINI_CONFIG', 'model_name'], new_value)
            elif choice == "3":
                new_value = self._get_float_input("Request delay (seconds)", gemini_config.get('request_delay_seconds', 0.5))
                if new_value is not None:
                    config_manager.update_config(['GEMINI_CONFIG', 'request_delay_seconds'], new_value)
            elif choice == "4":
                new_value = self._get_int_input("Max retries", gemini_config.get('max_retries', 3))
                if new_value is not None:
                    config_manager.update_config(['GEMINI_CONFIG', 'max_retries'], new_value)
            elif choice == "5":
                new_value = self._get_string_input("Response MIME type", gemini_config.get('response_mime_type', 'application/json'))
                if new_value is not None:
                    config_manager.update_config(['GEMINI_CONFIG', 'response_mime_type'], new_value)

    def _edit_file_paths(self, config_manager):
        """Edit file path configuration."""
        self.console.print("[yellow]File paths are automatically managed and should not be edited directly.[/yellow]")
        self.console.print("[dim]File paths are based on the project structure and generated data directory.[/dim]")
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _get_int_input(self, setting_name: str, current_value: int) -> Optional[int]:
        """Get integer input from user with validation."""
        try:
            value_str = Prompt.ask(f"Enter new value for {setting_name}", default=str(current_value))
            if value_str == str(current_value):
                return None  # No change
            new_value = int(value_str)
            if new_value <= 0:
                self.console.print("[red]Value must be positive[/red]")
                return None
            self.console.print(f"[green]✓ {setting_name} updated to {new_value}[/green]")
            return new_value
        except ValueError:
            self.console.print("[red]Invalid integer value[/red]")
            return None

    def _get_float_input(self, setting_name: str, current_value: float) -> Optional[float]:
        """Get float input from user with validation."""
        try:
            value_str = Prompt.ask(f"Enter new value for {setting_name}", default=str(current_value))
            if value_str == str(current_value):
                return None  # No change
            new_value = float(value_str)
            if new_value < 0:
                self.console.print("[red]Value must be non-negative[/red]")
                return None
            self.console.print(f"[green]✓ {setting_name} updated to {new_value}[/green]")
            return new_value
        except ValueError:
            self.console.print("[red]Invalid numeric value[/red]")
            return None

    def _get_string_input(self, setting_name: str, current_value: str) -> Optional[str]:
        """Get string input from user."""
        new_value = Prompt.ask(f"Enter new value for {setting_name}", default=current_value)
        if new_value == current_value:
            return None  # No change
        self.console.print(f"[green]✓ {setting_name} updated to '{new_value}'[/green]")
        return new_value

    def _get_bool_input(self, setting_name: str, current_value: bool) -> Optional[bool]:
        """Get boolean input from user."""
        value_str = Prompt.ask(
            f"Enter new value for {setting_name} (true/false)",
            default=str(current_value).lower(),
            choices=["true", "false"]
        )
        if value_str == str(current_value).lower():
            return None  # No change
        new_value = value_str.lower() == "true"
        self.console.print(f"[green]✓ {setting_name} updated to {new_value}[/green]")
        return new_value

    def _edit_api_key(self, env_var_name: str, service_name: str):
        """Edit API key for a service."""
        current_key = os.getenv(env_var_name)
        current_status = "Set" if current_key else "Not Set"
        
        self.console.print(f"\n[bold]Edit {service_name} API Key[/bold]")
        self.console.print(f"Current status: [{'green' if current_key else 'red'}]{current_status}[/]")
        
        if current_key:
            # Show masked version
            masked_key = current_key[:8] + "..." + current_key[-8:] if len(current_key) > 16 else current_key[:4] + "..." + current_key[-4:]
            self.console.print(f"Current key: [dim]{masked_key}[/dim]")
        
        choices = ["1", "b"]
        choice_text = "1. Set new API key"
        
        if current_key:
            choices.append("2")
            choice_text += ", 2. Clear current key"
        
        self.console.print(f"\nOptions:\n{choice_text}\nb. Back to menu")
        
        choice = Prompt.ask(
            "Select action",
            choices=choices,
            default="b"
        )
        
        if choice == "1":
            self.console.print(f"\n[yellow]⚠️  Security Note:[/yellow]")
            self.console.print("• Input will be hidden for security")
            
            from getpass import getpass
            new_key = getpass(f"\nEnter {service_name} API key (input hidden): ").strip()
            
            if new_key:
                # Set in current session
                os.environ[env_var_name] = new_key
                
                # Always save to .env file automatically
                success = self._save_to_env_file(env_var_name, new_key)
                if success:
                    self.console.print(f"[green]✓ {service_name} API key updated and saved to .env file[/green]")
                    # Reload environment to pick up changes
                    self._reload_environment()
                    # Update ES config cache if this was an ES key
                    if env_var_name.startswith('ES_'):
                        self._update_es_config()
                else:
                    self.console.print(f"[yellow]⚠️ {service_name} API key updated for session, but could not save to .env file[/yellow]")
            else:
                self.console.print("[yellow]No key entered, keeping current setting[/yellow]")
                
        elif choice == "2" and current_key:
            if Confirm.ask(f"Remove {service_name} API key from this session?"):
                del os.environ[env_var_name]
                self.console.print(f"[green]✓ {service_name} API key removed from this session[/green]")
        
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _save_to_env_file(self, env_var_name: str, value: str) -> bool:
        """Save environment variable to .env file."""
        try:
            env_file_path = ".env"
            
            # Read existing .env file or create new content
            env_lines = []
            existing_vars = {}
            
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, _ = line.split('=', 1)
                            existing_vars[key] = line
                        env_lines.append(line)
            else:
                # Create from template if .env doesn't exist
                if os.path.exists('.env.template'):
                    with open('.env.template', 'r') as f:
                        env_lines = [line.rstrip() for line in f]
            
            # Update or add the variable
            new_line = f"{env_var_name}={value}"
            
            # First, remove ALL existing instances of this variable
            env_lines = [line for line in env_lines if not (line.strip().startswith(f"{env_var_name}=") and not line.strip().startswith('#'))]
            
            # Now add the new value in the appropriate section
            added = False
            if env_var_name.startswith('ES_'):
                # Find Elasticsearch section
                for i, line in enumerate(env_lines):
                    if 'Elasticsearch' in line and line.startswith('#'):
                        # Find the end of the ES section to insert the variable
                        j = i + 1
                        while j < len(env_lines) and (env_lines[j].startswith('#') or env_lines[j].strip() == '' or env_lines[j].startswith('ES_')):
                            j += 1
                        env_lines.insert(j, new_line)
                        added = True
                        break
                        
            elif env_var_name.startswith('GEMINI_'):
                # Find Gemini section  
                for i, line in enumerate(env_lines):
                    if 'Gemini' in line and line.startswith('#'):
                        # Find the end of the Gemini section to insert the variable
                        j = i + 1
                        while j < len(env_lines) and (env_lines[j].startswith('#') or env_lines[j].strip() == '' or env_lines[j].startswith('GEMINI_')):
                            j += 1
                        env_lines.insert(j, new_line)
                        added = True
                        break
            
            # If not added to a section, append at the end
            if not added:
                env_lines.append(new_line)
            
            # Write back to file
            with open(env_file_path, 'w') as f:
                f.write('\n'.join(env_lines) + '\n')
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error saving to .env file: {e}[/red]")
            return False

    def _reload_environment(self):
        """Reload environment variables from .env file."""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)  # Override existing env vars
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not reload environment: {e}[/yellow]")

    def _update_es_config(self):
        """Update the cached ES_CONFIG dictionary from current environment."""
        try:
            import sys
            import os
            sys.path.append('scripts')
            from config import ES_CONFIG
            
            # Update the cached ES_CONFIG values
            ES_CONFIG['endpoint_url'] = os.getenv("ES_ENDPOINT_URL", "https://localhost:9200")
            ES_CONFIG['api_key'] = os.getenv("ES_API_KEY")
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not update ES_CONFIG cache: {e}[/yellow]")

    def _get_api_key_status(self, env_var_name: str) -> str:
        """Get API key status with source information."""
        current_key = os.getenv(env_var_name)
        if not current_key:
            return "❌ Not Set"
        
        # Check if key is in .env file
        env_file_path = ".env"
        in_env_file = False
        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith(f"{env_var_name}=") and not line.strip().startswith('#'):
                            in_env_file = True
                            break
            except:
                pass
        
        if in_env_file:
            return "✓ Set (.env file)"
        else:
            return "✓ Set (session only)"

    def _save_preset(self, config_manager):
        """Save current configuration as preset."""
        preset_name = Prompt.ask("Enter preset name")
        if preset_name:
            config_manager.save_preset(preset_name)
            self.console.print(f"[green]✓ Preset '{preset_name}' saved[/green]")
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _load_preset(self, config_manager):
        """Load a saved preset."""
        presets = config_manager.list_presets()
        if not presets:
            self.console.print("[yellow]No presets available[/yellow]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return

        table = Table(title="📂 Available Presets")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")

        for preset in presets:
            table.add_row(preset['name'], preset.get('description', 'No description'))

        self.console.print(table)

        preset_name = Prompt.ask("Enter preset name to load", default="")
        if preset_name:
            config_manager.load_preset(preset_name)
            self.console.print(f"[green]✓ Preset '{preset_name}' loaded[/green]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _validate_config(self, config_manager):
        """Validate current configuration."""
        is_valid, errors = config_manager.validate_config()

        if is_valid:
            self.console.print("[green]✓ Configuration is valid[/green]")
        else:
            self.console.print("[red]❌ Configuration has errors:[/red]")
            for error in errors:
                self.console.print(f"  • [red]{error}[/red]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def show_es_test_menu(self):
        """Show Elasticsearch testing and retry menu."""
        while True:
            self.console.clear()
            
            # Test current ES connectivity
            try:
                import sys
                sys.path.append('scripts')
                from config import ES_CONFIG
                from common_utils import create_elasticsearch_client
            except ImportError:
                self.console.print("[red]Could not import ES modules[/red]")
                self.console.input("\n[dim]Press Enter to continue...[/dim]")
                return
            
            # Display current ES status
            table = Table(title="🔍 Elasticsearch Test & Retry")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Details", style="dim")
            
            # Check configuration
            endpoint = ES_CONFIG.get('endpoint_url', 'Not set')
            api_key_set = "✓ Set" if ES_CONFIG.get('api_key') else "❌ Not Set"
            
            table.add_row("Endpoint", endpoint, "Elasticsearch server URL")
            table.add_row("API Key", api_key_set, "Authentication credential")
            
            # Test connectivity if configured
            connection_status = "⏸️ Not Tested"
            connection_details = ""
            
            if ES_CONFIG.get('api_key') and ES_CONFIG.get('endpoint_url'):
                try:
                    es_client = create_elasticsearch_client()
                    cluster_info = es_client.info()
                    connection_status = "✅ Connected"
                    connection_details = f"ES {cluster_info.get('version', {}).get('number', 'Unknown')}"
                except Exception as e:
                    connection_status = "❌ Failed"
                    connection_details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            else:
                connection_details = "Missing credentials"
            
            table.add_row("Connection", connection_status, connection_details)
            
            self.console.print(table)
            
            # Menu options
            self.console.print("\n[bold]Options:[/bold]")
            self.console.print("1. Test connection")
            self.console.print("2. Retry ingestion of existing files")
            self.console.print("3. View available data files")
            self.console.print("4. Configure API keys")
            self.console.print("5. Back to main menu")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5"],
                default="5"
            )
            
            if choice == "1":
                self._test_es_connection()
            elif choice == "2":
                self._retry_es_ingestion()
            elif choice == "3":
                self._show_available_files()
            elif choice == "4":
                # Quick shortcut to ES config
                from lib.config_manager import ConfigManager
                config_manager = ConfigManager()
                self._edit_elasticsearch_config(config_manager)
            elif choice == "5":
                break

    def _test_es_connection(self):
        """Test Elasticsearch connection."""
        self.console.print("\n[blue]Testing Elasticsearch connection...[/blue]")
        
        try:
            import sys
            sys.path.append('scripts')
            from common_utils import create_elasticsearch_client
        except ImportError:
            self.console.print("[red]Could not import ES modules[/red]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return
        
        try:
            es_client = create_elasticsearch_client()
            cluster_info = es_client.info()
            
            self.console.print("[green]✅ Connection successful![/green]")
            self.console.print(f"  Cluster: {cluster_info.get('cluster_name', 'Unknown')}")
            self.console.print(f"  Version: {cluster_info.get('version', {}).get('number', 'Unknown')}")
            
            # Test cluster health
            try:
                health = es_client.cluster.health()
                status_color = {"green": "green", "yellow": "yellow", "red": "red"}.get(health.get('status', 'unknown'), "white")
                self.console.print(f"  Health: [{status_color}]{health.get('status', 'unknown')}[/{status_color}]")
                self.console.print(f"  Nodes: {health.get('number_of_nodes', 0)}")
            except Exception:
                self.console.print("  Health: Could not retrieve")
                
        except Exception as e:
            self.console.print(f"[red]❌ Connection failed: {e}[/red]")
            
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _retry_es_ingestion(self):
        """Retry ingesting existing data files to Elasticsearch."""
        self.console.print("\n[blue]Checking for existing data files...[/blue]")
        
        # Check available files
        import os
        data_dir = "generated_data"
        
        if not os.path.exists(data_dir):
            self.console.print("[red]No generated_data directory found[/red]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return
        
        # Map files to indices
        file_mapping = {
            "generated_accounts.jsonl": ("financial_accounts", "account_id", "Accounts"),
            "generated_holdings.jsonl": ("financial_holdings", "holding_id", "Holdings"),
            "generated_asset_details.jsonl": ("financial_asset_details", "symbol", "Asset Details"),
            "generated_news.jsonl": ("financial_news", "article_id", "News Articles"),
            "generated_reports.jsonl": ("financial_reports", "report_id", "Reports"),
            "financial_trades.jsonl": ("financial_trades", "trade_id", "Trade Activity")
        }
        
        available_files = []
        for filename, (index, id_field, display_name) in file_mapping.items():
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if file_size > 0:
                    # Count lines for JSONL files
                    try:
                        with open(filepath, 'r') as f:
                            line_count = sum(1 for _ in f)
                        available_files.append((filename, index, id_field, display_name, line_count))
                    except:
                        available_files.append((filename, index, id_field, display_name, "?"))
        
        if not available_files:
            self.console.print("[yellow]No data files available for ingestion[/yellow]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return
        
        # Display available files
        table = Table(title="Available Data Files")
        table.add_column("File", style="cyan")
        table.add_column("Records", style="white")
        table.add_column("Target Index", style="dim")
        
        for filename, index, id_field, display_name, count in available_files:
            table.add_row(filename, str(count), index)
        
        self.console.print(table)
        
        if Confirm.ask("\nProceed with ingestion of all available files?"):
            self.console.print("\n[blue]Starting ingestion process...[/blue]")
            self._perform_ingestion(available_files)
        
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _show_available_files(self):
        """Show available generated data files."""
        self.console.print("\n[blue]Scanning generated data files...[/blue]")
        
        import os
        data_dir = "generated_data"
        
        if not os.path.exists(data_dir):
            self.console.print("[red]No generated_data directory found[/red]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return
        
        table = Table(title="📊 Generated Data Files")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="white")
        table.add_column("Records", style="white") 
        table.add_column("Last Modified", style="dim")
        
        import datetime
        
        files = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.jsonl'):
                filepath = os.path.join(data_dir, filename)
                stat = os.stat(filepath)
                size = stat.st_size
                modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                
                # Count records
                record_count = "0"
                if size > 0:
                    try:
                        with open(filepath, 'r') as f:
                            record_count = str(sum(1 for _ in f))
                    except:
                        record_count = "?"
                
                # Format size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size//1024} KB"
                else:
                    size_str = f"{size//1024//1024} MB"
                
                files.append((filename, size_str, record_count, modified))
        
        files.sort()  # Sort alphabetically
        
        for filename, size_str, record_count, modified in files:
            table.add_row(filename, size_str, record_count, modified)
        
        if not files:
            table.add_row("No JSONL files found", "", "", "")
        
        self.console.print(table)
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _perform_ingestion(self, available_files):
        """Actually perform the ingestion of files to Elasticsearch."""
        try:
            import sys
            import os
            sys.path.append('scripts')
            from common_utils import create_elasticsearch_client, ingest_data_to_es
            from lib.index_manager import ensure_indices_exist
            
            # Create ES client
            es_client = create_elasticsearch_client()
            
            # Ensure all target indices exist
            target_indices = [index for _, index, _, _, _ in available_files]
            self.console.print(f"[blue]Ensuring indices exist: {', '.join(set(target_indices))}[/blue]")
            ensure_indices_exist(es_client, list(set(target_indices)))
            
            # Ingest each file with progress tracking
            successful_ingestions = []
            failed_ingestions = []
            
            for filename, index, id_field, display_name, count in available_files:
                filepath = os.path.join("generated_data", filename)
                
                self.console.print(f"\n[blue]Ingesting {display_name} ({count} records)...[/blue]")
                
                try:
                    # Use the existing ingestion function
                    ingest_data_to_es(
                        es_client=es_client,
                        filepath=filepath,
                        index_name=index,
                        id_field_in_doc=id_field
                    )
                    # The function doesn't return success/failure, so assume success if no exception
                    success = True
                    
                    if success:
                        successful_ingestions.append((display_name, count))
                        self.console.print(f"[green]✅ {display_name}: Successfully ingested {count} records[/green]")
                    else:
                        failed_ingestions.append((display_name, "Ingestion returned False"))
                        self.console.print(f"[red]❌ {display_name}: Ingestion failed[/red]")
                        
                except Exception as e:
                    failed_ingestions.append((display_name, str(e)))
                    self.console.print(f"[red]❌ {display_name}: Error - {e}[/red]")
            
            # Summary
            self.console.print("\n" + "="*50)
            self.console.print("[bold]Ingestion Summary[/bold]")
            
            if successful_ingestions:
                self.console.print("[green]✅ Successfully ingested:[/green]")
                for name, count in successful_ingestions:
                    self.console.print(f"  • {name}: {count} records")
            
            if failed_ingestions:
                self.console.print("[red]❌ Failed ingestions:[/red]")
                for name, error in failed_ingestions:
                    self.console.print(f"  • {name}: {error}")
            
            total_success = len(successful_ingestions)
            total_files = len(available_files)
            self.console.print(f"\n[bold]Result: {total_success}/{total_files} files successfully ingested[/bold]")
            
        except ImportError as e:
            self.console.print(f"[red]❌ Could not import required modules: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Ingestion failed: {e}[/red]")

    def show_index_status_only(self):
        """Show only the Elasticsearch index status (for --check-indices flag)."""
        try:
            # Try to connect to Elasticsearch
            from common_utils import create_elasticsearch_client
            from index_manager import IndexManager

            self.console.print("🔍 [blue]Connecting to Elasticsearch...[/blue]")
            es_client = create_elasticsearch_client()
            manager = IndexManager(es_client)

            # Test connection first
            connection_test = manager.test_connection()
            if not connection_test['success']:
                self.console.print(f"[red]❌ Connection test failed:[/red]")
                self.console.print(f"   Error Type: {connection_test.get('error_type', 'Unknown')}")
                self.console.print(f"   Error: {connection_test['error']}")
                return

            self.console.print(f"✅ [green]Connected to Elasticsearch {connection_test['version']}[/green]")

            # Get status of all indices
            statuses = manager.get_all_indices_status()

            # Create status table
            table = Table(title="📊 Index Status Summary")
            table.add_column("Index Name", style="cyan", width=25)
            table.add_column("Exists", style="white", width=8)
            table.add_column("Documents", style="white", width=10, justify="right")
            table.add_column("Size", style="white", width=10, justify="right")
            table.add_column("Errors", style="red", width=30)

            total_docs = 0
            total_size = 0
            indices_exist = 0

            for status in statuses:
                # Check for errors first
                if 'error' in status:
                    table.add_row(
                        status['index'],
                        "❌",
                        "-",
                        "-",
                        status['error'][:30] + "..." if len(status['error']) > 30 else status['error']
                    )
                    continue

                exists_str = "✓" if status['exists'] else "❌"
                error_str = ""

                if status['exists']:
                    indices_exist += 1
                    doc_count = status.get('doc_count', 0) or 0  # Ensure not None
                    total_docs += doc_count

                    # Format document count
                    doc_str = f"{doc_count:,}" if doc_count > 0 else "0"

                    # Format size (note: size may be None in serverless)
                    size_bytes = status.get('size')
                    if size_bytes is not None and size_bytes > 0:
                        total_size += size_bytes
                        if size_bytes >= 1024 * 1024:  # MB
                            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                        elif size_bytes >= 1024:  # KB
                            size_str = f"{size_bytes / 1024:.1f} KB"
                        else:
                            size_str = f"{size_bytes} B"
                    else:
                        size_str = "N/A"  # Not available in serverless

                    # Check for sub-errors (updated for serverless compatibility)
                    errors = []
                    for key in ['count_error', 'mapping_error']:
                        if key in status:
                            errors.append(status[key].split(':')[0])  # Just the error type
                    error_str = ", ".join(errors) if errors else ""
                else:
                    doc_str = "-"
                    size_str = "-"

                table.add_row(
                    status['index'],
                    exists_str,
                    doc_str,
                    size_str,
                    error_str
                )

            # Display the table
            self.console.print()
            self.console.print(table)

            # Summary statistics
            self.console.print()
            if indices_exist == len(statuses):
                self.console.print(f"[green]✓ All {indices_exist} indices are properly configured[/green]")
            elif indices_exist > 0:
                self.console.print(f"[yellow]⚠️  {indices_exist}/{len(statuses)} indices exist[/yellow]")
            else:
                self.console.print(f"[red]❌ No indices exist - run setup first[/red]")

            if total_docs > 0:
                if total_size > 0:
                    total_size_mb = total_size / (1024 * 1024)
                    self.console.print(f"[dim]Total: {total_docs:,} documents, {total_size_mb:.1f} MB[/dim]")
                else:
                    self.console.print(f"[dim]Total: {total_docs:,} documents (size not available in serverless)[/dim]")

            self.console.print()

        except ImportError as e:
            self.console.print(f"[red]❌ Import error: {e}[/red]")
            self.console.print("[yellow]Please ensure all dependencies are installed[/yellow]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to connect to Elasticsearch: {e}[/red]")
            self.console.print("[yellow]Please check your ES_ENDPOINT_URL and ES_API_KEY environment variables[/yellow]")

    def update_elasticsearch_timestamps(self, offset_hours=0):
        """Update timestamps in all Elasticsearch indices."""
        try:
            from common_utils import create_elasticsearch_client
            from timestamp_updater import TimestampUpdater

            self.console.print(f"\n🕐 [bold blue]Updating Elasticsearch Timestamps[/bold blue]")

            if offset_hours != 0:
                if offset_hours > 0:
                    self.console.print(f"[yellow]Offset: {offset_hours} hours in the future[/yellow]")
                else:
                    self.console.print(f"[yellow]Offset: {abs(offset_hours)} hours in the past[/yellow]")
            else:
                self.console.print("[yellow]Setting timestamps to current time[/yellow]")

            # Connect to Elasticsearch
            self.console.print("\n[yellow]Connecting to Elasticsearch...[/yellow]")
            es_client = create_elasticsearch_client()

            # Update all indices
            self.console.print("[yellow]Updating timestamps...[/yellow]\n")
            results = TimestampUpdater.update_all_indices(es_client, offset_hours)

            # Display results
            formatted_results = TimestampUpdater.format_results(results)
            self.console.print(formatted_results)

            # Show new timestamp
            target_time = TimestampUpdater.calculate_target_timestamp(offset_hours)
            self.console.print(f"\n[green]✓ Timestamps updated to: {target_time}[/green]")

        except ImportError as e:
            self.console.print(f"[red]❌ Import error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Error updating timestamps: {e}[/red]")

    def update_data_file_timestamps(self, offset_hours=0):
        """Update timestamps in data files."""
        try:
            from timestamp_updater import TimestampUpdater
            import os

            self.console.print(f"\n📁 [bold blue]Updating Data File Timestamps[/bold blue]")

            if offset_hours != 0:
                if offset_hours > 0:
                    self.console.print(f"[yellow]Offset: {offset_hours} hours in the future[/yellow]")
                else:
                    self.console.print(f"[yellow]Offset: {abs(offset_hours)} hours in the past[/yellow]")
            else:
                self.console.print("[yellow]Setting timestamps to current time[/yellow]")

            # Find all data files
            data_dir = "generated_data"
            if not os.path.exists(data_dir):
                self.console.print(f"[red]❌ Data directory '{data_dir}' not found[/red]")
                return

            data_files = [
                ('generated_accounts.jsonl', 'accounts'),
                ('generated_holdings.jsonl', 'holdings'),
                ('generated_asset_details.jsonl', 'asset_details'),
                ('generated_news.jsonl', 'news'),
                ('generated_reports.jsonl', 'reports'),
                ('generated_controlled_news.jsonl', 'news'),
                ('generated_controlled_reports.jsonl', 'reports')
            ]

            total_updated = 0
            self.console.print("\n[yellow]Updating files...[/yellow]")

            for filename, doc_type in data_files:
                filepath = os.path.join(data_dir, filename)
                if os.path.exists(filepath):
                    try:
                        count = TimestampUpdater.update_file_timestamps(
                            filepath,
                            doc_type=doc_type,
                            offset_hours=offset_hours
                        )
                        self.console.print(f"✓ {filename}: Updated {count} documents")
                        total_updated += count
                    except Exception as e:
                        self.console.print(f"❌ {filename}: Error - {e}")
                else:
                    self.console.print(f"[dim]⏭️  {filename}: File not found[/dim]")

            # Show summary
            target_time = TimestampUpdater.calculate_target_timestamp(offset_hours)
            self.console.print(f"\n[green]✓ Total: {total_updated} documents updated[/green]")
            self.console.print(f"[green]✓ Timestamps set to: {target_time}[/green]")

        except ImportError as e:
            self.console.print(f"[red]❌ Import error: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Error updating files: {e}[/red]")

    def show_index_management_menu(self):
        """Display Elasticsearch index management menu."""
        # Import here to avoid circular dependencies
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

        try:
            from lib.index_manager import IndexManager
            from scripts.common_utils import create_elasticsearch_client
        except ImportError as e:
            self.console.print(f"[red]Error: Required modules not available: {e}[/red]")
            self.console.input("\n[dim]Press Enter to continue...[/dim]")
            return

        while True:
            index_items = [
                ("1", "📋 Check Index Status", "View status of all indices"),
                ("2", "✨ Create Missing Indices", "Create indices that don't exist"),
                ("3", "♻️  Recreate All Indices", "Delete and recreate all indices"),
                ("4", "🗑️  Delete Index", "Delete a specific index"),
                ("5", "🔍 View Index Mapping", "Show mapping for an index"),
                ("6", "🔙 Back to Main Menu", "Return to main menu"),
            ]

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Choice", style="bold cyan", width=3)
            table.add_column("Action", style="bold white", width=25)
            table.add_column("Description", style="dim white")

            for choice, action, description in index_items:
                table.add_row(choice, action, description)

            panel = Panel(
                table,
                title="🗄️ Index Management",
                border_style="blue"
            )

            self.console.print(panel)

            choice = Prompt.ask(
                "\n[bold cyan]Choose an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "6"],
                default="6"
            )

            if choice == "6":
                break

            # Initialize ES client for operations
            try:
                self.console.print("[yellow]Connecting to Elasticsearch...[/yellow]")
                es_client = create_elasticsearch_client()
                manager = IndexManager(es_client)
            except Exception as e:
                self.console.print(f"[red]Failed to connect to Elasticsearch: {e}[/red]")
                self.console.input("\n[dim]Press Enter to continue...[/dim]")
                continue

            if choice == "1":
                self._show_index_status(manager)
            elif choice == "2":
                self._create_missing_indices(manager)
            elif choice == "3":
                self._recreate_all_indices(manager)
            elif choice == "4":
                self._delete_index(manager)
            elif choice == "5":
                self._view_index_mapping(manager)

    def _show_index_status(self, manager):
        """Show status of all indices."""
        statuses = manager.get_all_indices_status()

        table = Table(title="📊 Index Status")
        table.add_column("Index", style="cyan")
        table.add_column("Exists", style="white")
        table.add_column("Health", style="white")
        table.add_column("Documents", style="white")
        table.add_column("Size", style="white")

        for status in statuses:
            exists_str = "✓" if status['exists'] else "✗"
            health_color = {
                'green': 'green',
                'yellow': 'yellow',
                'red': 'red'
            }.get(status.get('health', ''), 'white')

            health_str = f"[{health_color}]{status.get('health', 'N/A')}[/{health_color}]" if status['exists'] else "N/A"
            doc_count = str(status.get('doc_count', 0)) if status['exists'] else "N/A"

            size = status.get('size', 0)
            if size and status['exists']:
                size_mb = size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB"
            else:
                size_str = "N/A"

            table.add_row(
                status['name'],
                exists_str,
                health_str,
                doc_count,
                size_str
            )

        self.console.print(table)
        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _create_missing_indices(self, manager):
        """Create indices that don't exist."""
        self.console.print("[yellow]Creating missing indices...[/yellow]")
        successful, failed = manager.ensure_indices_exist()

        if failed == 0:
            self.console.print(f"[green]✓ All indices created successfully ({successful} total)[/green]")
        else:
            self.console.print(f"[yellow]⚠️  Created {successful} indices, {failed} failed[/yellow]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _recreate_all_indices(self, manager):
        """Recreate all indices after confirmation."""
        if Confirm.ask("[red]⚠️  This will DELETE all data in existing indices. Continue?[/red]", default=False):
            self.console.print("[yellow]Recreating all indices...[/yellow]")
            successful, failed = manager.recreate_all_indices()

            if failed == 0:
                self.console.print(f"[green]✓ All indices recreated successfully ({successful} total)[/green]")
            else:
                self.console.print(f"[yellow]⚠️  Recreated {successful} indices, {failed} failed[/yellow]")
        else:
            self.console.print("[blue]Operation cancelled[/blue]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _delete_index(self, manager):
        """Delete a specific index."""
        index_name = Prompt.ask("Enter index name to delete")

        if Confirm.ask(f"[red]Delete index '{index_name}'? This cannot be undone.[/red]", default=False):
            if manager.delete_index(index_name):
                self.console.print(f"[green]✓ Index '{index_name}' deleted[/green]")
            else:
                self.console.print(f"[red]Failed to delete index '{index_name}'[/red]")
        else:
            self.console.print("[blue]Operation cancelled[/blue]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")

    def _view_index_mapping(self, manager):
        """View mapping for a specific index."""
        index_name = Prompt.ask("Enter index name")

        mapping = manager.get_index_mapping(index_name)
        if mapping:
            import json
            self.console.print(json.dumps(mapping, indent=2))
        else:
            self.console.print(f"[yellow]No mapping found for index '{index_name}'[/yellow]")

        self.console.input("\n[dim]Press Enter to continue...[/dim]")
