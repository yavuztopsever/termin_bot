import { Injectable } from '@nestjs/common';
import { Subject } from 'rxjs';

export interface DomainEvent {
  type: string;
  data: any;
  timestamp: Date;
}

@Injectable()
export class EventBus {
  private readonly events = new Subject<DomainEvent>();

  publish(event: DomainEvent): void {
    this.events.next(event);
  }

  subscribe(callback: (event: DomainEvent) => void): void {
    this.events.subscribe(callback);
  }

  unsubscribe(): void {
    this.events.complete();
  }
} 