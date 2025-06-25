#!/usr/bin/env python3
"""
GitLab Test Operations Implementation
Simple test runner for minimal FCM testing
"""

import os
import sys


class TestOperations:
    """Handle test operations from FCM definitions"""
    
    def __init__(self):
        self.message = os.environ.get('MESSAGE', 'Hello from GitLab test operations!')
        self.outputs = {}
    
    def run(self):
        """Execute the test operation"""
        try:
            print(f"Test message: {self.message}")
            
            # Set outputs
            self.outputs['result'] = 'success'
            
            self._write_outputs()
            print("✓ Test operation completed successfully")
            
        except Exception as e:
            print(f"ERROR: Test operation failed - {e}")
            sys.exit(1)
    
    def _write_outputs(self):
        """Write outputs to dotenv file for GitLab"""
        with open('operation_outputs.env', 'w') as f:
            for key, value in self.outputs.items():
                # GitLab dotenv format
                f.write(f'{key.upper()}="{value}"\n')


def main():
    """Main entry point"""
    print("GitLab Test Operations Runner")
    print(f"Model: {os.environ.get('FCM_MODEL', 'unknown')}")
    print(f"Version: {os.environ.get('FCM_VERSION', 'unknown')}")
    print()
    
    test_ops = TestOperations()
    test_ops.run()


if __name__ == "__main__":
    main()