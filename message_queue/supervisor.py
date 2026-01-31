"""
Process Supervisor for Event Consumers

Monitors consumer processes and restarts them on failure.
"""

import time
import logging
import threading
from multiprocessing import Process
from typing import List, Callable

logger = logging.getLogger(__name__)


class ProcessSupervisor:
    """
    Supervisor for monitoring and restarting consumer processes.
    
    Runs in a background thread and monitors consumer process health.
    Automatically restarts processes that terminate unexpectedly.
    """
    
    def __init__(
        self,
        process_factory: Callable[[], Process],
        max_retries: int = 3,
        retry_delay: int = 5,
        check_interval: int = 5
    ):
        """
        Initialize process supervisor.
        
        Args:
            process_factory: Function that returns a new Process instance
            max_retries: Maximum restart attempts before giving up
            retry_delay: Seconds to wait between restart attempts
            check_interval: Seconds between health checks
        """
        self.process_factory = process_factory
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.check_interval = check_interval
        
        self.process = None
        self.retry_count = 0
        self.is_running = False
        self.monitor_thread = None
        
    def start(self):
        """
        Start the consumer process and monitoring thread.
        """
        if self.is_running:
            logger.warning("Supervisor already running")
            return
        
        logger.info("Starting process supervisor")
        self.is_running = True
        
        # Start initial process
        self._start_process()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="supervisor_monitor"
        )
        self.monitor_thread.start()
        
        logger.info("Process supervisor started successfully")
    
    def stop(self):
        """
        Stop the supervisor and terminate consumer process.
        """
        logger.info("Stopping process supervisor")
        self.is_running = False
        
        if self.process and self.process.is_alive():
            logger.info("Terminating consumer process")
            self.process.terminate()
            self.process.join(timeout=10)
            
            if self.process.is_alive():
                logger.warning("Process did not terminate gracefully, killing")
                self.process.kill()
                self.process.join()
        
        logger.info("Process supervisor stopped")
    
    def _start_process(self):
        """
        Create and start a new consumer process.
        """
        try:
            self.process = self.process_factory()
            self.process.start()
            logger.info(f"Started consumer process (PID: {self.process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start consumer process: {e}")
            raise
    
    def _monitor_loop(self):
        """
        Main monitoring loop that checks process health.
        """
        logger.info("Supervisor monitoring loop started")
        
        while self.is_running:
            try:
                time.sleep(self.check_interval)
                
                if not self.process or not self.process.is_alive():
                    logger.warning("Consumer process is not alive")
                    self._handle_process_failure()
                else:
                    # Process is healthy, reset retry count
                    if self.retry_count > 0:
                        logger.info("Consumer process recovered, resetting retry count")
                        self.retry_count = 0
                        
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
        
        logger.info("Supervisor monitoring loop stopped")
    
    def _handle_process_failure(self):
        """
        Handle consumer process failure and attempt restart.
        """
        if self.retry_count >= self.max_retries:
            logger.error(
                f"Consumer process failed {self.retry_count} times. "
                f"Max retries ({self.max_retries}) reached. Giving up."
            )
            self.is_running = False
            return
        
        self.retry_count += 1
        
        # Calculate exponential backoff
        delay = self.retry_delay * (2 ** (self.retry_count - 1))
        
        logger.warning(
            f"Attempting to restart consumer process "
            f"(attempt {self.retry_count}/{self.max_retries}) "
            f"in {delay} seconds..."
        )
        
        time.sleep(delay)
        
        try:
            # Clean up old process
            if self.process:
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(timeout=5)
                self.process.close()
            
            # Start new process
            self._start_process()
            logger.info(f"Consumer process restarted successfully")
            
        except Exception as e:
            logger.error(f"Failed to restart consumer process: {e}")
    
    def get_status(self) -> dict:
        """
        Get current supervisor status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "process_alive": self.process.is_alive() if self.process else False,
            "process_pid": self.process.pid if self.process and self.process.is_alive() else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class MultiProcessSupervisor:
    """
    Supervisor for managing multiple consumer processes.
    """
    
    def __init__(self):
        self.supervisors: List[ProcessSupervisor] = []
    
    def add_process(
        self,
        process_factory: Callable[[], Process],
        max_retries: int = 3,
        retry_delay: int = 5,
        check_interval: int = 5
    ):
        """
        Add a consumer process to be supervised.
        
        Args:
            process_factory: Function that returns a new Process instance
            max_retries: Maximum restart attempts
            retry_delay: Seconds to wait between restarts
            check_interval: Seconds between health checks
        """
        supervisor = ProcessSupervisor(
            process_factory,
            max_retries,
            retry_delay,
            check_interval
        )
        self.supervisors.append(supervisor)
    
    def start_all(self):
        """
        Start all supervised processes.
        """
        logger.info(f"Starting {len(self.supervisors)} supervised processes")
        
        for supervisor in self.supervisors:
            supervisor.start()
        
        logger.info("All supervised processes started")
    
    def stop_all(self):
        """
        Stop all supervised processes.
        """
        logger.info(f"Stopping {len(self.supervisors)} supervised processes")
        
        for supervisor in self.supervisors:
            supervisor.stop()
        
        logger.info("All supervised processes stopped")
    
    def get_status_all(self) -> List[dict]:
        """
        Get status of all supervised processes.
        
        Returns:
            List of status dictionaries
        """
        return [s.get_status() for s in self.supervisors]
