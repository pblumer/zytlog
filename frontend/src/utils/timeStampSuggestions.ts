import type { TimeStampEvent, TimeStampEventType } from '../types/api';

export function getSuggestedNextStampType(events: TimeStampEvent[] | undefined): TimeStampEventType {
  if (!events?.length) return 'clock_in';

  const sortedEvents = [...events].sort((a, b) => {
    const diff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
    if (diff !== 0) return diff;
    return a.id - b.id;
  });

  const lastEvent = sortedEvents[sortedEvents.length - 1];
  return lastEvent.type === 'clock_in' ? 'clock_out' : 'clock_in';
}
