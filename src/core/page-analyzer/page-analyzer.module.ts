import { Module } from '@nestjs/common';
import { CommonModule } from '../common/common.module';
import { BrowserModule } from '../browser/browser.module';
import { PageAnalyzerService } from './page-analyzer.service';

@Module({
  imports: [CommonModule, BrowserModule],
  providers: [PageAnalyzerService],
  exports: [PageAnalyzerService]
})
export class PageAnalyzerModule {} 