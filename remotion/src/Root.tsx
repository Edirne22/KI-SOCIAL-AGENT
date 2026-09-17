import React from 'react';
import { Composition } from 'remotion';
import { RaceCalendar, RaceCalendarProps } from './RaceCalendar';

export const Root: React.FC = () => {
  const defaultProps: RaceCalendarProps = {
    series: 'MotoGP World Championship',
    track: 'Red Bull Ring',
    dateRange: '18.–20. September 2026',
  };

  return (
    <>
      <Composition
        id="RaceCalendar"
        component={RaceCalendar}
        durationInFrames={210}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
    </>
  );
};
