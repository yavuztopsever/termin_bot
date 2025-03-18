declare module 'node-notifier' {
  interface NotificationOptions {
    title?: string;
    subtitle?: string;
    message?: string;
    sound?: boolean | string;
    icon?: string;
    contentImage?: string;
    open?: string;
    wait?: boolean;
    timeout?: number;
    closeLabel?: string;
    actions?: string[];
    dropdownLabel?: string;
    reply?: boolean;
    [key: string]: any;
  }

  interface NotificationCallback {
    (err: Error | null, response: any, metadata?: any): void;
  }

  interface Notifier {
    notify(options: NotificationOptions, callback?: NotificationCallback): Notifier;
    notify(options: NotificationOptions): Notifier;
  }

  const notifier: Notifier;
  export = notifier;
}
