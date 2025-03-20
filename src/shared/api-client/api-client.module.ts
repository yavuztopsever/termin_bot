import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ApiClientService } from './api-client.service';

@Module({
  imports: [ConfigModule],
  providers: [ApiClientService],
  exports: [ApiClientService],
})
export class ApiClientModule {} 