import { DomainEvent } from '../common/domain-event';
import { Appointment } from './appointment';

type AppointmentEventData = {
  appointmentId: string;
  type: string;
  time: Date;
  status: string;
  metadata: Record<string, unknown>;
};

export class AppointmentCreatedEvent extends DomainEvent<AppointmentEventData> {
  constructor(public readonly appointment: Appointment) {
    super('APPOINTMENT_CREATED', {
      appointmentId: appointment.id,
      type: appointment.type,
      time: appointment.time,
      status: appointment.status,
      metadata: appointment.metadata
    });
  }
}

export class AppointmentBookedEvent extends DomainEvent<AppointmentEventData> {
  constructor(public readonly appointment: Appointment) {
    super('APPOINTMENT_BOOKED', {
      appointmentId: appointment.id,
      type: appointment.type,
      time: appointment.time,
      status: appointment.status,
      metadata: appointment.metadata
    });
  }
}

export class AppointmentCancelledEvent extends DomainEvent<AppointmentEventData> {
  constructor(public readonly appointment: Appointment) {
    super('APPOINTMENT_CANCELLED', {
      appointmentId: appointment.id,
      type: appointment.type,
      time: appointment.time,
      status: appointment.status,
      metadata: appointment.metadata
    });
  }
} 