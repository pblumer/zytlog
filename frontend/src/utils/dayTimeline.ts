import type { DailyAccountStatus, TimeStampEvent } from '../types/api';

export type DayTimelineItem = {
  id: number;
  type: 'clock_in' | 'clock_out';
  timeLabel: string;
  hasComment: boolean;
  isCorrected: boolean;
  isInvalidPoint: boolean;
  isInvalidFlow: boolean;
};

export type DayTimelineInterval = {
  startId: number;
  startLabel: string;
  endId: number | null;
  endLabel: string | null;
  state: 'complete' | 'open';
};

export type DayTimelineModel = {
  items: DayTimelineItem[];
  intervals: DayTimelineInterval[];
  firstInvalidItemId: number | null;
  hasOpenBlock: boolean;
};

function formatEventTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

export function buildDayTimelineModel(events: TimeStampEvent[] | undefined, dayStatus: DailyAccountStatus | undefined): DayTimelineModel {
  const sortedEvents = [...(events ?? [])].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  let expectedType: 'clock_in' | 'clock_out' = 'clock_in';
  let openStartEvent: TimeStampEvent | null = null;
  let firstInvalidIndex: number | null = null;

  const intervals: DayTimelineInterval[] = [];

  for (let index = 0; index < sortedEvents.length; index += 1) {
    const event = sortedEvents[index];
    const isValidTransition = event.type === expectedType;

    if (!isValidTransition && firstInvalidIndex === null) {
      firstInvalidIndex = index;
    }

    if (!isValidTransition) {
      continue;
    }

    if (event.type === 'clock_in') {
      openStartEvent = event;
      expectedType = 'clock_out';
      continue;
    }

    if (openStartEvent) {
      intervals.push({
        startId: openStartEvent.id,
        startLabel: formatEventTime(openStartEvent.timestamp),
        endId: event.id,
        endLabel: formatEventTime(event.timestamp),
        state: 'complete',
      });
    }
    openStartEvent = null;
    expectedType = 'clock_in';
  }

  if (firstInvalidIndex === null && openStartEvent !== null) {
    intervals.push({
      startId: openStartEvent.id,
      startLabel: formatEventTime(openStartEvent.timestamp),
      endId: null,
      endLabel: null,
      state: 'open',
    });
  }

  if (dayStatus === 'invalid' && firstInvalidIndex === null && sortedEvents.length > 0) {
    firstInvalidIndex = sortedEvents.length - 1;
  }

  const firstInvalidItemId = firstInvalidIndex !== null ? sortedEvents[firstInvalidIndex]?.id ?? null : null;

  const items: DayTimelineItem[] = sortedEvents.map((event, index) => ({
    id: event.id,
    type: event.type,
    timeLabel: formatEventTime(event.timestamp),
    hasComment: Boolean(event.comment),
    isCorrected: new Date(event.updated_at).getTime() > new Date(event.created_at).getTime(),
    isInvalidPoint: firstInvalidIndex === index,
    isInvalidFlow: firstInvalidIndex !== null && index >= firstInvalidIndex,
  }));

  return {
    items,
    intervals,
    firstInvalidItemId,
    hasOpenBlock: intervals.some((interval) => interval.state === 'open'),
  };
}
