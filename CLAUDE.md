# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ERPLibre is a CRM/ERP platform based on Odoo Community Edition (OCE) with automated installation, maintenance, and development tools. It's a "soft-fork" that aims to contribute back upstream while providing production-ready modules supported by the Odoo Community Association (OCA).

## Common Development Commands

### Installation and Setup
```bash
# Fresh installation (30+ minutes)
make install_os
make install_odoo_16

# Development environment setup
./script/install/install_dev.sh
./script/install/install_locally_dev.sh

# Generate configuration
make config_install
```

### Running ERPLibre
```bash
# Standard run
make run
# or
./run.sh

# Run with test database
make run_test

# Run specific database
./run.sh --database [DATABASE_NAME]
```

### Development Tools
```bash
# Format code (parallel execution)
make format

# Format specific components
make format_code_generator
make format_erplibre_addons
make format_script

# Version management
make version

# Clean environment
make clean
```

### Testing
```bash
# Fast comprehensive test suite
make test_full_fast

# Full test with coverage
make test_full_fast_coverage

# Basic tests only
make test

# View test coverage
make open_test_coverage

# Test specific module
./run.sh -d [DATABASE] -i [module] --test-enable --no-http --stop-after-init --log-level=test
```

### Database Operations
```bash
# Restore database from image
./script/database/db_restore.py --database [DB_NAME]

# Create test database
make db_create_db_test

# Clone database
make db_clone_test_to_test2

# Clean PostgreSQL database manually
sudo -iu postgres
psql
DROP DATABASE database_name;
rm -r ~/.local/share/Odoo/filestore/database_name
```

### Git Repository Management
```bash
# Show status of all repositories
make repo_show_status

# Configure all repositories
make repo_configure_all

# Switch all repos to SSH
make repo_use_all_ssh

# Switch all repos to HTTPS
make repo_use_all_https

# Show differences from last version
make repo_diff_from_last_version
```

## Architecture

### Core Structure
- **Main Application**: Built on Odoo 16 (configurable for 12.0, 14.0)
- **Addons Management**: Multi-repository system managed via repo manifests
- **Code Generator**: Automated module creation and templating system
- **Configuration**: Environment-based configuration with `config.conf`

### Key Directories
- `addons/`: Contains all addon repositories (managed by repo tool)
- `script/`: Python scripts for automation, testing, and maintenance
- `conf/`: Makefile configurations for different operations
- `docker/`: Docker configurations for different Odoo versions
- `manifest/`: Repository manifest files for dependency management
- `doc/`: Comprehensive documentation

### Repository Management
ERPLibre uses Google's `repo` tool to manage multiple git repositories. The `default.xml` manifest defines all addon repositories and their versions. Key groups:
- `base`: Core ERPLibre functionality
- `addons`: Community addon repositories
- `code_generator`: Code generation tools

### Code Generator System
Three-tier architecture for automated code generation:
1. **Template** → **Code_Generator** → **Module**
2. Templates can generate other Templates or Code_Generators
3. Code_Generators produce functional Odoo modules
4. Templates can read existing Modules to generate Code_Generators

**Warning**: Never run code generation on production - it creates circular dependencies.

### Python Environment
- Uses Poetry for dependency management with in-project virtual environment
- Python version managed via `.python-version` file
- Virtual environment located in `./.venv/`

### Testing Strategy
- Parallel test execution via `./script/test/run_parallel_test.py`
- Coverage reporting with focus on `addons/TechnoLibre_odoo-code-generator/*`
- Database caching for faster test runs
- Format checking with Black and Prettier

### Configuration Files
- `config.conf`: Generated Odoo configuration
- `poetry.toml`: Poetry configuration for in-project venv
- `package.json`: Prettier and XML formatting tools
- `.flake8`: Python linting configuration

## Development Workflow

### Module Development
```bash
# Create new module scaffold
source ./.venv/bin/activate
python odoo/odoo-bin scaffold MODULE_NAME addons/REPO_NAME/

# Install module for testing
./run.sh -d [DATABASE] -i [MODULE_NAME]

# Update module
./run.sh -d [DATABASE] -u [MODULE_NAME]
```

### Code Generator Workflow
```bash
# Install code generator
make addons_install_code_generator_basic
make run_code_generator

# Access at http://localhost:8069 (admin/admin)
# Enable debug mode: http://localhost:8069/web?debug=
# Use Code Generator app to create modules
```

### Adding New Repositories
1. Add repository URL to `source_repo_addons.csv`
2. Fork repository: `./script/git/fork_project_ERPLibre.py`
3. Regenerate manifest: `./script/git/fork_project_ERPLibre.py --skip_fork`
4. Check auto_install flags: `./script/git/repo_remove_auto_install.py`

### Commit Standards
Follow this format:
```bash
git commit -am "[#ticket] subject: short sentence"
```

## IDE Configuration

### PyCharm Setup
```bash
make pycharm_open        # First open
make pycharm_configure   # Configure (close first)
make pycharm_open        # Reopen configured
```

## Linting and Formatting

### Python Code
```bash
# Black formatter (preferred)
./script/maintenance/black.sh ./addons/[ADDON_PATH]

# Alternative: autopep8
./script/maintenance/autopep8.sh ./addons/[ADDON_PATH]
```

### XML/HTML
```bash
./script/maintenance/prettier_xml.sh ./addons/[ADDON_PATH]
```

### JavaScript
```bash
./script/maintenance/prettier.sh --tab-width 4 ./addons/[ADDON_PATH]
```

## Important Notes

- Always commit changes before using code generator (sync mode can erase data)
- Database operations require PostgreSQL service: `sudo systemctl start postgresql.service`
- Log files stored in `./.venv/make_test.log`
- Use `make log_show_test` to view test logs
- Configuration supports proxy mode for deployment
- Multi-version support (Odoo 12.0, 14.0, 16.0) via Docker configurations