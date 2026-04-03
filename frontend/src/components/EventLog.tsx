import React from 'react';
import './EventLog.css';

interface Event {
  type: 'goal' | 'yellow_card' | 'red_card' | 'substitution' | string;
  team: string;
  player: string;
  minute: number;
  description: string;
  timestamp: Date;
}

interface EventLogProps {
  events: Event[];
  maxDisplayed?: number;
}

/**
 * Displays a log of match events (goals, cards, substitutions)
 */
const EventLog: React.FC<EventLogProps> = ({ events, maxDisplayed = 10 }) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'goal':
        return '⚽';
      case 'yellow_card':
        return '🟨';
      case 'red_card':
        return '🟥';
      case 'substitution':
        return '🔄';
      default:
        return '📝';
    }
  };

  const getEventClass = (type: string) => {
    return `event-${type.replace(/_/g, '-')}`;
  };

  const displayedEvents = events.slice(0, maxDisplayed).reverse();

  if (events.length === 0) {
    return (
      <div className="event-log empty">
        <p>No events yet</p>
      </div>
    );
  }

  return (
    <div className="event-log">
      <div className="events-list">
        {displayedEvents.map((event, index) => (
          <div key={index} className={`event ${getEventClass(event.type)}`}>
            <div className="event-icon">{getEventIcon(event.type)}</div>
            <div className="event-details">
              <div className="event-header">
                <span className="event-minute">{event.minute}'</span>
                <span className="event-type">{event.type}</span>
                <span className="event-team">{event.team}</span>
              </div>
              <div className="event-info">
                <span className="player">{event.player}</span>
                <span className="description">{event.description}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      {events.length > maxDisplayed && (
        <div className="events-overflow">
          +{events.length - maxDisplayed} more events
        </div>
      )}
    </div>
  );
};

export default EventLog;
