import http from 'http';
import { logger } from './services/loggingService';

// Health check state
let healthStatus = {
  status: 'starting', // 'starting', 'ok', 'degraded', 'failing'
  startTime: new Date().toISOString(),
  lastChecked: new Date().toISOString(),
  failureCount: 0,
  maxFailures: 3, // Number of failures before reporting unhealthy
  checks: {
    browserInitialized: false,
    apiConnected: false
  }
};

/**
 * Update the health status of a specific component
 * @param component The component to update
 * @param isHealthy Whether the component is healthy
 */
export function updateHealthStatus(component: keyof typeof healthStatus.checks, isHealthy: boolean): void {
  healthStatus.checks[component] = isHealthy;
  healthStatus.lastChecked = new Date().toISOString();
  
  // Determine overall health status
  const allChecks = Object.values(healthStatus.checks);
  
  if (allChecks.every(check => check)) {
    healthStatus.status = 'ok';
    healthStatus.failureCount = 0;
  } else if (allChecks.some(check => check)) {
    healthStatus.status = 'degraded';
  } else {
    healthStatus.status = 'failing';
    healthStatus.failureCount++;
  }
  
  logger.debug(`Health status updated: ${component} = ${isHealthy}, overall = ${healthStatus.status}`);
}

/**
 * Enhanced health check server for Docker
 */
export function startHealthCheckServer(port = 3000): void {
  const server = http.createServer((req, res) => {
    if (req.url === '/health') {
      // Determine HTTP status code based on health status
      let statusCode = 200;
      
      // If we're failing for too long, report as unhealthy
      if (healthStatus.status === 'failing' && healthStatus.failureCount >= healthStatus.maxFailures) {
        statusCode = 503; // Service Unavailable
      } else if (healthStatus.status === 'degraded') {
        statusCode = 200; // Still OK for Docker health checks
      }
      
      // Return health check response
      res.writeHead(statusCode, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: healthStatus.status,
        startTime: healthStatus.startTime,
        lastChecked: healthStatus.lastChecked,
        uptime: Math.floor((new Date().getTime() - new Date(healthStatus.startTime).getTime()) / 1000),
        checks: healthStatus.checks
      }));
    } else {
      // Return 404 for other requests
      res.writeHead(404);
      res.end();
    }
  });

  server.listen(port, () => {
    logger.info(`Health check server running on port ${port}`);
  });

  server.on('error', (error) => {
    logger.error(`Health check server error: ${error instanceof Error ? error.message : String(error)}`);
  });
}
