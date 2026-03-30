import { EmptyState } from './common';
import type { DailyAccountStatus, TimeStampEvent } from '../types/api';
import { buildDayTimelineModel } from '../utils/dayTimeline';

function getTimelineHint(status: DailyAccountStatus | undefined, hasOpenBlock: boolean, hasInvalidPoint: boolean): string | null {
  if (status === 'invalid' || hasInvalidPoint) return 'Ungültige Reihenfolge – bitte den markierten Bereich prüfen.';
  if (status === 'incomplete' || hasOpenBlock) return 'Offener Zeitblock – Gegenstempel fehlt.';
  return null;
}

export function DayTimeline({ events, status }: { events: TimeStampEvent[]; status?: DailyAccountStatus }) {
  const model = buildDayTimelineModel(events, status);

  if (!model.items.length) {
    return <EmptyState title="Kein Zeitverlauf verfügbar" description="Noch keine Zeitstempel für diesen Tag vorhanden." />;
  }

  const hint = getTimelineHint(status, model.hasOpenBlock, Boolean(model.firstInvalidItemId));

  return (
    <section className="day-timeline" aria-label="Zeitverlauf">
      <div className="day-timeline-flow" role="list" aria-label="Zeitereignisse in Reihenfolge">
        {model.items.map((item, index) => (
          <div key={item.id} className="day-timeline-node-wrap" role="listitem">
            <div
              className={`day-timeline-node ${item.type === 'clock_in' ? 'is-in' : 'is-out'} ${item.isInvalidFlow ? 'is-invalid' : ''}`.trim()}
              title={item.hasComment ? 'Kommentiert' : undefined}
            >
              <span className="day-timeline-type">{item.type === 'clock_in' ? 'Kommen' : 'Gehen'}</span>
              <strong className="time-value">{item.timeLabel}</strong>
              <div className="day-timeline-meta">
                {item.hasComment ? <span className="day-timeline-flag">Kommentiert</span> : null}
                {item.isCorrected ? <span className="day-timeline-flag">Korrigiert</span> : null}
                {item.isInvalidPoint ? <span className="day-timeline-flag danger">Ungültige Reihenfolge</span> : null}
              </div>
            </div>
            {index < model.items.length - 1 ? <span className={`day-timeline-connector ${item.isInvalidFlow ? 'is-invalid' : ''}`.trim()} aria-hidden /> : null}
          </div>
        ))}
      </div>

      {hint ? <p className={`meta ${status === 'invalid' ? 'inline-error' : ''}`}>{hint}</p> : null}

      {model.intervals.length ? (
        <div className="day-intervals">
          <strong>Arbeitsblöcke</strong>
          <ul>
            {model.intervals.map((interval) => (
              <li key={`${interval.startId}-${interval.endId ?? 'open'}`} className={interval.state === 'open' ? 'is-open' : ''}>
                {interval.state === 'complete' ? `${interval.startLabel} – ${interval.endLabel}` : `${interval.startLabel} – offen`}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
