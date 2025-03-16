import http from 'http';
import { logger } from './services/loggingService';

/**
 * Simple health check server for Docker
 */
export function startHealthCheckServer(port = 3000): void {
  const server = http.createServer((req, res) => {
    if (req.url === '/health') {
      // Return 200 OK for health checks
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
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
