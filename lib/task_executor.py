"""
Task Executor for Synthetic Financial Data Generator

Handles script execution with live progress tracking and status dashboard.
"""

import os
import sys
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.table import Table
from rich.text import Text
from rich.align import Align

class TaskExecutor:
    """Executes data generation tasks with live progress tracking."""
    
    def __init__(self, console: Console):
        self.console = console
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            expand=True
        )
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.stop_requested = False
        self.interactive_mode = True  # Default to interactive
        
        # Script mappings
        self.script_map = {
            'accounts': 'scripts/generate_holdings_accounts.py',
            'news': 'scripts/generate_reports_and_news_new.py', 
            'reports': 'scripts/generate_reports_and_news_new.py',
            'trigger_event': 'scripts/trigger_bad_news_event.py'
        }
    
    def execute_tasks(self, config: Dict[str, Any], interactive: bool = True):
        """Execute configured tasks with live dashboard."""
        self.stop_requested = False
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.interactive_mode = interactive
        
        # Plan tasks based on configuration
        tasks = self._plan_tasks(config)
        
        if not tasks:
            self.console.print("[yellow]No tasks to execute[/yellow]")
            return
        
        # Create layout for live dashboard
        layout = self._create_dashboard_layout()
        
        with Live(layout, refresh_per_second=2, console=self.console, screen=True) as live:
            # Submit all tasks
            futures = []
            for task in tasks:
                future = self.executor.submit(self._execute_single_task, task)
                futures.append((future, task))
                self.active_tasks[task['name']] = {
                    'task': task,
                    'status': 'queued',
                    'progress': 0,
                    'message': 'Waiting to start...',
                    'start_time': time.time(),
                    'task_id': None
                }
            
            # Monitor tasks
            try:
                self._monitor_tasks(futures, layout, live)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Stopping tasks...[/yellow]")
                self.stop_requested = True
                self.executor.shutdown(wait=True)
        
        # Show final summary
        self._show_final_summary()
    
    def stop_all_tasks(self):
        """Stop all running tasks."""
        self.stop_requested = True
        self.executor.shutdown(wait=False)
    
    def _plan_tasks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan tasks based on configuration."""
        tasks = []
        
        # Check if this is a data loading operation (no generation settings)
        is_loading_existing_data = not any([
            config.get('num_accounts'),
            config.get('num_news'), 
            config.get('num_reports'),
            config.get('trigger_event')
        ])
        
        if config.get('generate_accounts'):
            # Check if data files exist when loading existing data
            missing_files = []
            if is_loading_existing_data:
                missing_files = self._check_missing_data_files(['accounts', 'holdings', 'asset_details'])
                
            if missing_files:
                # Add a validation task that will explain the issue
                tasks.append({
                    'name': 'accounts',
                    'description': 'Check Accounts Data Files',
                    'script': None,  # Special marker for validation task
                    'estimated_duration': 1,
                    'config': config,
                    'missing_files': missing_files,
                    'task_type': 'validation'
                })
            else:
                tasks.append({
                    'name': 'accounts',
                    'description': 'Generate Accounts & Holdings',
                    'script': self.script_map['accounts'],
                    'estimated_duration': 120,  # seconds
                    'config': config
                })
        
        if config.get('generate_news'):
            missing_files = []
            if is_loading_existing_data:
                missing_files = self._check_missing_data_files(['news'])
                
            if missing_files:
                tasks.append({
                    'name': 'news',
                    'description': 'Check News Data Files',
                    'script': None,
                    'estimated_duration': 1,
                    'config': config,
                    'missing_files': missing_files,
                    'task_type': 'validation'
                })
            else:
                tasks.append({
                    'name': 'news', 
                    'description': 'Generate News Articles',
                    'script': self.script_map['news'],
                    'estimated_duration': 300,
                    'config': config
                })
        
        if config.get('generate_reports'):
            missing_files = []
            if is_loading_existing_data:
                missing_files = self._check_missing_data_files(['reports'])
                
            if missing_files:
                tasks.append({
                    'name': 'reports',
                    'description': 'Check Reports Data Files',
                    'script': None,
                    'estimated_duration': 1,
                    'config': config,
                    'missing_files': missing_files,
                    'task_type': 'validation'
                })
            else:
                tasks.append({
                    'name': 'reports',
                    'description': 'Generate Reports',
                    'script': self.script_map['reports'], 
                    'estimated_duration': 180,
                    'config': config
                })
        
        if config.get('trigger_event'):
            tasks.append({
                'name': 'trigger_event',
                'description': f'Trigger {config.get("event_type", "unknown")} Event',
                'script': self.script_map['trigger_event'],
                'estimated_duration': 60,
                'config': config
            })
        
        return tasks
    
    def _check_missing_data_files(self, data_types: List[str]) -> List[str]:
        """Check which data files are missing from generated_data directory."""
        missing_files = []
        
        # File mapping for each data type
        expected_files = {
            'accounts': 'generated_accounts.jsonl',
            'holdings': 'generated_holdings.jsonl', 
            'asset_details': 'generated_asset_details.jsonl',
            'news': 'generated_news.jsonl',
            'reports': 'generated_reports.jsonl'
        }
        
        generated_data_dir = os.path.join(os.getcwd(), 'generated_data')
        
        for data_type in data_types:
            if data_type in expected_files:
                file_path = os.path.join(generated_data_dir, expected_files[data_type])
                if not os.path.exists(file_path):
                    missing_files.append(expected_files[data_type])
        
        return missing_files
    
    def _handle_validation_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation tasks that report missing data files."""
        task_name = task['name']
        missing_files = task.get('missing_files', [])
        
        # Create helpful error message
        error_msg = f"❌ Missing data files for {task_name}:\n"
        error_msg += f"   Missing: {', '.join(missing_files)}\n\n"
        error_msg += "💡 Solutions:\n"
        error_msg += "   1. Generate missing data first:\n"
        
        if task_name == 'accounts':
            error_msg += "      python3 control.py --custom --accounts --num-accounts 1000\n"
        elif task_name == 'news':
            error_msg += "      python3 control.py --custom --news --num-news 100\n"
        elif task_name == 'reports':
            error_msg += "      python3 control.py --custom --reports --num-reports 50\n"
            
        error_msg += "   2. Or generate all data at once:\n"
        error_msg += "      python3 control.py --quick-start\n"
        error_msg += "   3. Only load data types that exist:\n"
        error_msg += "      python3 control.py --status  # Check what files exist"
        
        # Update task status
        self.active_tasks[task_name]['status'] = 'error'
        self.active_tasks[task_name]['message'] = f'Missing required data files'
        
        return {'success': False, 'error': error_msg}
    
    def _execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        task_name = task['name']
        
        if self.stop_requested:
            return {'success': False, 'error': 'Stopped by user'}
        
        # Update task status
        self.active_tasks[task_name]['status'] = 'running'
        self.active_tasks[task_name]['message'] = 'Starting...'
        
        # Handle validation tasks (missing data files)
        if task.get('task_type') == 'validation':
            return self._handle_validation_task(task)
        
        try:
            # Prepare script execution
            script_path = task['script']
            
            # Create command
            cmd = [sys.executable, script_path]
            
            # Add event-specific arguments for trigger events
            if task_name == 'trigger_event':
                event_type = task.get('config', {}).get('event_type', 'bad_news')
                cmd.extend(['--event-type', event_type])
            
            # Set environment variables if needed
            env = os.environ.copy()
            
            # Execute script
            self.active_tasks[task_name]['message'] = 'Running script...'
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # Monitor process with real-time output parsing
            stdout_lines = []
            stderr_lines = []
            
            # Read output line by line for real-time progress tracking
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    stdout_lines.append(line)
                    
                    # Parse progress from output
                    progress = self._parse_progress_from_output(line)
                    if progress is not None:
                        self.active_tasks[task_name]['progress'] = progress
                        self.active_tasks[task_name]['message'] = self._extract_message_from_output(line)
            
            # Get any remaining stderr
            stderr = process.stderr.read() if process.stderr else ''
            stdout = '\n'.join(stdout_lines)
            
            if process.returncode == 0:
                # Success
                self.active_tasks[task_name]['status'] = 'completed'
                self.active_tasks[task_name]['message'] = 'Completed successfully'
                self.active_tasks[task_name]['progress'] = 100
                
                # Move to completed tasks
                completed_task = self.active_tasks[task_name].copy()
                completed_task['stdout'] = stdout
                completed_task['end_time'] = time.time()
                self.completed_tasks.append(completed_task)
                
                return {'success': True, 'stdout': stdout}
            else:
                # Error - show full error message
                self.active_tasks[task_name]['status'] = 'error' 
                error_msg = stderr.strip() if stderr.strip() else "Process failed with no error details"
                self.active_tasks[task_name]['message'] = f'Error: {error_msg}'
                
                return {'success': False, 'error': stderr, 'stdout': stdout}
                
        except Exception as e:
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['message'] = f'Exception: {str(e)}'
            return {'success': False, 'error': str(e)}
    
    def _monitor_tasks(self, futures: List, layout: Layout, live: Live):
        """Monitor task execution and update dashboard."""
        completed_count = 0
        total_tasks = len(futures)
        
        # Add tasks to progress tracker
        for future, task in futures:
            task_name = task['name']
            task_id = self.progress.add_task(
                task['description'],
                total=100
            )
            self.active_tasks[task_name]['task_id'] = task_id
        
        while completed_count < total_tasks:
            if self.stop_requested:
                break
            
            # Update progress for each task
            for future, task in futures:
                task_name = task['name']
                task_info = self.active_tasks.get(task_name)
                
                if task_info and task_info['task_id'] is not None:
                    # Update progress based on status
                    if task_info['status'] == 'running':
                        # Use real-time progress from script output parsing
                        progress = task_info.get('progress', 0)
                        
                        self.progress.update(
                            task_info['task_id'],
                            completed=progress,
                            description=f"{task['description']} - {task_info['message']}"
                        )
                    
                    elif task_info['status'] == 'completed':
                        self.progress.update(
                            task_info['task_id'],
                            completed=100,
                            description=f"✓ {task['description']} - Completed"
                        )
                        if future.done():
                            completed_count += 1
                    
                    elif task_info['status'] == 'error':
                        self.progress.update(
                            task_info['task_id'],
                            completed=0,
                            description=f"❌ {task['description']} - Error"
                        )
                        if future.done():
                            completed_count += 1
            
            # Update dashboard layout
            self._update_dashboard(layout)
            
            time.sleep(0.5)
    
    def _create_dashboard_layout(self) -> Layout:
        """Create the live dashboard layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=10),
            Layout(name="status"),
        )
        
        layout["status"].split_row(
            Layout(name="active", ratio=2),
            Layout(name="system", ratio=1)
        )
        
        return layout
    
    def _update_dashboard(self, layout: Layout):
        """Update dashboard with current status."""
        # Header
        layout["header"].update(
            Panel(
                Align.center(
                    Text("🏦 Synthetic Data Generation Dashboard", style="bold blue")
                ),
                style="blue"
            )
        )
        
        # Progress
        layout["progress"].update(
            Panel(
                self.progress,
                title="📊 Task Progress",
                border_style="green"
            )
        )
        
        # Active Tasks Status
        active_table = Table(title="🔄 Active Tasks")
        active_table.add_column("Task", style="cyan")
        active_table.add_column("Status", style="white")
        active_table.add_column("Message", style="dim white")
        
        for task_name, task_info in self.active_tasks.items():
            status_color = {
                'queued': 'yellow',
                'running': 'blue', 
                'completed': 'green',
                'error': 'red'
            }.get(task_info['status'], 'white')
            
            active_table.add_row(
                task_name.title(),
                f"[{status_color}]{task_info['status'].title()}[/{status_color}]",
                task_info['message'][:50] + ('...' if len(task_info['message']) > 50 else '')
            )
        
        layout["active"].update(
            Panel(active_table, border_style="yellow")
        )
        
        # System Status
        system_table = Table(title="💻 System")
        system_table.add_column("Metric", style="cyan")
        system_table.add_column("Value", style="white")
        
        system_table.add_row("Active Tasks", str(len([t for t in self.active_tasks.values() if t['status'] == 'running'])))
        system_table.add_row("Completed", str(len(self.completed_tasks)))
        system_table.add_row("Total Tasks", str(len(self.active_tasks)))
        
        layout["system"].update(
            Panel(system_table, border_style="cyan")
        )
    
    def _parse_progress_from_output(self, line: str) -> Optional[int]:
        """Parse progress percentage from script output line."""
        import re
        
        # Look for tqdm progress patterns like "50%|████████████" or "Progress: 50%"
        tqdm_pattern = r'(\d+)%\|'
        progress_pattern = r'(\d+)%'
        
        # Check for tqdm format first
        match = re.search(tqdm_pattern, line)
        if match:
            return int(match.group(1))
        
        # Check for general progress format
        match = re.search(progress_pattern, line)
        if match:
            return int(match.group(1))
        
        # Look for completion indicators
        if 'completed successfully' in line.lower() or 'finished' in line.lower():
            return 100
        
        # Look for phase transitions to estimate progress
        phase_indicators = {
            'initializing': 5,
            'validating': 10,
            'generating accounts': 20,
            'generating holdings': 40,
            'generating news': 60,
            'generating reports': 80,
            'ingesting': 90,
            'completed': 100
        }
        
        line_lower = line.lower()
        for indicator, progress in phase_indicators.items():
            if indicator in line_lower:
                return progress
        
        return None
    
    def _extract_message_from_output(self, line: str) -> str:
        """Extract a concise message from script output line."""
        # Remove timestamp if present
        import re
        timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - '
        line = re.sub(timestamp_pattern, '', line)
        
        # Extract key information
        if 'generating' in line.lower():
            return line.strip()
        elif 'ingesting' in line.lower():
            return line.strip()
        elif 'completed' in line.lower():
            return "Completed successfully"
        elif 'error' in line.lower():
            return line.strip()
        else:
            # Return truncated line for other messages
            return line[:50] + "..." if len(line) > 50 else line
    
    def _show_final_summary(self):
        """Show final execution summary."""
        success_count = len([t for t in self.completed_tasks if t.get('task', {}).get('success', True)])
        total_count = len(self.completed_tasks) + len([t for t in self.active_tasks.values() if t['status'] == 'error'])
        
        if success_count == total_count and total_count > 0:
            status_color = "green"
            status_icon = "✅"
            status_text = "All tasks completed successfully"
        elif success_count > 0:
            status_color = "yellow" 
            status_icon = "⚠️"
            status_text = f"{success_count}/{total_count} tasks completed successfully"
        else:
            status_color = "red"
            status_icon = "❌"
            status_text = "No tasks completed successfully"
        
        summary_table = Table(title=f"{status_icon} Execution Summary")
        summary_table.add_column("Task", style="cyan")
        summary_table.add_column("Status", style="white")
        summary_table.add_column("Duration", style="dim white")
        
        for completed_task in self.completed_tasks:
            task_name = completed_task['task']['name']
            duration = completed_task.get('end_time', time.time()) - completed_task['start_time']
            
            summary_table.add_row(
                task_name.title(),
                f"[green]✓ Completed[/green]",
                f"{duration:.1f}s"
            )
        
        # Add error tasks
        for task_name, task_info in self.active_tasks.items():
            if task_info['status'] == 'error':
                duration = time.time() - task_info['start_time']
                summary_table.add_row(
                    task_name.title(),
                    f"[red]❌ Error[/red]",
                    f"{duration:.1f}s"
                )
        
        panel = Panel(
            summary_table,
            title="📋 Final Summary",
            border_style=status_color
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
        # Show detailed errors if any
        error_tasks = [t for t in self.active_tasks.values() if t['status'] == 'error']
        if error_tasks:
            self.console.print("\n[red]❌ Error Details:[/red]")
            for task_info in error_tasks:
                task_name = task_info['task']['name']
                error_msg = task_info['message']
                
                # Try to get the full error from the task result if available
                future_result = getattr(task_info, 'result', None)
                if future_result and hasattr(future_result, 'result'):
                    try:
                        result = future_result.result()
                        if not result.get('success') and result.get('error'):
                            full_error = result['error'].strip()
                            if full_error:
                                error_msg = f"Error: {full_error}"
                    except:
                        pass
                
                self.console.print(f"  • {task_name}: {error_msg}")
        
        self.console.print(f"\n[{status_color}]{status_text}[/{status_color}]")
        
        # Pause for user to see results (only in interactive mode)
        if not self.stop_requested and self.interactive_mode:
            self.console.input("\n[dim]Press Enter to continue...[/dim]")