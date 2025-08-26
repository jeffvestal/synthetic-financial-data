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

def _is_notebook_environment():
    """Detect if running in a notebook environment (Colab/Jupyter)."""
    try:
        # Check for Google Colab
        import google.colab
        return True
    except ImportError:
        pass
    
    try:
        # Check for Jupyter notebook/lab
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is not None and hasattr(ipython, 'kernel'):
            return True  # Jupyter notebook/lab
    except ImportError:
        pass
    
    return False


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
        
        # Check if we're in a notebook environment
        is_notebook = _is_notebook_environment()
        
        if is_notebook:
            # Simple progress for notebook environments
            self.console.print(f"[blue]🚀 Starting {len(tasks)} tasks...[/blue]")
            for task in tasks:
                self.console.print(f"  • {task['description']}")
            self.console.print(f"[dim]Progress will be shown with percentage bars and updates every few seconds[/dim]")
            self.console.print()
            
            # Submit all tasks
            futures = []
            for task in tasks:
                # Populate active_tasks BEFORE submitting to avoid race condition
                self.active_tasks[task['name']] = {
                    'task': task,
                    'status': 'queued',
                    'progress': 0,
                    'message': 'Waiting to start...',
                    'start_time': time.time(),
                    'task_id': None
                }
                future = self.executor.submit(self._execute_single_task_with_progress, task)
                futures.append((future, task))
            
            # Monitor tasks with simple progress
            try:
                self._monitor_tasks_simple_with_progress(futures)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Stopping tasks...[/yellow]")
                self.stop_requested = True
                self.executor.shutdown(wait=True)
        else:
            # Create layout for live dashboard (terminal only)
            layout = self._create_dashboard_layout()
            
            with Live(layout, refresh_per_second=2, console=self.console, screen=True) as live:
                # Submit all tasks
                futures = []
                for task in tasks:
                    # Populate active_tasks BEFORE submitting to avoid race condition
                    self.active_tasks[task['name']] = {
                        'task': task,
                        'status': 'queued',
                        'progress': 0,
                        'message': 'Waiting to start...',
                        'start_time': time.time(),
                        'task_id': None
                    }
                    future = self.executor.submit(self._execute_single_task, task)
                    futures.append((future, task))
                
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
        
        # Check if this is a data loading operation (loading existing data with possible timestamp updates)
        is_loading_existing_data = config.get('update_timestamps_on_load', False)
        
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
                # Choose description based on whether we're loading existing data or generating new data
                description = 'Load Accounts & Holdings Data' if is_loading_existing_data else 'Generate Accounts & Holdings'
                tasks.append({
                    'name': 'accounts',
                    'description': description,
                    'script': self.script_map['accounts'],
                    'estimated_duration': 120,  # seconds
                    'config': config
                })
        
        # Handle news and reports together since they use the same script
        if config.get('generate_news') or config.get('generate_reports'):
            missing_files = []
            data_types_to_check = []
            
            if config.get('generate_news'):
                data_types_to_check.append('news')
            if config.get('generate_reports'):  
                data_types_to_check.append('reports')
                
            if is_loading_existing_data:
                missing_files = self._check_missing_data_files(data_types_to_check)
                
            if missing_files:
                # Create a single validation task for both
                description = "Check News & Reports Data Files"
                if config.get('generate_news') and not config.get('generate_reports'):
                    description = "Check News Data Files"
                elif config.get('generate_reports') and not config.get('generate_news'):
                    description = "Check Reports Data Files"
                    
                tasks.append({
                    'name': 'news_and_reports',
                    'description': description,
                    'script': None,
                    'estimated_duration': 1,
                    'config': config,
                    'missing_files': missing_files,
                    'task_type': 'validation'
                })
            else:
                # Create a single execution task for both
                # Choose description based on whether we're loading existing data or generating new data
                if is_loading_existing_data:
                    description = "Load News & Reports Data"
                    if config.get('generate_news') and not config.get('generate_reports'):
                        description = "Load News Data"
                    elif config.get('generate_reports') and not config.get('generate_news'):
                        description = "Load Reports Data"
                else:
                    description = "Generate News & Reports"
                    if config.get('generate_news') and not config.get('generate_reports'):
                        description = "Generate News Articles"
                    elif config.get('generate_reports') and not config.get('generate_news'):
                        description = "Generate Reports"
                    
                tasks.append({
                    'name': 'news_and_reports',
                    'description': description,
                    'script': self.script_map['news'],  # Both use the same script
                    'estimated_duration': 300,
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
            
            # Use communicate() to properly capture both stdout and stderr
            try:
                # For real-time progress, we need to read line by line from stdout
                # But we also need to capture stderr properly
                import select
                
                while process.poll() is None:
                    # Check if there's data to read from stdout
                    if sys.platform != 'win32':
                        # Unix-like systems can use select
                        ready, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                        
                        if process.stdout in ready:
                            line = process.stdout.readline()
                            if line:
                                line = line.strip()
                                stdout_lines.append(line)
                                
                                # Parse progress from output
                                progress = self._parse_progress_from_output(line)
                                if progress is not None:
                                    self.active_tasks[task_name]['progress'] = progress
                                    self.active_tasks[task_name]['message'] = self._extract_message_from_output(line)
                        
                        if process.stderr in ready:
                            line = process.stderr.readline()
                            if line:
                                stderr_lines.append(line.strip())
                    else:
                        # Windows fallback - read stdout only for progress
                        line = process.stdout.readline()
                        if line:
                            line = line.strip()
                            stdout_lines.append(line)
                            
                            # Parse progress from output
                            progress = self._parse_progress_from_output(line)
                            if progress is not None:
                                self.active_tasks[task_name]['progress'] = progress
                                self.active_tasks[task_name]['message'] = self._extract_message_from_output(line)
                
                # Get any remaining output
                remaining_stdout, remaining_stderr = process.communicate()
                if remaining_stdout:
                    stdout_lines.extend(remaining_stdout.strip().split('\n') if remaining_stdout.strip() else [])
                if remaining_stderr:
                    stderr_lines.extend(remaining_stderr.strip().split('\n') if remaining_stderr.strip() else [])
                    
            except Exception as e:
                # Fallback to communicate() if select fails
                try:
                    remaining_stdout, remaining_stderr = process.communicate(timeout=30)
                    if remaining_stdout:
                        stdout_lines.extend(remaining_stdout.strip().split('\n') if remaining_stdout.strip() else [])
                    if remaining_stderr:
                        stderr_lines.extend(remaining_stderr.strip().split('\n') if remaining_stderr.strip() else [])
                except subprocess.TimeoutExpired:
                    process.kill()
                    stderr_lines.append("Process timed out and was killed")
            
            stdout = '\n'.join(stdout_lines)
            stderr = '\n'.join(stderr_lines)
            
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
                # Error - show meaningful error message
                self.active_tasks[task_name]['status'] = 'error'
                
                # Try to extract meaningful error information
                error_msg = ""
                if stderr.strip():
                    # Use stderr if available
                    error_msg = stderr.strip()
                elif stdout.strip():
                    # If no stderr, look at the last few lines of stdout
                    stdout_lines_list = [line for line in stdout.split('\n') if line.strip()]
                    if stdout_lines_list:
                        # Show last 3 lines of stdout for context
                        error_msg = '\n'.join(stdout_lines_list[-3:])
                else:
                    # Last resort - show process info
                    error_msg = f"Process exited with code {process.returncode}"
                
                # Truncate very long error messages for the live display
                display_msg = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                self.active_tasks[task_name]['message'] = f'Error: {display_msg}'
                
                # Store the full error for final summary
                self.active_tasks[task_name]['full_error'] = error_msg
                self.active_tasks[task_name]['return_code'] = process.returncode
                
                return {'success': False, 'error': error_msg, 'stdout': stdout, 'stderr': stderr}
                
        except Exception as e:
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['message'] = f'Exception: {str(e)}'
            self.active_tasks[task_name]['full_error'] = str(e)
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
    
    def _execute_single_task_with_progress(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with real-time progress updates for notebooks."""
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
            
            # Execute script with real-time output capture
            self.active_tasks[task_name]['message'] = 'Running script...'
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # Monitor process with real-time output parsing for progress
            stdout_lines = []
            stderr_lines = []
            
            # Read output line by line to parse progress
            try:
                while process.poll() is None and not self.stop_requested:
                    if process.stdout.readable():
                        line = process.stdout.readline()
                        if line:
                            stdout_lines.append(line.strip())
                            # Parse progress from the line
                            progress = self._parse_progress_from_output(line)
                            if progress is not None:
                                self.active_tasks[task_name]['progress'] = progress
                                self.active_tasks[task_name]['message'] = self._extract_message_from_output(line)
                
                # Get any remaining output
                remaining_stdout, remaining_stderr = process.communicate()
                if remaining_stdout:
                    stdout_lines.extend(remaining_stdout.strip().split('\n') if remaining_stdout.strip() else [])
                if remaining_stderr:
                    stderr_lines.extend(remaining_stderr.strip().split('\n') if remaining_stderr.strip() else [])
                    
            except Exception as e:
                # Fallback to communicate() if line-by-line reading fails
                try:
                    remaining_stdout, remaining_stderr = process.communicate(timeout=30)
                    if remaining_stdout:
                        stdout_lines.extend(remaining_stdout.strip().split('\n') if remaining_stdout.strip() else [])
                    if remaining_stderr:
                        stderr_lines.extend(remaining_stderr.strip().split('\n') if remaining_stderr.strip() else [])
                except subprocess.TimeoutExpired:
                    process.kill()
                    stderr_lines.append("Process timed out and was killed")
            
            stdout = '\n'.join(stdout_lines)
            stderr = '\n'.join(stderr_lines)
            
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
                # Error - show meaningful error message
                self.active_tasks[task_name]['status'] = 'error'
                
                # Try to extract meaningful error information
                error_msg = ""
                if stderr.strip():
                    # Use stderr if available
                    error_msg = stderr.strip()
                elif stdout.strip():
                    # Use last few lines of stdout if stderr is empty
                    stdout_lines = stdout.strip().split('\n')
                    error_msg = '\n'.join(stdout_lines[-3:])  # Last 3 lines
                else:
                    error_msg = f"Process exited with code {process.returncode}"
                
                # Store error details
                display_msg = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                self.active_tasks[task_name]['message'] = f'Error: {display_msg}'
                
                # Store the full error for final summary
                self.active_tasks[task_name]['full_error'] = error_msg
                self.active_tasks[task_name]['return_code'] = process.returncode
                
                return {'success': False, 'error': error_msg, 'stdout': stdout, 'stderr': stderr}
                
        except Exception as e:
            self.active_tasks[task_name]['status'] = 'error'
            self.active_tasks[task_name]['message'] = f'Exception: {str(e)}'
            self.active_tasks[task_name]['full_error'] = str(e)
            return {'success': False, 'error': str(e)}
    
    def _monitor_tasks_simple_with_progress(self, futures: List):
        """Simple task monitoring for notebook environments with percentage progress."""
        completed_count = 0
        total_tasks = len(futures)
        progress_counter = 0
        last_progress_update = {}  # Track when we last showed progress for each task
        
        while completed_count < total_tasks:
            if self.stop_requested:
                break
            
            progress_counter += 1
            
            # Check task completion and report status changes
            for future, task in futures:
                task_name = task['name']
                task_info = self.active_tasks.get(task_name)
                
                if task_info and future.done():
                    if task_info['status'] not in ['completed', 'error']:
                        # Task just finished, get result
                        try:
                            result = future.result()
                            if isinstance(result, dict) and result.get('success'):
                                task_info['status'] = 'completed'
                                final_progress = task_info.get('progress', 100)
                                progress_bar = "█" * 20  # Full bar
                                self.console.print(f"[green]✓ {task['description']} [{progress_bar}] {final_progress}% - Completed![/green]")
                            else:
                                task_info['status'] = 'error'
                                self.console.print(f"[red]❌ {task['description']} failed[/red]")
                                if isinstance(result, dict) and result.get('error'):
                                    self.console.print(f"   Error: {result['error'][:100]}...")
                                else:
                                    self.console.print(f"   Unexpected result: {result}")
                        except Exception as e:
                            task_info['status'] = 'error'
                            import traceback
                            error_details = f"{type(e).__name__}: {e}"
                            self.console.print(f"[red]❌ {task['description']} failed with exception: {error_details}[/red]")
                        
                        completed_count += 1
                        
                elif task_info and task_info['status'] == 'queued':
                    # Check if task started running
                    task_info['status'] = 'running' 
                    task_info['start_progress_time'] = progress_counter
                    self.console.print(f"[blue]🔄 {task['description']} started[/blue]")
                    last_progress_update[task_name] = progress_counter
                    
                elif task_info and task_info['status'] == 'running':
                    # Show progress updates every 3 seconds or when progress changes significantly
                    current_progress = task_info.get('progress', 0)
                    last_shown_progress = last_progress_update.get(f"{task_name}_progress", 0)
                    
                    should_update = (
                        progress_counter % 3 == 0 and (
                            task_name not in last_progress_update or 
                            progress_counter - last_progress_update[task_name] >= 3
                        )
                    ) or (current_progress - last_shown_progress >= 5)  # Update if progress jumped 5%+
                    
                    if should_update and current_progress > 0:
                        # Show percentage progress bar
                        progress_bar = "█" * (current_progress // 5) + "░" * (20 - (current_progress // 5))
                        self.console.print(f"[dim]   ⏳ {task['description']} [{progress_bar}] {current_progress}%[/dim]")
                        last_progress_update[task_name] = progress_counter  
                        last_progress_update[f"{task_name}_progress"] = current_progress
            
            time.sleep(1.0)  # Check every second
        
        # Show completion summary for notebook environments
        completed_tasks = [task for task in self.active_tasks.values() if task['status'] == 'completed']
        failed_tasks = [task for task in self.active_tasks.values() if task['status'] == 'error']
        
        self.console.print(f"\n[bold]📊 Task Summary:[/bold]")
        self.console.print(f"[green]✓ Completed: {len(completed_tasks)}[/green]")
        if failed_tasks:
            self.console.print(f"[red]❌ Failed: {len(failed_tasks)}[/red]")
        else:
            self.console.print("[dim]❌ Failed: 0[/dim]")
            
        if len(completed_tasks) == total_tasks:
            self.console.print(f"[green]🎉 All tasks completed successfully![/green]")

    def _monitor_tasks_simple(self, futures: List):
        """Simple task monitoring for notebook environments with progress indicators."""
        completed_count = 0
        total_tasks = len(futures)
        progress_counter = 0
        last_progress_update = {}  # Track when we last showed progress for each task
        
        while completed_count < total_tasks:
            if self.stop_requested:
                break
            
            progress_counter += 1
            
            # Check task completion and report status changes
            for future, task in futures:
                task_name = task['name']
                task_info = self.active_tasks.get(task_name)
                
                if task_info and future.done():
                    if task_info['status'] not in ['completed', 'error']:
                        # Task just finished, get result
                        try:
                            result = future.result()
                            if isinstance(result, dict) and result.get('success'):
                                task_info['status'] = 'completed'
                                self.console.print(f"[green]✓ {task['description']} completed successfully[/green]")
                            else:
                                task_info['status'] = 'error'
                                self.console.print(f"[red]❌ {task['description']} failed[/red]")
                                if isinstance(result, dict) and result.get('error'):
                                    self.console.print(f"   Error: {result['error'][:100]}...")
                                else:
                                    self.console.print(f"   Unexpected result: {result}")
                        except Exception as e:
                            task_info['status'] = 'error'
                            import traceback
                            error_details = f"{type(e).__name__}: {e}"
                            self.console.print(f"[red]❌ {task['description']} failed with exception: {error_details}[/red]")
                            # Print a few lines of traceback for debugging
                            tb_lines = traceback.format_exc().split('\n')[-6:-1]  # Last 5 lines
                            for line in tb_lines:
                                if line.strip():
                                    self.console.print(f"   {line.strip()}")
                        
                        completed_count += 1
                        
                elif task_info and task_info['status'] == 'queued':
                    # Check if task started running
                    task_info['status'] = 'running' 
                    task_info['start_progress_time'] = progress_counter
                    self.console.print(f"[blue]🔄 {task['description']} started[/blue]")
                    last_progress_update[task_name] = progress_counter
                    
                elif task_info and task_info['status'] == 'running':
                    # Show progress updates every 5 seconds (5 iterations) or when progress changes
                    current_progress = task_info.get('progress', 0)
                    should_update = (
                        progress_counter % 5 == 0 and (
                            task_name not in last_progress_update or 
                            progress_counter - last_progress_update[task_name] >= 5
                        )
                    )
                    
                    if should_update:
                        elapsed_time = progress_counter - task_info.get('start_progress_time', 0)
                        
                        if current_progress > 0:
                            # Show percentage if available
                            progress_bar = "█" * (current_progress // 5) + "░" * (20 - (current_progress // 5))
                            self.console.print(f"[dim]   ⏳ {task['description']} [{progress_bar}] {current_progress}%[/dim]")
                        else:
                            # Fallback to dots animation if no progress data
                            dots = "." * ((elapsed_time // 5) % 4)  # Animated dots
                            self.console.print(f"[dim]   ⏳ {task['description']} in progress{dots} ({elapsed_time}s)[/dim]")
                        
                        last_progress_update[task_name] = progress_counter
            
            time.sleep(1.0)  # Check every second
        
        # Show completion summary for notebook environments
        completed_tasks = [task for task in self.active_tasks.values() if task['status'] == 'completed']
        failed_tasks = [task for task in self.active_tasks.values() if task['status'] == 'error']
        
        self.console.print(f"\n[bold]📊 Task Summary:[/bold]")
        self.console.print(f"[green]✓ Completed: {len(completed_tasks)}[/green]")
        if failed_tasks:
            self.console.print(f"[red]❌ Failed: {len(failed_tasks)}[/red]")
        else:
            self.console.print("[dim]❌ Failed: 0[/dim]")
            
        if len(completed_tasks) == total_tasks:
            self.console.print(f"[green]🎉 All tasks completed successfully![/green]")
    
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
        
        # Look for various progress patterns
        patterns = [
            r'(\d+)%\|',  # tqdm format: "50%|████████████"
            r'Progress:.*?(\d+)%',  # "Progress: 1234/5000 documents (25%)"
            r'\((\d+)%\)',  # "(25%)"
            r'(\d+)%'  # General "50%"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return int(match.group(1))
        
        # Look for completion indicators
        if 'completed successfully' in line.lower() or 'finished' in line.lower():
            return 100
        
        # Look for phase transitions to estimate progress - updated for actual script output patterns
        phase_indicators = {
            'initializing': 5,
            'validating': 10,
            'starting ingestion': 15,
            'starting': 10,
            '--- ingesting accounts ---': 25,
            '--- ingesting holdings ---': 50, 
            '--- ingesting asset details ---': 60,
            '--- ingesting news ---': 75,
            '--- ingesting reports ---': 90,
            'finished ingestion': 95,
            'successfully ingested': 100,
            'ingesting': 20,  # General fallback
            'finished': 95,
            'completed': 100,
            'all.*completed': 100
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
                
                # Use full error if available, otherwise fall back to message
                if 'full_error' in task_info and task_info['full_error']:
                    error_msg = task_info['full_error']
                    # Add return code for additional context
                    if 'return_code' in task_info:
                        error_msg = f"{error_msg} (exit code: {task_info['return_code']})"
                else:
                    error_msg = task_info['message']
                
                # For very long errors, show first few lines
                if len(error_msg) > 300:
                    lines = error_msg.split('\n')
                    if len(lines) > 5:
                        error_msg = '\n'.join(lines[:5]) + f"\n... ({len(lines)-5} more lines)"
                
                self.console.print(f"  • {task_name}: {error_msg}")
        
        self.console.print(f"\n[{status_color}]{status_text}[/{status_color}]")
        
        # Pause for user to see results (only in interactive mode)
        if not self.stop_requested and self.interactive_mode:
            self.console.input("\n[dim]Press Enter to continue...[/dim]")