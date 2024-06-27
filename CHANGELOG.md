# Change Log

All notable changes to this project will be documented in this file.

## [v0.3.1] 2024-06-27

- Removal: removed the legend

## [v0.3.0] 2024-06-26

- Enhancement: Added USER and COMMAND fields to the process listing output for more detailed information.
- Enhancement: Introduced the --all flag to prompt for sudo elevation and run lsof with sudo, allowing listing and killing of all processes.
- Enhancement: Improved help dialogues for better clarity and usability.
- Enhancement: Updated command output to display ANY when no process name or port is specified.
- Enhancement: Adjusted the kill command to use sudo for elevated permissions when necessary.
- Enhancement: color coding (root, current user, other)
- Enhancement: sorted output
- Removal: Removed error printing for cleaner output.

## [v0.2.0] 2024-06-26

- Enhancement: Added support to list processes without specifying a process name (list command).
- Enhancement: Updated process listing to enclose ports in square brackets for clearer output format.
- Bug Fix: Fixed issue with subprocess error handling in process management operations.
