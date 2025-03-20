import { Module } from '@nestjs/common';
import { StateService } from './state.service';
import { ConfigModule } from '../../config/config.module';
import { MonitoringModule } from '../monitoring/monitoring.module';

@Module({
  imports: [
    ConfigModule,
    MonitoringModule
  ],
  providers: [StateService],
  exports: [StateService]
})
export class StateModule {} 