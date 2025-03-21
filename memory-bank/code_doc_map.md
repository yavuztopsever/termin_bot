# Munich Termin Automator (MTA) - Code Documentation Map

## Status
- **Version**: 1.0.0
- **Status**: In Development
- **Last Updated**: Current
- **Next Review**: Daily

## 1. Core Components

### 1.1 Main Application
- **File**: `src/main.py`
- **Documentation**: `memory-bank/architecture.md#system-overview`
- **Status**: In Progress
- **Notes**: Main application entry point, service initialization

### 1.2 Bot Module
- **Directory**: `src/bot/`
- **Documentation**: `memory-bank/architecture.md#telegram-bot-layer`
- **Status**: In Progress
- **Notes**: Telegram bot implementation, command handlers

### 1.3 Database Module
- **Directory**: `src/data/database/`
- **Documentation**: `memory-bank/architecture.md#data-layer`
- **Status**: In Progress
- **Notes**: Database models, migrations, repositories

### 1.4 API Module
- **Directory**: `src/gateway/`
- **Documentation**: `memory-bank/architecture.md#api-gateway-layer`
- **Status**: In Progress
- **Notes**: API endpoints, middleware, routing

### 1.5 Services Module
- **Directory**: `src/control/services/`
- **Documentation**: `memory-bank/architecture.md#control-layer`
- **Status**: In Progress
- **Notes**: Business logic, service implementations

### 1.6 Utils Module
- **Directory**: `src/utils/`
- **Documentation**: `memory-bank/architecture.md#utility-layer`
- **Status**: In Progress
- **Notes**: Helper functions, common utilities

### 1.7 Manager Module
- **Directory**: `src/control/manager/`
- **Documentation**: `memory-bank/architecture.md#control-layer`
- **Status**: In Progress
- **Notes**: Task management, coordination

### 1.8 Analyzer Module
- **Directory**: `src/control/analyzer/`
- **Documentation**: `memory-bank/architecture.md#control-layer`
- **Status**: In Progress
- **Notes**: Pattern analysis, bot detection

## 2. Configuration Files

### 2.1 Environment Configuration
- **File**: `.env.example`
- **Documentation**: `memory-bank/tech_context.md#configuration`
- **Status**: Complete
- **Notes**: Environment variables template

### 2.2 Docker Configuration
- **File**: `Dockerfile`
- **Documentation**: `memory-bank/tech_context.md#deployment`
- **Status**: Complete
- **Notes**: Container build configuration

### 2.3 Docker Compose
- **File**: `docker-compose.yml`
- **Documentation**: `memory-bank/tech_context.md#deployment`
- **Status**: Complete
- **Notes**: Service orchestration

### 2.4 Requirements
- **File**: `requirements.txt`
- **Documentation**: `memory-bank/tech_context.md#dependencies`
- **Status**: Complete
- **Notes**: Python dependencies

## 3. Test Files

### 3.1 Unit Tests
- **Directory**: `tests/unit/`
- **Documentation**: `memory-bank/tech_context.md#testing`
- **Status**: Not Started
- **Notes**: Component-level tests

### 3.2 Integration Tests
- **Directory**: `tests/integration/`
- **Documentation**: `memory-bank/tech_context.md#testing`
- **Status**: Not Started
- **Notes**: Service integration tests

### 3.3 End-to-End Tests
- **Directory**: `tests/e2e/`
- **Documentation**: `memory-bank/tech_context.md#testing`
- **Status**: Not Started
- **Notes**: System-level tests

## 4. Documentation Files

### 4.1 Memory Bank
- **Directory**: `memory-bank/`
- **Documentation**: `memory-bank/index.md`
- **Status**: In Progress
- **Notes**: Project documentation

### 4.2 API Documentation
- **Directory**: `docs/api/`
- **Documentation**: `memory-bank/architecture.md#api-design`
- **Status**: Not Started
- **Notes**: API specifications

### 4.3 User Guide
- **Directory**: `docs/user/`
- **Documentation**: `memory-bank/product_context.md`
- **Status**: Not Started
- **Notes**: User documentation

## 5. Scripts

### 5.1 Development Scripts
- **Directory**: `scripts/dev/`
- **Documentation**: `memory-bank/tech_context.md#development-setup`
- **Status**: In Progress
- **Notes**: Development utilities

### 5.2 Deployment Scripts
- **Directory**: `scripts/deploy/`
- **Documentation**: `memory-bank/tech_context.md#deployment`
- **Status**: Not Started
- **Notes**: Deployment automation

### 5.3 Maintenance Scripts
- **Directory**: `scripts/maintain/`
- **Documentation**: `memory-bank/tech_context.md#maintenance`
- **Status**: Not Started
- **Notes**: System maintenance

## 6. Database Files

### 6.1 Migrations
- **Directory**: `src/data/database/migrations/`
- **Documentation**: `memory-bank/architecture.md#database-schema`
- **Status**: In Progress
- **Notes**: Database schema changes

### 6.2 Models
- **Directory**: `src/data/models/`
- **Documentation**: `memory-bank/architecture.md#database-schema`
- **Status**: In Progress
- **Notes**: Data models

### 6.3 Repositories
- **Directory**: `src/data/repositories/`
- **Documentation**: `memory-bank/architecture.md#data-layer`
- **Status**: In Progress
- **Notes**: Data access layer

## 7. Monitoring Files

### 7.1 Metrics
- **Directory**: `src/monitoring/metrics/`
- **Documentation**: `memory-bank/architecture.md#monitoring-architecture`
- **Status**: In Progress
- **Notes**: System metrics

### 7.2 Health Checks
- **Directory**: `src/monitoring/health/`
- **Documentation**: `memory-bank/architecture.md#monitoring-architecture`
- **Status**: In Progress
- **Notes**: Health monitoring

### 7.3 Logging
- **Directory**: `src/monitoring/logging/`
- **Documentation**: `memory-bank/architecture.md#logging-architecture`
- **Status**: In Progress
- **Notes**: Logging configuration

## 8. Security Files

### 8.1 Authentication
- **Directory**: `src/security/auth/`
- **Documentation**: `memory-bank/architecture.md#security-architecture`
- **Status**: In Progress
- **Notes**: Authentication logic

### 8.2 Authorization
- **Directory**: `src/security/authz/`
- **Documentation**: `memory-bank/architecture.md#security-architecture`
- **Status**: In Progress
- **Notes**: Authorization logic

### 8.3 Encryption
- **Directory**: `src/security/encryption/`
- **Documentation**: `memory-bank/architecture.md#security-architecture`
- **Status**: Not Started
- **Notes**: Data encryption

## 9. Integration Files

### 9.1 Telegram Integration
- **Directory**: `src/integration/telegram/`
- **Documentation**: `memory-bank/architecture.md#telegram-bot-layer`
- **Status**: In Progress
- **Notes**: Telegram API integration

### 9.2 Target Site Integration
- **Directory**: `src/integration/target/`
- **Documentation**: `memory-bank/architecture.md#external-integration`
- **Status**: In Progress
- **Notes**: Target site integration

### 9.3 Redis Integration
- **Directory**: `src/integration/redis/`
- **Documentation**: `memory-bank/architecture.md#external-integration`
- **Status**: In Progress
- **Notes**: Redis integration

## 10. Documentation Updates

### 10.1 Recent Updates
- **File**: `memory-bank/changelog.md`
- **Documentation**: `memory-bank/index.md`
- **Status**: Current
- **Notes**: Recent documentation changes

### 10.2 Upcoming Updates
- **File**: `memory-bank/timeline.md`
- **Documentation**: `memory-bank/index.md`
- **Status**: Current
- **Notes**: Planned documentation updates

### 10.3 Review Schedule
- **File**: `memory-bank/index.md`
- **Documentation**: `memory-bank/index.md`
- **Status**: Current
- **Notes**: Documentation review schedule 